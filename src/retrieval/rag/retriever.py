from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from langchain_core.documents import Document
from typing import List
from llm_scribe.memory import VectorMemoryStore
from llm_scribe.llm.moonshot.model_factory import MoonshotFactory
from llm_scribe.config import plugin_config as config


class RAGRetriever:
    """基于向量相似度的检索增强生成"""

    def __init__(
            self,
            vector_store: VectorMemoryStore,
            model_factory: MoonshotFactory,
            score_threshold: float = None,
            use_compression: bool = True,
            compression_model: str = "moonshot-v1-8k"
    ):
        self.vector_store = vector_store
        self.model_factory = model_factory
        self.use_compression = use_compression

        self.score_threshold = score_threshold or config.retrieval_score_threshold
        self._init_retriever()

        # 优化压缩器
        if self.use_compression:
            try:
                llm = model_factory.create_model(compression_model)
                self.compressor = LLMChainExtractor.from_llm(llm)

                self.compression_retriever = ContextualCompressionRetriever(
                    base_compressor=self.compressor,
                    base_retriever=self.base_retriever
                )
            except Exception as e:
                print(f"警告：压缩器初始化失败: {e}")
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
                    "k": 10
                }
            )
        except Exception as e:
            print(f"警告：回退到普通检索: {e}")
            self.base_retriever = self.vector_store.vector_store.as_retriever(
                search_kwargs={"k": 10}
            )

    async def retrieve_relevant_context(
            self,
            query: str,
            group_id: int,
            top_k: int = 5
    ) -> List[Document]:
        try:
            filter_dict = {"group_id": group_id}

            if self.use_compression and self.compression_retriever:
                results = await self.compression_retriever.aget_relevant_documents(
                    query,
                    metadata_filter=filter_dict
                )
            else:
                results = await self.base_retriever.aget_relevant_documents(
                    query,
                    filter=filter_dict
                )

            filtered_results = self._filter_by_group_id(results, group_id)

            return filtered_results[:top_k]

        except Exception as e:
            print(f"检索失败: {e}")
            return self.vector_store.search_similar_summaries(query, group_id, top_k)

    @staticmethod
    def _filter_by_group_id(
            documents: List[Document],
            group_id: int
    ) -> List[Document]:
        """按 group_id 过滤文档"""
        filtered = []
        for doc in documents:
            doc_group_id = doc.metadata.get('group_id') if isinstance(doc.metadata, dict) else getattr(doc.metadata,
                                                                                                       'group_id', None)
            if doc_group_id == group_id:
                filtered.append(doc)
        return filtered