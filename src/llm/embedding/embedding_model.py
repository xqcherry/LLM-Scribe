from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import plugin_config as config

_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """获取 Embedding 模型实例"""
    global _embeddings_instance
    if _embeddings_instance is None:

        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=config.huggingface_model_name,
            model_kwargs=config.huggingface_model_kwargs
        )

    return _embeddings_instance