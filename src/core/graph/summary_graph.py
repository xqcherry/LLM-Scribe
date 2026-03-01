import time
from typing import cast, Any, List, Dict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from llm_scribe.core.graph.state import SummaryState
from llm_scribe.llm.moonshot.model_factory import MoonshotFactory
from llm_scribe.cache.llm_cache import LLMCacheFactory
from llm_scribe.memory import MemoryManager
from llm_scribe.retrieval import RAGRetriever, HybridSearch
from llm_scribe.core.chains.summary_chain import SummaryChain
from llm_scribe.pipeline import filter_msgs
from llm_scribe.config import plugin_config as config
from llm_scribe.storage.database.repositories import MessageRepository


class SummaryGraph:
    """摘要生成工作流"""
    
    def __init__(
        self,
        model_factory: MoonshotFactory = None,
        memory_manager: MemoryManager = None,
        use_hybrid_search: bool = None
    ):
        # 核心模型工厂
        self.model_factory = model_factory or MoonshotFactory()
        # 语义缓存
        self.llm_cache = LLMCacheFactory.create_cache()
        # 记忆管理器
        self.memory_manager = memory_manager or MemoryManager()

        # 检索配置
        if use_hybrid_search is None:
            use_hybrid_search = config.retrieval_use_hybrid_search
        
        # 初始化检索器
        rag_retriever = RAGRetriever(
            self.memory_manager.vector_store_instance,
            self.model_factory,
            use_compression=config.retrieval_use_compression
        )
        
        # 使用混合检索
        if use_hybrid_search:
            self.retriever = HybridSearch(rag_retriever)
        else:
            self.retriever = rag_retriever
        
        self.message_repo = MessageRepository()
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
            {"hit": END, "miss": "count_tokens"}
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
            state["hours"]
        )
        return state

    @staticmethod
    def filter_messages(state: SummaryState) -> SummaryState:
        """过滤消息"""
        state["filtered_messages"] = filter_msgs(
            state["raw_messages"],
            config.ignore_qq
        )
        return state
    
    def check_cache(self, state: SummaryState) -> SummaryState:
        """检查Redis缓存"""
        cached = self.llm_cache.get(
            group_id=state["group_id"],
            messages=state["filtered_messages"]
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
        
        # 使用改进的检索器
        if isinstance(self.retriever, HybridSearch):
            # 使用混合检索（向量检索 + 重排序）
            result = await self.retriever.search(
                query=query,
                group_id=state["group_id"],
                top_k=5
            )
        else:
            # 使用 RAGRetriever
            result = await self.retriever.retrieve_relevant_context(
                query=query,
                group_id=state["group_id"]
            )

        state["memory_context"] = "\n\n".join([doc.page_content for doc in result]) if result else ""
        return state
    
    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """生成LLM结构化摘要"""
        llm = self.model_factory.create_model(
            model_name=state["selected_model"]
        )
        chain = SummaryChain(llm)
        
        result = await chain.invoke(
            state["filtered_messages"],
            state["memory_context"]
        )
        state["summary"] = self._format_summary(result)
        
        # 提取 metadata
        state["metadata"] = {
            "model": state["selected_model"],
            "token_count": state["token_count"],
            "concepts": getattr(result, 'participants', []),
            "events": self._extract_events_from_result(result)
        }
        state["summary_output"] = result
        return state

    @staticmethod
    def _extract_events_from_result(result: Any) -> List[Dict]:
        """解析话题事件"""
        if not hasattr(result, 'topics') or not result.topics:
            return []

        return [
            {
                "event": t.topic,
                "summary": t.summary,
                "participants": getattr(t, 'participants', []),
                "timestamp": int(time.time())
            }
            for t in result.topics
        ]

    @staticmethod
    def _format_summary(res: Any) -> str:
        """文本格式化展示（使用字面量列表合并优化风格）"""
        lines = [
            f"📊 【群聊摘要】",
            f"🔍 核心摘要：\n{res.overall_summary}\n"
        ]

        if res.topics:
            lines.append("💡 话题回顾：")
            lines.extend([f"• {t.topic}" for t in res.topics[:5]])

        if res.key_quotes:
            lines.append(f"\n💬 精彩瞬间：\n“{res.key_quotes[0]}”")

        return "\n".join(lines)
    
    def save_cache(self, state: SummaryState) -> SummaryState:
        """保存到 Redis 语义缓存"""
        if not state.get("cache_hit"):
            self.llm_cache.put(
                group_id=state["group_id"],
                hours=state["hours"],
                messages=state["filtered_messages"],
                summary=state["summary"],
                metadata=state.get("metadata", {})
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
            metadata={"hours": state["hours"], **meta}
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
            "summary_output": None
        }

        try:
            result = await self.graph.ainvoke(cast(Any, initial_state))
            return result["summary"]
        except Exception as e:
            return f"日报生成失败 {e}"
