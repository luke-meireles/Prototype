"""Tool: consulta histórico clínico do beneficiário Care Plus (mockado)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Caminho para o mock — relativo à raiz do projeto
_MOCK_PATH = Path(__file__).resolve().parents[2] / "data" / "mocks" / "perfis_clinicos.json"


class HistoricoInput(BaseModel):
    """Schema de entrada validado por Pydantic."""

    beneficiario_id: str = Field(..., description="ID no formato BENEF-XXX")


def _carregar_mock() -> dict[str, Any]:
    with _MOCK_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def consultar_historico_paciente(beneficiario_id: str) -> dict[str, Any]:
    """Retorna o dossiê clínico mockado do beneficiário.

    Em produção, este método seria substituído por uma chamada autenticada
    ao prontuário eletrônico Care Plus, com auditoria LGPD apropriada.
    """
    HistoricoInput(beneficiario_id=beneficiario_id)  # valida o input

    base = _carregar_mock()
    perfil = base.get(beneficiario_id)

    if perfil is None:
        return {
            "encontrado": False,
            "beneficiario_id": beneficiario_id,
            "mensagem": "Beneficiário não localizado na base mockada.",
        }

    return {
        "encontrado": True,
        "beneficiario_id": perfil["beneficiario_id"],
        "nome": perfil["nome"],
        "idade": perfil["idade"],
        "sexo": perfil["sexo"],
        "condicoes_cronicas": perfil["condicoes_cronicas"],
        "alergias": perfil["alergias"],
        "medicamentos_em_uso": perfil["medicamentos_em_uso"],
        "ultimas_consultas": perfil["ultimas_consultas"],
    }
