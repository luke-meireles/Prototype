"""Tool: leitura de sinais vitais do wearable (mockado).

Em produção, integraria com Apple Health / Google Fit / Fitbit via OAuth.
``periodo_dias`` é restrito a 1..30 para refletir o limite de retenção
típico desses provedores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_MOCK_PATH = Path(__file__).resolve().parents[2] / "data" / "mocks" / "wearable_apple_health.json"


class WearableInput(BaseModel):
    beneficiario_id: str
    periodo_dias: int = Field(..., ge=1, le=30)


def _carregar_mock() -> dict[str, Any]:
    with _MOCK_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def consultar_sinais_vitais_wearable(
    beneficiario_id: str, periodo_dias: int
) -> dict[str, Any]:
    """Retorna o snapshot mockado de sinais vitais do wearable."""
    WearableInput(beneficiario_id=beneficiario_id, periodo_dias=periodo_dias)

    base = _carregar_mock()
    dados = base.get(beneficiario_id)
    if dados is None:
        return {
            "encontrado": False,
            "beneficiario_id": beneficiario_id,
            "mensagem": "Sem dados de wearable para este beneficiário.",
        }

    passos = dados["passos_diarios"][-periodo_dias:]
    return {
        "encontrado": True,
        "beneficiario_id": beneficiario_id,
        "fonte": dados["fonte"],
        "ultima_sincronizacao": dados["ultima_sincronizacao"],
        "periodo_dias": periodo_dias,
        "frequencia_cardiaca_bpm": dados["frequencia_cardiaca_bpm"],
        "spo2_percent": dados["spo2_percent"],
        "passos_diarios": passos,
        "qualidade_sono": dados["qualidade_sono"],
        "variabilidade_cardiaca_ms": dados["variabilidade_cardiaca_ms"],
        "alertas_detectados": dados["alertas_detectados"],
    }
