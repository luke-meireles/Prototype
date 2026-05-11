"""Roteador de intenção — classifica a mensagem do usuário em uma das 5 intents.

Buckets: checkup, triagem_sintoma, prescricao, duvida_geral, fora_escopo.
Usa Qwen com thinking desligado, temperature 0.1 e saída forçada em JSON
— classificação é tarefa rápida e queremos determinismo.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from src.llm.qwen_client import chat

INTENT_VALORES = Literal[
    "checkup", "triagem_sintoma", "prescricao", "duvida_geral", "fora_escopo"
]

_PROMPT_ROTEADOR = """Você é o Roteador de Intenção do BluaDiagnostics.

Classifique a última mensagem do usuário em UMA das intents:
- "checkup": coleta de sintomas, sinais vitais ou avaliação preventiva
- "triagem_sintoma": queixa específica que precisa de classificação de risco
- "prescricao": pedido vindo de médico para apoio à prescrição (raro, atende caminho secundário)
- "duvida_geral": dúvida educacional, dúvida sobre o app, sobre LGPD, agendamento
- "fora_escopo": qualquer coisa não clínica (investimentos, redação comercial, código, opinião política, etc.)

Responda EXCLUSIVAMENTE em JSON com a estrutura:
{"intent": "...", "confianca": 0.0, "justificativa": "..."}

Sem texto antes nem depois do JSON."""


def classificar_intent(
    mensagem_usuario: str,
    historico: list[dict[str, Any]] | None = None,
    backend: str = "dashscope",
) -> dict[str, Any]:
    """Classifica a intent do usuário usando Qwen com thinking desligado.

    Args:
        mensagem_usuario: última mensagem recebida.
        historico: turnos anteriores (opcional, ajuda em diálogos).
        backend: ``"dashscope"`` ou ``"ollama"``.

    Returns:
        Dict com chaves ``intent``, ``confianca``, ``justificativa``.
    """
    messages: list[dict[str, Any]] = [{"role": "system", "content": _PROMPT_ROTEADOR}]
    if historico:
        # Janela dos últimos 6 turnos para não estourar contexto na PoC.
        messages.extend(historico[-6:])
    messages.append({"role": "user", "content": mensagem_usuario})

    resposta = chat(
        messages=messages,
        enable_thinking=False,
        temperature=0.1,
        response_format={"type": "json_object"},
        backend=backend,  # type: ignore[arg-type]
    )

    # Fail-safe: em caso de JSON quebrado, caímos em duvida_geral
    # (caminho mais conservador).
    try:
        payload = json.loads(resposta["content"])
    except json.JSONDecodeError:
        payload = {
            "intent": "duvida_geral",
            "confianca": 0.0,
            "justificativa": (
                "Falha ao parsear JSON do roteador; assumindo dúvida geral por segurança."
            ),
        }

    intents_validas = {
        "checkup",
        "triagem_sintoma",
        "prescricao",
        "duvida_geral",
        "fora_escopo",
    }
    if payload.get("intent") not in intents_validas:
        payload["intent"] = "duvida_geral"

    return payload
