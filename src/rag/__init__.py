"""Camada RAG — indexação ChromaDB + retrieval + reranker (interface).

RAG = Retrieval-Augmented Generation. Ideia central: dar ao LLM acesso
controlado a documentos curados (knowledge base) em vez de confiar só
no conhecimento do treino. Reduz alucinação clínica e mantém respostas
ancoradas em material auditável.

Três sub-módulos:
- ``indexer``: lê os .md da KB, divide em chunks, gera embeddings e
  grava no ChromaDB. Executado uma vez por sessão.
- ``retriever``: faz a busca semântica para uma query — devolve top-k
  chunks com seus scores.
- ``reranker``: interface para reordenar resultados; desligado por
  padrão na PoC.
"""

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
