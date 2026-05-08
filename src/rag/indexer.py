"""Indexação da knowledge base no ChromaDB com embeddings multilíngues."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Diretórios
_KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"
_CHROMA_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parents[2] / "chroma_db")))

# Mapeamento nome de arquivo → tipo de conteúdo (para metadados)
_TIPO_POR_ARQUIVO: dict[str, str] = {
    "bulas_resumidas.md": "bula",
    "triagem_manchester_simplificado.md": "protocolo",
    "politicas_care_plus_telemedicina.md": "politica",
    "red_flags_clinicas.md": "red_flag",
    "cartilha_beneficiario_blua.md": "cartilha",
    "protocolos_check_up_preventivo.md": "preventivo",
    "mapa_especialidades.md": "especialidade",
}

_COLLECTION = "bluadiagnostics_kb"
_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"


def _embedding_function() -> Any:
    """Constrói a função de embeddings multilíngue.

    Usamos sentence-transformers via integração nativa do Chroma. O modelo
    multilingual-e5-large performa bem em PT-BR sem fine-tuning."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=_EMBEDDING_MODEL
    )


def _client() -> chromadb.ClientAPI:
    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(_CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


def get_collection() -> chromadb.api.models.Collection.Collection:
    """Retorna (ou cria) a collection persistida."""
    return _client().get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def _splitter() -> RecursiveCharacterTextSplitter:
    """Splitter com 300–400 tokens equivalentes (≈1500 chars) e overlap 50."""
    return RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )


def indexar_knowledge_base(forcar_reindex: bool = False) -> dict[str, Any]:
    """Indexa todos os documentos da knowledge_base no ChromaDB.

    Args:
        forcar_reindex: se True, deleta a collection existente antes de
            reindexar. Útil quando o conteúdo de KB muda.

    Returns:
        Estatísticas da operação.
    """
    client = _client()
    if forcar_reindex:
        try:
            client.delete_collection(_COLLECTION)
        except Exception:
            pass

    coll = client.get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )

    if coll.count() > 0 and not forcar_reindex:
        return {
            "status": "ja_indexado",
            "total_chunks": coll.count(),
            "collection": _COLLECTION,
        }

    splitter = _splitter()
    documentos: list[str] = []
    metadados: list[dict[str, Any]] = []
    ids: list[str] = []

    for arquivo in sorted(_KB_DIR.glob("*.md")):
        tipo = _TIPO_POR_ARQUIVO.get(arquivo.name, "outro")
        texto = arquivo.read_text(encoding="utf-8")
        chunks = splitter.split_text(texto)
        for idx, chunk in enumerate(chunks):
            documentos.append(chunk)
            metadados.append(
                {
                    "tipo": tipo,
                    "fonte": arquivo.name,
                    "chunk_id": idx,
                }
            )
            ids.append(f"{arquivo.stem}_{idx:03d}")

    if not documentos:
        return {
            "status": "vazio",
            "total_chunks": 0,
            "collection": _COLLECTION,
        }

    coll.add(documents=documentos, metadatas=metadados, ids=ids)
    return {
        "status": "indexado",
        "total_chunks": len(documentos),
        "collection": _COLLECTION,
        "fontes": sorted({m["fonte"] for m in metadados}),
    }
