"""Retrieval semântico sobre o ChromaDB com filtro opcional por metadado.

Converte distância cosseno em score (1 - dist) para leitura mais
intuitiva: 1.0 = idêntico, 0.0 = totalmente diferente.
"""

from __future__ import annotations

from typing import Any

from src.rag.indexer import get_collection
from src.rag.reranker import RerankerConfig, rerank


def recuperar_chunks(
    query: str,
    top_k: int = 4,
    filtro_tipo: str | list[str] | None = None,
    reranker_config: RerankerConfig | None = None,
) -> list[dict[str, Any]]:
    """Recupera os top-k chunks mais relevantes para a query.

    Args:
        query: pergunta ou contexto a buscar.
        top_k: número de chunks a retornar.
        filtro_tipo: opcional — restringe por tipo (ex: "red_flag",
            "bula"). Aceita string única ou lista para OR semântico.
        reranker_config: se fornecido, aplica reranker ao resultado.

    Returns:
        Lista de dicionários com chaves: documento, fonte, tipo, score, chunk_id.
    """
    coll = get_collection()

    where: dict[str, Any] | None = None
    if isinstance(filtro_tipo, str):
        where = {"tipo": filtro_tipo}
    elif isinstance(filtro_tipo, list) and filtro_tipo:
        where = {"tipo": {"$in": filtro_tipo}}

    # Busca o dobro do top_k para dar margem ao reranker (quando ativado).
    raw = coll.query(
        query_texts=[query],
        n_results=max(top_k * 2, top_k),
        where=where,
    )

    documentos = raw.get("documents", [[]])[0]
    metadados = raw.get("metadatas", [[]])[0]
    distancias = raw.get("distances", [[]])[0]

    chunks: list[dict[str, Any]] = []
    for doc, meta, dist in zip(documentos, metadados, distancias):
        chunks.append(
            {
                "documento": doc,
                "fonte": meta.get("fonte"),
                "tipo": meta.get("tipo"),
                "chunk_id": meta.get("chunk_id"),
                "score": round(1.0 - float(dist), 4),
            }
        )

    if reranker_config and reranker_config.enabled:
        chunks = rerank(query, chunks, config=reranker_config)

    return chunks[:top_k]
