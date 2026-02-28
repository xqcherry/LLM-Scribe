from typing import Dict, List, Optional
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from llm_scribe.config import plugin_config as config
from llm_scribe.memory.vector.vector_store_base import BaseVectorStore

_embeddings_instance: Optional[HuggingFaceEmbeddings] = None
def get_embeddings() -> HuggingFaceEmbeddings:
    """获取 Embeddings 单例实例"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=config.huggingface_model_name,
            model_kwargs=config.huggingface_model_kwargs
        )
    return _embeddings_instance

class VectorMemoryStore(BaseVectorStore):
    """基于 ChromaDB 的向量记忆存储"""

    def __init__(self):
        self.client = chromadb.HttpClient(
            host=config.chromadb_host,
            port=config.chromadb_port
        )

        self.embeddings = get_embeddings()

        self.vector_store = Chroma(
            client=self.client,
            collection_name=config.chroma_collection_name,
            embedding_function=self.embeddings
        )

    def add_summary(
            self,
            group_id: int,
            summary: str,
            metadata: Dict,
    ):
        final_metadata = {
            "group_id": str(group_id),
            "timestamp": metadata['timestamp'],
            "hours": metadata['hours'],
            **metadata,
        }

        doc = Document(
            page_content=summary,
            metadata=final_metadata,
        )

        self.vector_store.add_documents([doc])

    def search_similar_summaries(
            self,
            query: str,
            group_id: int,
            top_k: int = 3
    ) -> List[Document]:
        results = self.vector_store.similarity_search(
            query=query,
            k=top_k,
            filter={"group_id": str(group_id)}
        )

        return results
