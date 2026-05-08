"""Interface de reranker — desligada por padrão na PoC.

Esta camada existe para demonstrar a arquitetura prevista para produção.
Quando ativada, espera-se integrar Qwen3-Reranker (ou equivalente) para
reordenar os chunks recuperados antes de compor o prompt final.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RerankerConfig:
    """Configuração da camada de reranker.

    Atributos:
        enabled: se False (padrão na PoC), o reranker é um no-op.
        model: nome do modelo de reranking. Em produção: ``Qwen3-Reranker-0.6B``.
        top_n: número de chunks a manter após reranking.
    """

    enabled: bool = False
    model: str = "Qwen3-Reranker-0.6B"
    top_n: int = 4


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    config: RerankerConfig | None = None,
) -> list[dict[str, Any]]:
    """Reordena os chunks segundo relevância com a query.

    Implementação atual: identidade (no-op). A integração com modelo de
    reranking foi propositalmente adiada para evitar custo desnecessário na
    PoC; o ganho marginal observado nos primeiros experimentos não justificou
    a latência adicional. Quando ativarmos, usaremos a API DashScope do
    Qwen3-Reranker (TODO documentado).
    """
    if config is None:
        config = RerankerConfig()

    if not config.enabled:
        return chunks

    # TODO: integrar Qwen3-Reranker via DashScope quando o trade-off
    # latência/qualidade for validado em ambiente de homologação.
    #
    # Esboço de implementação:
    #   client = openai.OpenAI(api_key=..., base_url="https://...")
    #   response = client.rerank.create(model=config.model, query=query,
    #                                   documents=[c["documento"] for c in chunks])
    #   ordered = sorted(zip(chunks, response.scores),
    #                    key=lambda x: x[1], reverse=True)
    #   return [c for c, _ in ordered][:config.top_n]
    return chunks[: config.top_n]
