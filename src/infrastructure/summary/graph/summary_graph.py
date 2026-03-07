from typing import Any, Dict, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.application.ports.message_filter_port import MessageFilterPort
from src.application.ports.message_repository_port import MessageRepositoryPort
from src.domain.entities.analysis import (
    ActivityStatistics,
    ConversationAnalysisResult,
    ConversationStatistics,
    TokenUsage,
)
from src.domain.services.llm_service import LLMModelFactoryInterface
from src.domain.services.summary_format_service import SummaryFormatService
from src.infrastructure.llm.factory_impl import LLMProviderFactoryAdapter
from src.infrastructure.message_processing.extractors.meta_extractor import compute_message_meta
from src.infrastructure.message_processing.filters.message_filter_adapter import MessageFilterImpl
from src.infrastructure.persistence.adapters.mysql_message_repository import (
    MySQLMessageRepository,
)
from src.infrastructure.summary.chains.summary_chain import SummaryChain
from src.infrastructure.summary.graph.state import SummaryState


class SummaryGraph:
    """摘要生成工作流"""

    def __init__(
        self,
        model_factory: LLMModelFactoryInterface | None = None,
        message_repository: MessageRepositoryPort | None = None,
        filter_service: MessageFilterPort | None = None,
    ) -> None:
        self.model_factory = model_factory or LLMProviderFactoryAdapter()
        self.message_repo = message_repository or MySQLMessageRepository()
        self.filter_service = filter_service or MessageFilterImpl()
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """构建工作流"""
        workflow = StateGraph(cast(Any, SummaryState))

        workflow.add_node("load_messages", cast(Any, self.load_messages))
        workflow.add_node("filter_messages", cast(Any, self.filter_messages))
        workflow.add_node("count_tokens", cast(Any, self.count_tokens))
        workflow.add_node("select_model", cast(Any, self.select_model))
        workflow.add_node("generate_summary", cast(Any, self.generate_summary))

        workflow.set_entry_point("load_messages")
        workflow.add_edge("load_messages", "filter_messages")
        workflow.add_edge("filter_messages", "count_tokens")
        workflow.add_edge("count_tokens", "select_model")
        workflow.add_edge("select_model", "generate_summary")
        workflow.add_edge("generate_summary", END)

        return workflow.compile()

    def load_messages(self, state: SummaryState) -> SummaryState:
        """加载消息"""
        state["raw_messages"] = self.message_repo.get_group_messages(
            state["group_id"],
            state["hours"],
        )
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
        state["token_count"] = self.model_factory.token_counter.count_messages_tokens(
            state["filtered_messages"]
        )
        return state

    def select_model(self, state: SummaryState) -> SummaryState:
        """选择模型"""
        state["selected_model"] = self.model_factory.select_model(state["token_count"])
        return state

    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """生成LLM结构化摘要"""
        llm = self.model_factory.create_model(model_name=state["selected_model"])

        chain = SummaryChain(llm, max_topics=5)
        result = await chain.invoke(state["filtered_messages"])

        state["topics"] = [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in result.topics
        ]
        state["summary"] = SummaryFormatService.format(result)
        state["analysis"] = self._build_analysis(state)
        state["metadata"] = self._build_technical_metadata(state)

        return state

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
            estimated_cost = self.model_factory.estimate_cost(
                state["selected_model"],
                state["token_count"],
            )
        except Exception as _:
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
            "analysis": ConversationAnalysisResult(group_id=group_id),
            "metadata": {},
        }

        result = await self.graph.ainvoke(cast(Any, initial_state))
        return result
