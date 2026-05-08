"""Safety Layer — auditor automático que aprova ou reprova respostas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.llm.qwen_client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _carregar_prompts() -> str:
    principal = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    sub = (_PROMPTS_DIR / "agente_safety.md").read_text(encoding="utf-8")
    return f"{principal}\n\n---\n\n{sub}"


def auditar_resposta(
    pergunta_usuario: str,
    resposta_candidata: str,
    intent_classificada: str,
    red_flag_detectada: bool = False,
    agente_origem: str | None = None,
    backend: str = "dashscope",
) -> dict[str, Any]:
    """Audita uma resposta candidata contra os critérios de segurança.

    Returns:
        Dict com ``aprovado: bool``, ``motivos_reprovacao: list``,
        ``criterios_atendidos: list``, ``sugestao_correcao: str | None``.
    """
    system = _carregar_prompts()

    user_prompt = (
        "Audite a resposta a seguir contra os critérios.\n\n"
        f"intent_classificada: {intent_classificada}\n"
        f"red_flag_detectada: {red_flag_detectada}\n"
        f"agente_origem: {agente_origem or 'desconhecido'}\n\n"
        f"## Pergunta do usuário\n{pergunta_usuario}\n\n"
        f"## Resposta candidata\n{resposta_candidata}\n\n"
        "Devolva APENAS o JSON conforme o esquema do prompt."
    )

    resposta = chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        enable_thinking=False,
        temperature=0.0,
        response_format={"type": "json_object"},
        backend=backend,  # type: ignore[arg-type]
    )

    try:
        parsed = json.loads(resposta["content"])
    except json.JSONDecodeError:
        # Em caso de erro de parsing, reprovamos por segurança
        parsed = {
            "aprovado": False,
            "motivos_reprovacao": ["Falha ao parsear resposta do Safety Layer."],
            "criterios_atendidos": [],
            "sugestao_correcao": "Reescrever a resposta em PT-BR claro com disclaimer.",
        }

    # Valida shape mínimo
    parsed.setdefault("aprovado", False)
    parsed.setdefault("motivos_reprovacao", [])
    parsed.setdefault("criterios_atendidos", [])
    parsed.setdefault("sugestao_correcao", None)

    return parsed
