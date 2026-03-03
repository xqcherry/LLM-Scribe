import time
from typing import cast, Any, List, Dict

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.application.chains.summary_chain import SummaryChain
from src.application.graph.state import SummaryState
from src.config import plugin_config as config
from src.domain.repositories.message_repository import MessageRepositoryInterface
from src.domain.services.cache_service import LLMCacheInterface
from src.domain.services.summary_format_service import SummaryFormatService
from src.domain.services.message_filter_service import MessageFilterService
from src.domain.services.memory_service import MemoryManagerInterface
from src.domain.services.retrieval_service import RetrievalInterface
from src.domain.services.llm_service import LLMModelFactoryInterface
from src.infrastructure.persistence.message_repository_impl import (
    MySQLMessageRepository,
)
from src.infrastructure.cache.llm_cache_impl import RedisLLMCache
from src.infrastructure.memory.memory_manager_impl import DefaultMemoryManager
from src.infrastructure.retrieval.hybrid_retrieval_impl import HybridRetriever
from src.infrastructure.llm.moonshot_factory_impl import MoonshotFactoryAdapter
from src.infrastructure.retrieval.rag_retriever import RAGRetriever


class SummaryGraph:
    """摘要生成工作流"""

    def __init__(
        self,
        model_factory: LLMModelFactoryInterface | None = None,
        memory_manager: MemoryManagerInterface | None = None,
        use_hybrid_search: bool = None,
        message_repository: MessageRepositoryInterface | None = None,
        llm_cache: LLMCacheInterface | None = None,
    ):
        # 核心模型工厂
        self.model_factory: LLMModelFactoryInterface = (
            model_factory or MoonshotFactoryAdapter()
        )
        # 语义缓存（默认使用 Redis 实现）
        self.llm_cache: LLMCacheInterface = llm_cache or RedisLLMCache()
        # 记忆管理器
        self.memory_manager: MemoryManagerInterface = (
            memory_manager or DefaultMemoryManager()
        )

        # 检索配置
        if use_hybrid_search is None:
            use_hybrid_search = config.retrieval_use_hybrid_search

        # 初始化检索器（基于 RAG + HybridSearch）
        rag_retriever = RAGRetriever(
            self.memory_manager.vector_store_instance,
            # 传入底层 Moonshot 工厂（适配器内部持有原工厂实例）
            getattr(self.model_factory, "_inner", None)
            or MoonshotFactoryAdapter()._inner,
            use_compression=config.retrieval_use_compression,
        )
        self.retriever: RetrievalInterface = HybridRetriever(
            rag_retriever=rag_retriever,
            use_hybrid=use_hybrid_search,
        )

        # 消息仓储：默认使用 MySQL 实现，允许按接口注入其他实现
        self.message_repo: MessageRepositoryInterface = (
            message_repository or MySQLMessageRepository()
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """构建工作流"""
        workflow = StateGraph(cast(Any, SummaryState))

        # 添加节点
        workflow.add_node("load_messages", cast(Any, self.load_messages))
        workflow.add_node("filter_messages", cast(Any, self.filter_messages))
        workflow.add_node("check_cache", cast(Any, self.check_cache))
        workflow.add_node("count_tokens", cast(Any, self.count_tokens))
        workflow.add_node("select_model", cast(Any, self.select_model))
        workflow.add_node("retrieve_memory", cast(Any, self.retrieve_memory))
        workflow.add_node("generate_summary", cast(Any, self.generate_summary))
        workflow.add_node("save_cache", cast(Any, self.save_cache))
        workflow.add_node("save_memory", cast(Any, self.save_memory))

        # 定义边,编排工作流
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

    @staticmethod
    def filter_messages(state: SummaryState) -> SummaryState:
        """过滤消息"""
        state["filtered_messages"] = MessageFilterService.filter(
            state["raw_messages"]
        )
        return state

    def check_cache(self, state: SummaryState) -> SummaryState:
        """检查Redis缓存"""
        cached = self.llm_cache.get(
            group_id=state["group_id"],
            messages=state["filtered_messages"],
        )

        if cached:
            state["summary"] = cached["summary"]
            state["cache_hit"] = True
            state["cache_similarity"] = cached.get("similarity_score", 1.0)
            state["metadata"] = cached.get("metadata", {})
        else:
            state["cache_hit"] = False

        return state

    @staticmethod
    def route_cache(state: SummaryState) -> str:
        """缓存路由"""
        return "hit" if state.get("cache_hit") else "miss"

    def count_tokens(self, state: SummaryState) -> SummaryState:
        """计算 token"""
        state["token_count"] = self.model_factory.token_counter.count_messages_tokens(
            state["filtered_messages"]
        )
        return state

    def select_model(self, state: SummaryState) -> SummaryState:
        """选择模型"""
        state["selected_model"] = self.model_factory.select_model(
            state["token_count"]
        )
        return state

    async def retrieve_memory(self, state: SummaryState) -> SummaryState:
        """检索RAG记忆"""
        query = f"群组 {state['group_id']} 历史讨论重点"

        # 通过检索接口获取上下文
        result = await self.retriever.retrieve(
            query=query,
            group_id=state["group_id"],
            top_k=5,
        )

        state["memory_context"] = (
            "\n\n".join([doc.page_content for doc in result]) if result else ""
        )
        return state

    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """生成LLM结构化摘要"""
        llm = self.model_factory.create_model(
            model_name=state["selected_model"],
        )
        chain = SummaryChain(llm)

        result = await chain.invoke(
            state["filtered_messages"],
            state["memory_context"],
        )
        state["summary"] = self._format_summary(result)

        # 提取 metadata
        state["metadata"] = {
            "model": state["selected_model"],
            "token_count": state["token_count"],
            "concepts": getattr(result, "participants", []),
            "events": self._extract_events_from_result(result),
        }
        state["summary_output"] = result
        return state

    @staticmethod
    def _extract_events_from_result(result: Any) -> List[Dict]:
        """解析话题事件"""
        if not hasattr(result, "topics") or not result.topics:
            return []

        return [
            {
                "event": t.topic,
                "summary": t.summary,
                "participants": getattr(t, "participants", []),
                "timestamp": int(time.time()),
            }
            for t in result.topics
        ]

    @staticmethod
    def _format_summary(res: Any) -> str:
        """
        文本格式化展示。

        为保持兼容性，实际逻辑委托给领域层的 `SummaryFormatService`，
        其实现与原始版本保持一致。
        """
        return SummaryFormatService.format(res)

    def save_cache(self, state: SummaryState) -> SummaryState:
        """保存到 Redis 语义缓存"""
        if not state.get("cache_hit"):
            self.llm_cache.put(
                group_id=state["group_id"],
                hours=state["hours"],
                messages=state["filtered_messages"],
                summary=state["summary"],
                metadata=state.get("metadata", {}),
            )
        return state

    def save_memory(self, state: SummaryState) -> SummaryState:
        """存入长短期记忆系统（Chroma + MySQL）"""
        meta = state.get("metadata", {})
        self.memory_manager.add_memory(
            group_id=state["group_id"],
            messages=state["filtered_messages"],
            summary=state["summary"],
            concepts=meta.get("concepts", []),
            events=meta.get("events", []),
            metadata={"hours": state["hours"], **meta},
        )
        return state

    async def invoke(self, group_id: int, hours: int) -> str:
        """执行工作流"""
        initial_state: SummaryState = {
            "group_id": group_id,
            "hours": hours,
            "raw_messages": [],
            "filtered_messages": [],
            "token_count": 0,
            "selected_model": "",
            "memory_context": "",
            "summary": "",
            "metadata": {},
            "refresh_mode": "high",
            "cache_hit": False,
            "cache_similarity": 0.0,
            "summary_output": None,
        }

        try:
            result = await self.graph.ainvoke(cast(Any, initial_state))
            return result["summary"]
        except Exception as e:  # noqa: BLE001
            return f"日报生成失败 {e}"

