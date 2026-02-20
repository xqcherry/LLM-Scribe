"""RAG 检索器"""
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.schema import Document
from typing import List
from ...memory.vector_store import VectorMemoryStore
from ...llm.moonshot.model_factory import MoonshotFactory


class RAGRetriever:
    """RAG 检索器"""
    
    def __init__(
        self,
        vector_store: VectorMemoryStore,
        model_factory: MoonshotFactory
    ):
        self.vector_store = vector_store
        self.model_factory = model_factory
        
        # 基础检索器
        self.base_retriever = vector_store.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.7, "k": 5}
        )
        
        # 使用小模型进行压缩
        llm = model_factory.create_model("moonshot-v1-8k")
        self.compressor = LLMChainExtractor.from_llm(llm)
        
        # 压缩检索器
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=self.base_retriever
        )
    
    def retrieve_relevant_context(
        self,
        query: str,
        group_id: int,
        top_k: int = 5
    ) -> List[Document]:
        """检索相关上下文"""
        results = self.compression_retriever.get_relevant_documents(
            f"群组 {group_id}: {query}"
        )
        return results
