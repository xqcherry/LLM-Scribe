import time
from typing import cast, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from .state import SummaryState
from ...llm.moonshot.model_factory import MoonshotFactory
from ...cache.llm_cache import LLMCacheFactory
from ...memory import MemoryManager
from ...retrieval import RAGRetriever, HybridSearch
from ...core.chains.summary_chain import SummaryChain
from ...storage.database import MessageRepository
from ...pipeline import filter_msgs
from ...config import get_config


class SummaryGraph:
    """摘要生成工作流"""
    
    def __init__(
        self,
        model_factory: MoonshotFactory = None,
        llm_cache = None,
        memory_manager: MemoryManager = None,
        use_hybrid_search: bool = None
    ):
        self.model_factory = model_factory or MoonshotFactory()
        self.llm_cache = llm_cache or LLMCacheFactory.create_cache()
        self.memory_manager = memory_manager or MemoryManager()
        
        # 获取配置
        config = get_config()
        if use_hybrid_search is None:
            use_hybrid_search = getattr(config, 'retrieval_use_hybrid_search', True)
        
        # 初始化检索器
        rag_retriever = RAGRetriever(
            self.memory_manager.vector_store_instance,
            self.model_factory,
            use_compression=getattr(config, 'retrieval_use_compression', True)
        )
        
        # 使用混合检索（推荐）或直接使用 RAGRetriever
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
        
        # 定义边
        workflow.set_entry_point("load_messages")
        workflow.add_edge("load_messages", "filter_messages")
        workflow.add_edge("filter_messages", "check_cache")
        
        # 缓存路由
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
        config = get_config()
        state["filtered_messages"] = filter_msgs(
            state["raw_messages"],
            config.ignore_qq
        )
        return state
    
    def check_cache(self, state: SummaryState) -> SummaryState:
        """检查缓存"""
        cached = self.llm_cache.get(
            state["group_id"],
            state["hours"],
            state["filtered_messages"]
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
    
    def retrieve_memory(self, state: SummaryState) -> SummaryState:
        """检索记忆（使用改进的 RAG 检索）"""
        query = f"群组 {state['group_id']} 最近 {state['hours']} 小时的聊天摘要"
        
        # 使用改进的检索器
        if isinstance(self.retriever, HybridSearch):
            # 使用混合检索（向量检索 + 重排序）
            result = self.retriever.search(
                query=query,
                group_id=state["group_id"],
                top_k=5,
                use_rerank=True
            )
            # 将 Document 列表转换为文本
            contexts = [doc.page_content for doc in result]
        else:
            # 使用 RAGRetriever
            result = self.retriever.retrieve_relevant_context(
                query=query,
                group_id=state["group_id"],
                top_k=5
            )
            contexts = [doc.page_content for doc in result]
        
        state["memory_context"] = "\n\n".join(contexts) if contexts else ""
        return state
    
    async def generate_summary(self, state: SummaryState) -> SummaryState:
        """生成摘要"""
        llm = self.model_factory.create_model(
            model_name=state["selected_model"]
        )
        chain = SummaryChain(llm)
        
        result = await chain.invoke(
            state["filtered_messages"],
            state["memory_context"]
        )
        
        # 转换为字符串格式
        state["summary"] = self._format_summary(result)
        
        # 从摘要结果中提取概念和事件
        concepts = result.participants if hasattr(result, 'participants') else []
        events = []
        if hasattr(result, 'topics') and result.topics:
            for topic in result.topics:
                events.append({
                    "event": topic.topic,
                    "participants": topic.participants if hasattr(topic, 'participants') else [],
                    "timestamp": int(time.time())
                })
        
        state["metadata"] = {
            "model": state["selected_model"],
            "token_count": state["token_count"],
            "concepts": concepts,
            "events": events
        }
        state["summary_output"] = result  # 保存原始结果以便后续使用
        return state

    @staticmethod
    def _format_summary(summary_output) -> str:
        """格式化摘要输出"""
        lines = [f"【整体摘要】\n{summary_output.overall_summary}\n"]
        
        if summary_output.topics:
            lines.append("【话题总结】")
            for topic in summary_output.topics:
                lines.append(f"\n话题：{topic.topic}")
                lines.append(f"摘要：{topic.summary}")
                lines.append(f"参与者：{', '.join(topic.participants)}")
        
        if summary_output.key_quotes:
            lines.append(f"\n【关键引用】\n" + "\n".join(summary_output.key_quotes))
        
        lines.append(f"\n【情感倾向】{summary_output.sentiment}")
        
        return "\n".join(lines)
    
    def save_cache(self, state: SummaryState) -> SummaryState:
        """保存缓存"""
        if not state.get("cache_hit"):
            self.llm_cache.put(
                state["group_id"],
                state["hours"],
                state["filtered_messages"],
                state["summary"],
                state.get("metadata", {})
            )
        return state
    
    def save_memory(self, state: SummaryState) -> SummaryState:
        """保存记忆到所有子系统（事件记忆、语义记忆、向量存储）"""
        # 从摘要中提取概念和事件（简化实现，实际可以从 SummaryOutput 中提取）
        concepts = state.get("metadata", {}).get("concepts", [])
        events = state.get("metadata", {}).get("events", [])
        
        # 使用 MemoryManager 的统一接口保存记忆
        self.memory_manager.add_memory(
            group_id=state["group_id"],
            messages=state["filtered_messages"],
            summary=state["summary"],
            concepts=concepts,
            events=events,
            metadata={
                "hours": state["hours"],
                **state.get("metadata", {})
            }
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
            "cache_similarity": 0.0
        }
        
        result = await self.graph.ainvoke(cast(Any, initial_state))
        return result["summary"]
