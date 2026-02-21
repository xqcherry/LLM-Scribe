"""RAG 检索器"""
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.schema import Document
from typing import List, Optional, Dict
from ...memory import VectorMemoryStore
from ...llm.moonshot.model_factory import MoonshotFactory
from ...config import get_config


class RAGRetriever:
    """
    RAG 检索器：基于向量相似度的检索增强生成
    
    支持：
    - 向量相似度检索
    - 上下文压缩（提取相关片段）
    - 可配置的相似度阈值
    - 按 group_id 过滤
    """
    
    def __init__(
        self,
        vector_store: VectorMemoryStore,
        model_factory: MoonshotFactory,
        score_threshold: float = None,
        use_compression: bool = True,
        compression_model: str = "moonshot-v1-8k"
    ):
        """
        初始化 RAG 检索器
        
        Args:
            vector_store: 向量存储实例
            model_factory: LLM 模型工厂
            score_threshold: 相似度阈值（0-1），None 则使用配置默认值
            use_compression: 是否使用上下文压缩
            compression_model: 用于压缩的模型名称
        """
        self.vector_store = vector_store
        self.model_factory = model_factory
        self.use_compression = use_compression
        
        # 获取配置
        config = get_config()
        self.score_threshold = score_threshold or getattr(config, 'retrieval_score_threshold', 0.7)
        
        # 初始化基础检索器
        self._init_retriever()
        
        # 初始化压缩器（如果需要）
        if self.use_compression:
            try:
                llm = model_factory.create_model(compression_model)
                self.compressor = LLMChainExtractor.from_llm(llm)
                self.compression_retriever = ContextualCompressionRetriever(
                    base_compressor=self.compressor,
                    base_retriever=self.base_retriever
                )
            except Exception as e:
                # 如果压缩器初始化失败，回退到不使用压缩
                print(f"警告：压缩器初始化失败，将不使用上下文压缩: {e}")
                self.use_compression = False
                self.compression_retriever = None
        else:
            self.compression_retriever = None
    
    def _init_retriever(self):
        """初始化基础检索器"""
        try:
            self.base_retriever = self.vector_store.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "score_threshold": self.score_threshold,
                    "k": 10  # 检索更多候选，后续可以重排序
                }
            )
        except Exception as e:
            # 如果相似度阈值检索失败，回退到普通检索
            print(f"警告：相似度阈值检索初始化失败，使用普通检索: {e}")
            self.base_retriever = self.vector_store.vector_store.as_retriever(
                search_kwargs={"k": 10}
            )
    
    def retrieve_relevant_context(
        self,
        query: str,
        group_id: int,
        top_k: int = 5,
        use_rerank: bool = False
    ) -> List[Document]:
        """
        检索相关上下文
        
        Args:
            query: 查询文本
            group_id: 群组 ID（用于过滤）
            top_k: 返回前 k 个文档
            use_rerank: 是否使用重排序（需要配合 HybridSearch 使用）
            
        Returns:
            相关文档列表
        """
        try:
            # 构建查询（添加 group_id 上下文）
            enhanced_query = f"群组 {group_id}: {query}"
            
            # 使用压缩检索器或基础检索器
            if self.use_compression and self.compression_retriever:
                results = self.compression_retriever.get_relevant_documents(enhanced_query)
            else:
                results = self.base_retriever.get_relevant_documents(enhanced_query)
            
            # 按 group_id 过滤（双重保险）
            filtered_results = self._filter_by_group_id(results, group_id)
            
            # 限制返回数量
            return filtered_results[:top_k]
            
        except Exception as e:
            print(f"检索失败: {e}")
            # 回退到直接使用向量存储的搜索方法
            try:
                results = self.vector_store.search_similar_summaries(
                    query,
                    group_id,
                    top_k
                )
                return results
            except Exception as e2:
                print(f"回退检索也失败: {e2}")
                return []
    
    def _filter_by_group_id(self, documents: List[Document], group_id: int) -> List[Document]:
        """按 group_id 过滤文档"""
        filtered = []
        for doc in documents:
            if isinstance(doc.metadata, dict):
                doc_group_id = doc.metadata.get('group_id')
            elif hasattr(doc.metadata, 'group_id'):
                doc_group_id = getattr(doc.metadata, 'group_id', None)
            else:
                doc_group_id = None
            
            if doc_group_id == group_id or doc_group_id is None:
                filtered.append(doc)
        
        return filtered
    
    def retrieve_with_metadata(
        self,
        query: str,
        group_id: int,
        top_k: int = 5
    ) -> Dict[str, any]:
        """
        检索并返回带元数据的结果
        
        Args:
            query: 查询文本
            group_id: 群组 ID
            top_k: 返回前 k 个文档
            
        Returns:
            包含文档列表和元数据的字典
        """
        documents = self.retrieve_relevant_context(query, group_id, top_k)
        
        return {
            "documents": documents,
            "count": len(documents),
            "query": query,
            "group_id": group_id,
            "score_threshold": self.score_threshold
        }
