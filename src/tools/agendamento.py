"""Tool: agendamento de teleconsulta Care Plus (mockado)."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

_MOCK_PATH = Path(__file__).resolve().parents[2] / "data" / "mocks" / "agendamentos.json"

# Janela de horário de atendimento por urgência (em minutos a partir de agora)
_JANELA_POR_URGENCIA: dict[str, int] = {
    "alta": 60,
    "media": 24 * 60,
    "baixa": 7 * 24 * 60,
}


class AgendamentoInput(BaseModel):
    especialidade: str
    data_preferencia: str = Field(..., description="Data ISO 8601 YYYY-MM-DD")
    urgencia: Literal["baixa", "media", "alta"]


def _carregar_mock() -> dict[str, Any]:
    with _MOCK_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def agendar_teleconsulta(
    especialidade: str,
    data_preferencia: str,
    urgencia: Literal["baixa", "media", "alta"],
) -> dict[str, Any]:
    """Cria um agendamento mockado de teleconsulta.

    A escolha do médico é determinística (primeiro da lista) para evitar
    flutuação nos resultados das demos. O horário simulado respeita a janela
    da urgência informada.
    """
    AgendamentoInput(
        especialidade=especialidade,
        data_preferencia=data_preferencia,
        urgencia=urgencia,
    )

    base = _carregar_mock()
    medicos = base["medicos_disponiveis"].get(especialidade.lower())
    if not medicos:
        return {
            "sucesso": False,
            "mensagem": (
                f"Especialidade '{especialidade}' não está disponível em telemedicina "
                "ou não foi reconhecida. Especialidades cobertas: "
                f"{list(base['medicos_disponiveis'].keys())}"
            ),
        }

    medico = medicos[0]
    janela_min = _JANELA_POR_URGENCIA[urgencia]
    horario = datetime.now(timezone.utc) + timedelta(minutes=janela_min)

    sufixo = "".join(random.choices("0123456789", k=5))
    id_consulta = f"TC-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{sufixo}"
    link = base["template_link"].format(id_consulta=id_consulta)

    return {
        "sucesso": True,
        "id_consulta": id_consulta,
        "horario_confirmado": horario.isoformat(),
        "link_teleconsulta": link,
        "medico_atribuido": medico,
        "especialidade": especialidade.lower(),
        "urgencia": urgencia,
        "observacao": (
            "Este é um agendamento simulado para fins de demonstração. "
            "Em produção, dispararia confirmação por SMS, push e e-mail "
            "ao beneficiário."
        ),
    }
