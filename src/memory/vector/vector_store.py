from typing import Dict, List
import chromadb
from src.llm.embedding.embedding_model import get_embeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import plugin_config as config
from src.memory.vector.vector_store_base import BaseVectorStore


class VectorMemoryStore(BaseVectorStore):
    """基于 ChromaDB 的向量记忆存储"""

    def __init__(self):
        self.client = chromadb.HttpClient(
            host=config.chroma_host,
            port=config.chroma_port
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
