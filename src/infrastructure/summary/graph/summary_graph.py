import asyncio
import hashlib
import time
from typing import Any, Dict, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ....application.ports.llm_gateway_port import LLMGatewayPort
from ....application.ports.message_filter_port import MessageFilterPort
from ....application.ports.message_repository_port import MessageRepositoryPort
from ....domain.entities.analysis import (
    ActivityStatistics,
    ConversationAnalysisResult,
    ConversationStatistics,
    TokenUsage,
)
from ....domain.services.summary_format_service import SummaryFormatService
from ...cache import AnchorStore, TTLCache
from ...llm.adapters.llm_gateway_adapter import LLMGatewayAdapter
from ...message_processing.extractors.meta_extractor import compute_message_meta
from ...message_processing.filters.message_filter_adapter import MessageFilterImpl
from ...message_processing.formatters.format_messages import format_messages
from ...persistence.adapters.mysql_message_repository import (
    MySQLMessageRepository,
)
from ..chains.compression_chain import CompressionChain
from ..chains.extraction_chain import ExtractionChain
from ..chains.summary_chain import SummaryChain
from .state import SummaryState


CHUNK_TOKEN_THRESHOLD = 5000
CHUNK_TOKEN_BUDGET = 3000


class SummaryGraph:
    """摘要生成工作流"""

    def __init__(
        self,
        llm_gateway: LLMGatewayPort | None = None,
        message_repository: MessageRepositoryPort | None = None,
        filter_service: MessageFilterPort | None = None,
        anchor_store: AnchorStore | None = None,
        chunk_cache: TTLCache | None = None,
    ) -> None:
        self.llm_gateway = llm_gateway or LLMGatewayAdapter()
        self.message_repo = message_repository or MySQLMessageRepository()
        self.filter_service = filter_service or MessageFilterImpl()
        self._anchor_store = anchor_store or AnchorStore()
        self._chunk_cache = chunk_cache or TTLCache(default_ttl=86400.0)
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """构建工作流"""
        workflow = StateGraph(cast(Any, SummaryState))

        workflow.add_node("load_messages", cast(Any, self.load_messages))
        workflow.add_node("filter_messages", cast(Any, self.filter_messages))
        workflow.add_node("count_tokens", cast(Any, self.count_tokens))
        workflow.add_node("select_model", cast(Any, self.select_model))
        workflow.add_node("split_chunks", cast(Any, self.split_chunks))
        workflow.add_node("extract_chunks", cast(Any, self.extract_chunks))
        workflow.add_node("merge_and_summarize", cast(Any, self.merge_and_summarize))
        workflow.add_node("generate_summary", cast(Any, self.generate_summary))
        workflow.add_node("update_anchor", cast(Any, self.update_anchor))

        workflow.set_entry_point("load_messages")
        workflow.add_edge("load_messages", "filter_messages")
        workflow.add_edge("filter_messages", "count_tokens")
        workflow.add_edge("count_tokens", "select_model")

        workflow.add_conditional_edges(
            "select_model",
            cast(Any, self._route_by_size),
            {
                "single": "generate_summary",
                "chunked": "split_chunks",
            },
        )

        workflow.add_edge("split_chunks", "extract_chunks")
        workflow.add_edge("extract_chunks", "merge_and_summarize")
        workflow.add_edge("merge_and_summarize", "update_anchor")
        workflow.add_edge("generate_summary", "update_anchor")
        workflow.add_edge("update_anchor", END)

        return workflow.compile()

    @staticmethod
    def _route_by_size(state: SummaryState) -> str:
        if state.get("token_count", 0) > CHUNK_TOKEN_THRESHOLD:
            return "chunked"
        return "single"

    async def load_messages(self, state: SummaryState) -> SummaryState:
        """加载消息：有窗口内锚点则取增量并带历史上下文，否则全量"""
        anchor = self._anchor_store.get(state["group_id"])
        now = int(time.time())
        window_start = now - state["hours"] * 3600

        if anchor and anchor.get("anchor_time", 0) >= window_start:
            state["raw_messages"] = await self.message_repo.get_group_messages_after(
                state["group_id"], anchor["anchor_time"]
            )
            state["memory_context"] = anchor.get("compressed_summary", "")
            state["is_incremental"] = True
        else:
            state["raw_messages"] = await self.message_repo.get_group_messages(
                state["group_id"],
                state["hours"],
            )
            state["memory_context"] = ""
            state["is_incremental"] = False
        return state

    def filter_messages(self, state: SummaryState) -> SummaryState:
        """过滤消息"""
        raw_messages = state["raw_messages"]
        state["filtered_messages"] = self.filter_service.filter_and_clean(raw_messages)

        id2name: Dict[str, str] = {}
        for msg in raw_messages:
            uid = str(msg.get("user_id", ""))
            if uid:
                id2name[uid] = str(msg.get("sender_nickname") or uid)
        state["nickname_map"] = id2name

        return state

    def count_tokens(self, state: SummaryState) -> SummaryState:
        """计算 token"""
        state["token_count"] = self.llm_gateway.token_counter.count_messages_tokens(
            state["filtered_messages"]
        )
        return state

    def select_model(self, state: SummaryState) -> SummaryState:
        """选择模型"""
        state["selected_model"] = self.llm_gateway.select_model(state["token_count"])
        return state

    def split_chunks(self, state: SummaryState) -> SummaryState:
        """按 token 预算把消息分块，每块格式化为文本"""
        messages = state["filtered_messages"]
        token_counter = self.llm_gateway.token_counter
        chunks: list[str] = []
        current: list[dict] = []
        current_tokens = 0

        for msg in messages:
            preview = f"[{msg.get('time', '')}] [{msg.get('user_id', '')}]: {msg.get('raw_message', '')}"
            msg_tokens = token_counter.count_tokens(preview)
            if current and current_tokens + msg_tokens > CHUNK_TOKEN_BUDGET:
                chunks.append(format_messages(current))
                current = [msg]
                current_tokens = msg_tokens
            else:
                current.append(msg)
                current_tokens += msg_tokens

        if current:
            chunks.append(format_messages(current))

        state["chunks"] = chunks
        return state

    async def extract_chunks(self, state: SummaryState) -> SummaryState:
        """并发对每块做信息提取，按块内容 hash 命中 L2 缓存"""
        llm = self.llm_gateway.create_model(model_name=state["selected_model"])
        chain = ExtractionChain(llm)
        chunks = state.get("chunks", []) or []
        if not chunks:
            state["extracted"] = []
            return state

        async def _extract_one(chunk_text: str) -> str:
            key = "chunk:" + hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
            cached = self._chunk_cache.get(key)
            if cached is not None:
                return cached
            extracted = await chain.invoke(chunk_text)
            self._chunk_cache.set(key, extracted)
            return extracted

        extracted = await asyncio.gather(*[_extract_one(c) for c in chunks])
        state["extracted"] = list(extracted)
        return state

    async def merge_and_summarize(self, state: SummaryState) -> SummaryState:
        """合并各块提取结果，生成结构化摘要"""
        llm = self.llm_gateway.create_model(model_name=state["selected_model"])
        chain = SummaryChain(llm, max_topics=5)
        merged_text = "\n\n---\n\n".join(state.get("extracted", []) or [])
        result = await chain.invoke(
            merged_text, memory_context=state.get("memory_context", "")
        )
        self._fill_summary_state(state, result)
        return state

    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """单次全量生成结构化摘要（短消息路径）"""
        llm = self.llm_gateway.create_model(model_name=state["selected_model"])
        chain = SummaryChain(llm, max_topics=5)
        messages_text = format_messages(state["filtered_messages"])
        result = await chain.invoke(
            messages_text, memory_context=state.get("memory_context", "")
        )
        self._fill_summary_state(state, result)
        return state

    async def update_anchor(self, state: SummaryState) -> SummaryState:
        """压缩当前摘要为历史上下文，更新群锚点；无新消息时保留旧锚点"""
        summary = state.get("summary", "")
        if not summary:
            return state
        llm = self.llm_gateway.create_model(model_name=state["selected_model"])
        chain = CompressionChain(llm)
        compressed = await chain.invoke(summary)

        times = [m.get("time", 0) for m in state["filtered_messages"]]
        anchor_time = max(times) if times else int(time.time())
        self._anchor_store.save(state["group_id"], anchor_time, compressed)

        state["compressed_summary"] = compressed
        return state

    def _fill_summary_state(self, state: SummaryState, result: Any) -> None:
        state["topics"] = [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in result.topics
        ]
        state["summary"] = SummaryFormatService.format(result)
        state["analysis"] = self._build_analysis(state)
        state["metadata"] = self._build_technical_metadata(state)

    def _build_analysis(self, state: SummaryState) -> ConversationAnalysisResult:
        """构建结构化分析结果"""
        msg_meta = compute_message_meta(state["filtered_messages"])

        stats = ConversationStatistics(
            message_count=msg_meta["msg_count"],
            participant_count=msg_meta["user_count"],
            total_characters=msg_meta["total_characters"],
            time_span=msg_meta["time_span"],
            duration=msg_meta["duration"],
            activity=ActivityStatistics(hourly_distribution=msg_meta["hourly_distribution"]),
        )

        try:
            estimated_cost = self.llm_gateway.estimate_cost(
                state["selected_model"],
                state["token_count"],
            )
        except Exception:
            estimated_cost = 0.0

        token_usage = TokenUsage(
            prompt_tokens=state["token_count"],
            total_tokens=state["token_count"],
            estimated_cost=estimated_cost,
        )

        return ConversationAnalysisResult(
            group_id=state["group_id"],
            statistics=stats,
            token_usage=token_usage,
        )

    @staticmethod
    def _build_technical_metadata(state: SummaryState) -> Dict[str, Any]:
        """构建技术侧元数据"""
        return {
            "model": state["selected_model"],
            "token_count": state["token_count"],
        }

    async def invoke(self, group_id: int, hours: int) -> Dict[str, Any]:
        """执行工作流"""
        initial_state: SummaryState = {
            "group_id": group_id,
            "hours": hours,
            "raw_messages": [],
            "filtered_messages": [],
            "nickname_map": {},
            "token_count": 0,
            "selected_model": "",
            "summary": "",
            "topics": [],
            "chunks": [],
            "extracted": [],
            "memory_context": "",
            "is_incremental": False,
            "compressed_summary": "",
            "analysis": ConversationAnalysisResult(group_id=group_id),
            "metadata": {},
        }

        result = await self.graph.ainvoke(cast(Any, initial_state))
        return result
