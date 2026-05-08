"""Camada RAG — indexação ChromaDB + retrieval + reranker (interface)."""

from src.rag.indexer import indexar_knowledge_base, get_collection
from src.rag.retriever import recuperar_chunks
from src.rag.reranker import rerank, RerankerConfig

__all__ = [
    "indexar_knowledge_base",
    "get_collection",
    "recuperar_chunks",
    "rerank",
    "RerankerConfig",
]
