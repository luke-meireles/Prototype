"""Tool: verificação de interações medicamentosas (mockado).

Compara todos os pares da lista contra a base mockada. Em produção,
integraria com UpToDate, Micromedex ou a base de bulas da ANVISA.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

_MOCK_PATH = Path(__file__).resolve().parents[2] / "data" / "mocks" / "interacoes_medicamentosas.json"

# Hierarquia de severidade — usada para retornar a mais alta encontrada
_SEVERIDADE_RANK = {"baixa": 1, "moderada": 2, "alta": 3, "contraindicada": 4}


class InteracoesInput(BaseModel):
    medicamentos: list[str] = Field(..., min_length=2)

    @field_validator("medicamentos")
    @classmethod
    def _normaliza(cls, v: list[str]) -> list[str]:
        # trim + lowercase + espaço→underscore. Em produção, usar um
        # normalizador clínico de verdade (RxNorm / SNOMED CT).
        return [m.strip().lower().replace(" ", "_") for m in v]


def _carregar_base() -> list[dict[str, Any]]:
    with _MOCK_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)["interacoes"]


def verificar_interacoes_medicamentosas(medicamentos: list[str]) -> dict[str, Any]:
    """Retorna a maior severidade encontrada entre pares de medicamentos."""
    payload = InteracoesInput(medicamentos=medicamentos)
    lista_normalizada = payload.medicamentos
    base = _carregar_base()

    encontradas: list[dict[str, Any]] = []
    for a, b in combinations(lista_normalizada, 2):
        for entrada in base:
            par = {p.lower() for p in entrada["par"]}
            if {a, b}.issubset(par) or {a, b} == par:
                encontradas.append(
                    {
                        "medicamentos": entrada["par"],
                        "severidade": entrada["severidade"],
                        "descricao": entrada["descricao"],
                        "recomendacao": entrada["recomendacao"],
                    }
                )

    if not encontradas:
        return {
            "interacoes_encontradas": [],
            "severidade": "baixa",
            "recomendacao": (
                "Nenhuma interação relevante identificada na base consultada. "
                "Esta verificação não substitui a análise médica, especialmente "
                "se houver comorbidades ou polifarmácia."
            ),
        }

    severidade_max = max(encontradas, key=lambda e: _SEVERIDADE_RANK[e["severidade"]])

    return {
        "interacoes_encontradas": encontradas,
        "severidade": severidade_max["severidade"],
        "recomendacao": (
            f"Foram identificadas {len(encontradas)} interação(ões). "
            f"Severidade máxima: {severidade_max['severidade']}. "
            f"{severidade_max['recomendacao']} "
            "Encaminhe-se para avaliação médica antes de qualquer mudança no esquema."
        ),
    }
