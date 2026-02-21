"""ChromaDB 向量存储实现"""
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from typing import List, Dict
from llm_scribe.memory.vector.vector_store_base import BaseVectorStore
from ...config import get_config


class VectorMemoryStore(BaseVectorStore):
    """基于 ChromaDB 的向量记忆存储"""
    
    def __init__(self, persist_directory: str = None):
        config = get_config()
        self.persist_directory = persist_directory or config.chroma_persist_dir
        
        # 使用本地 Embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def add_summary(
        self,
        group_id: int,
        summary: str,
        metadata: Dict
    ):
        """添加摘要"""
        doc = Document(
            page_content=summary,
            metadata={
                "group_id": group_id,
                "timestamp": metadata.get("timestamp"),
                "hours": metadata.get("hours"),
                **metadata
            }
        )
        self.vector_store.add_documents([doc])
    
    def search_similar_summaries(
        self,
        query: str,
        group_id: int,
        top_k: int = 3
    ) -> List[Document]:
        """搜索相似摘要"""
        results = self.vector_store.similarity_search(
            query,
            k=top_k,
            filter={"group_id": group_id}
        )
        return results
