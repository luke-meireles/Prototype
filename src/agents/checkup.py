"""Agente Check-up — coleta estruturada de sintomas e sinais vitais."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.llm.qwen_client import chat
from src.tools import TOOL_REGISTRY

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _carregar_prompts() -> str:
    """Compõe o system prompt: principal + sub-prompt do agente."""
    principal = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    sub = (_PROMPTS_DIR / "agente_checkup.md").read_text(encoding="utf-8")
    return f"{principal}\n\n---\n\n{sub}"


def _tools_spec_para_qwen() -> list[dict[str, Any]]:
    """Filtra do tools_spec.json apenas as tools que este agente pode chamar."""
    import json
    spec_path = Path(__file__).resolve().parents[2] / "tools" / "tools_spec.json"
    todas = json.loads(spec_path.read_text(encoding="utf-8"))
    nomes_permitidos = {"consultar_historico_paciente", "consultar_sinais_vitais_wearable"}
    return [t for t in todas if t["function"]["name"] in nomes_permitidos]


def executar_checkup(
    mensagens: list[dict[str, Any]],
    beneficiario_id: str | None = None,
    backend: str = "dashscope",
) -> dict[str, Any]:
    """Executa um turno do agente de Check-up.

    Args:
        mensagens: histórico do usuário no formato OpenAI ({role, content}).
        beneficiario_id: se conhecido, é injetado como contexto.
        backend: ``"dashscope"`` ou ``"ollama"``.

    Returns:
        Dict com ``content`` (mensagem ao paciente), ``tool_calls`` (lista
        de tool calls executadas com input/output), ``thinking`` (sempre None
        neste agente — thinking desligado).
    """
    system = _carregar_prompts()
    if beneficiario_id:
        system += f"\n\n## Contexto da sessão\n- beneficiario_id: {beneficiario_id}"

    payload_msgs: list[dict[str, Any]] = [{"role": "system", "content": system}]
    payload_msgs.extend(mensagens)

    resposta = chat(
        messages=payload_msgs,
        tools=_tools_spec_para_qwen(),
        enable_thinking=False,
        temperature=0.4,
        backend=backend,  # type: ignore[arg-type]
    )

    # Executa tool calls que o modelo solicitou e devolve resultados
    tool_outputs: list[dict[str, Any]] = []
    for tc in resposta["tool_calls"]:
        nome = tc["name"]
        if nome not in TOOL_REGISTRY:
            continue
        import json
        try:
            args = json.loads(tc["arguments"])
        except json.JSONDecodeError:
            args = {}
        saida = TOOL_REGISTRY[nome](**args)
        tool_outputs.append({"nome": nome, "input": args, "output": saida})

    return {
        "content": resposta["content"],
        "tool_calls": tool_outputs,
        "thinking": resposta["thinking"],
    }
