from typing import cast, Any, Dict

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.infrastructure.summary.chains.summary_chain import SummaryChain
from src.config import plugin_config as config
from src.domain.entities.analysis import (
    ActivityStatistics,
    ConversationAnalysisResult,
    ConversationStatistics,
    TokenUsage,
)
from src.application.ports.message_repository_port import MessageRepositoryPort
from src.domain.services.cache_service import LLMCacheInterface
from src.domain.services.llm_service import LLMModelFactoryInterface
from src.domain.services.memory_service import MemoryManagerInterface
from src.domain.services.msg_filter_service import MessageFilter
from src.domain.services.summary_format_service import SummaryFormatService
from src.infrastructure.llm.factory_impl import LLMProviderFactoryAdapter
from src.infrastructure.message_processing.extractors.meta_extractor import compute_message_meta
from src.infrastructure.persistence.adapters.mysql_message_repository import (
    MySQLMessageRepository,
)
from src.infrastructure.retrieval.detail.rag_retriever import RAGRetriever
from src.infrastructure.retrieval.hybrid_retrieval_impl import HybridRetriever
from src.infrastructure.summary.graph.state import SummaryState


class SummaryGraph:
    """摘要生成工作流"""

    def __init__(
        self,
        model_factory: LLMModelFactoryInterface | None = None,
        memory_manager: MemoryManagerInterface | None = None,
        use_hybrid_search: bool = None,
        message_repository: MessageRepositoryPort | None = None,
        llm_cache: LLMCacheInterface | None = None,
        filter_service: MessageFilter | None = None,
    ):
        self.model_factory = model_factory or LLMProviderFactoryAdapter()
        self.message_repo = message_repository or MySQLMessageRepository()
        self.filter_service = filter_service or MessageFilter()

        # self.llm_cache = llm_cache
        # self.memory_manager = memory_manager

        # if use_hybrid_search is None:
        #     use_hybrid_search = config.retrieval_use_hybrid_search
        #
        # if self.memory_manager:
        #     rag_retriever = RAGRetriever(
        #         self.memory_manager.vector_store_instance,
        #         getattr(self.model_factory, "provider", None),
        #         use_compression=config.retrieval_use_compression,
        #     )
        #     self.retriever = HybridRetriever(
        #         rag_retriever=rag_retriever,
        #         use_hybrid=use_hybrid_search,
        #     )
        # else:
        #     self.retriever = None

        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """构建工作流"""
        workflow = StateGraph(cast(Any, SummaryState))

        workflow.add_node("load_messages", cast(Any, self.load_messages))
        workflow.add_node("filter_messages", cast(Any, self.filter_messages))
        workflow.add_node("check_cache", cast(Any, self.check_cache))
        workflow.add_node("count_tokens", cast(Any, self.count_tokens))
        workflow.add_node("select_model", cast(Any, self.select_model))
        workflow.add_node("retrieve_memory", cast(Any, self.retrieve_memory))
        workflow.add_node("generate_summary", cast(Any, self.generate_summary))
        workflow.add_node("save_cache", cast(Any, self.save_cache))
        workflow.add_node("save_memory", cast(Any, self.save_memory))

        workflow.set_entry_point("load_messages")
        workflow.add_edge("load_messages", "filter_messages")
        workflow.add_edge("filter_messages", "check_cache")

        workflow.add_conditional_edges(
            "check_cache",
            self.route_cache,
            {"hit": END, "miss": "count_tokens"},
        )

        workflow.add_edge("count_tokens", "select_model")
        workflow.add_edge("select_model", "retrieve_memory")
        workflow.add_edge("retrieve_memory", "generate_summary")
        workflow.add_edge("generate_summary", "save_cache")
        workflow.add_edge("save_cache", "save_memory")
        workflow.add_edge("save_memory", END)

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
        raw_msgs = state["raw_messages"]
        state["filtered_messages"] = self.filter_service.get_cleaned_messages(raw_msgs)

        id2name = {}
        for msg in raw_msgs:
            uid = str(msg.get("user_id", ""))
            if uid:
                id2name[uid] = str(msg.get("sender_nickname") or uid)
        state["nickname_map"] = id2name

        return state

    # def check_cache(self, state: SummaryState) -> SummaryState:
    #     """检查Redis缓存"""
    #     if not self.llm_cache:
    #         state["cache_hit"] = False
    #         return state
    #
    #     cached = self.llm_cache.get(
    #         group_id=state["group_id"],
    #         messages=state["filtered_messages"],
    #     )
    #
    #     if cached:
    #         state["summary"] = cached["summary"]
    #         state["cache_hit"] = True
    #         state["cache_similarity"] = cached.get("similarity_score", 1.0)
    #         state["metadata"] = cached.get("metadata", {})
    #         state["analysis"] = state.get("analysis") or ConversationAnalysisResult(
    #             group_id=state["group_id"]
    #         )
    #     else:
    #         state["cache_hit"] = False
    #
    #     return state

    # @staticmethod
    # def route_cache(state: SummaryState) -> str:
    #     """缓存路由"""
    #     return "hit" if state.get("cache_hit") else "miss"

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

    # async def retrieve_memory(self, state: SummaryState) -> SummaryState:
    #     """检索RAG记忆"""
    #     if not self.memory_manager or not self.retriever:
    #         state["memory_context"] = ""
    #         return state
    #
    #     query = f"群组 {state['group_id']} 历史讨论重点"
    #
    #     result = await self.retriever.retrieve(
    #         query=query,
    #         group_id=state["group_id"],
    #         top_k=5,
    #     )
    #
    #     state["memory_context"] = (
    #         "\n\n".join([doc.page_content for doc in result]) if result else ""
    #     )
    #     return state

    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """生成LLM结构化摘要"""
        llm = self.model_factory.create_model(model_name=state["selected_model"])

        chain = SummaryChain(llm, max_topics=5)
        result = await chain.invoke(state["filtered_messages"], state["memory_context"])

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
            "cache_hit": state.get("cache_hit", False),
            "cache_similarity": state.get("cache_similarity", 0.0),
        }

    # def save_cache(self, state: SummaryState) -> SummaryState:
    #     """保存缓存：静默跳过"""
    #     if self.llm_cache and not state.get("cache_hit"):
    #         self.llm_cache.put(
    #             group_id=state["group_id"],
    #             hours=state["hours"],
    #             messages=state["filtered_messages"],
    #             summary=state["summary"],
    #             metadata=state.get("metadata", {}),
    #         )
    #     return state

    # def save_memory(self, state: SummaryState) -> SummaryState:
    #     """保存记忆：静默跳过"""
    #     if self.memory_manager:
    #         meta = state.get("metadata", {})
    #         self.memory_manager.add_memory(
    #             group_id=state["group_id"],
    #             messages=state["filtered_messages"],
    #             summary=state["summary"],
    #             concepts=[],
    #             events=[],
    #             metadata={"hours": state["hours"], **meta},
    #         )
    #     return state

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
            "memory_context": "",
            "summary": "",
            "topics": [],
            "analysis": ConversationAnalysisResult(group_id=group_id),
            "metadata": {},
            "refresh_mode": "high",
            "cache_hit": False,
            "cache_similarity": 0.0,
        }

        result = await self.graph.ainvoke(cast(Any, initial_state))
        return result
