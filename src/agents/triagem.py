"""Agente Triagem — classificação de risco com RAG + tools.

O agente mais crítico do sistema. Recebe a queixa, faz RAG sobre red
flags e protocolo de Manchester, chama tools de classificação de risco
e agendamento, e devolve a recomendação. Thinking ON porque triagem
clínica é exatamente o tipo de tarefa que se beneficia do passo extra
de raciocínio — o bloco <think> fica oculto do usuário.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.llm.qwen_client import chat
from src.rag.retriever import recuperar_chunks
from src.tools import TOOL_REGISTRY

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
_TOOLS_PATH = Path(__file__).resolve().parents[2] / "tools" / "tools_spec.json"


def _carregar_prompts() -> str:
    principal = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    sub = (_PROMPTS_DIR / "agente_triagem.md").read_text(encoding="utf-8")
    return f"{principal}\n\n---\n\n{sub}"


def _tools_filtradas() -> list[dict[str, Any]]:
    todas = json.loads(_TOOLS_PATH.read_text(encoding="utf-8"))
    permitidas = {
        "classificar_risco_clinico",
        "consultar_historico_paciente",
        "agendar_teleconsulta",
    }
    return [t for t in todas if t["function"]["name"] in permitidas]


def _formatar_chunks_rag(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(sem contexto recuperado)"
    linhas = []
    for c in chunks:
        linhas.append(f"### {c.get('fonte')} (tipo={c.get('tipo')}, score={c.get('score')})\n{c.get('documento')}")
    return "\n\n".join(linhas)


def executar_triagem(
    mensagens: list[dict[str, Any]],
    dossie_queixas: dict[str, Any] | None = None,
    beneficiario_id: str | None = None,
    backend: str = "dashscope",
) -> dict[str, Any]:
    """Executa a triagem clínica baseada no dossiê e RAG."""
    system = _carregar_prompts()
    if beneficiario_id:
        system += f"\n\n## Contexto da sessão\n- beneficiario_id: {beneficiario_id}"
    if dossie_queixas:
        system += "\n\n## Dossiê de queixas (do agente Check-up)\n```json\n"
        system += json.dumps(dossie_queixas, ensure_ascii=False, indent=2)
        system += "\n```"

    # Query RAG: última fala do usuário, com fallback para a queixa
    # principal do dossiê coletado pelo Check-up.
    query_rag = ""
    for m in reversed(mensagens):
        if m.get("role") == "user":
            query_rag = m.get("content", "")
            break
    if not query_rag and dossie_queixas:
        query_rag = dossie_queixas.get("queixa_principal", "")

    # Filtro por tipo evita poluir o contexto com bulas/políticas que
    # importam mais ao agente de prescrição.
    chunks = recuperar_chunks(
        query=query_rag,
        top_k=4,
        filtro_tipo=["red_flag", "protocolo", "especialidade"],
    )
    system += "\n\n## Contexto RAG\n" + _formatar_chunks_rag(chunks)

    payload_msgs: list[dict[str, Any]] = [{"role": "system", "content": system}]
    payload_msgs.extend(mensagens)

    resposta = chat(
        messages=payload_msgs,
        tools=_tools_filtradas(),
        enable_thinking=True,
        temperature=0.3,
        backend=backend,  # type: ignore[arg-type]
    )

    tool_outputs: list[dict[str, Any]] = []
    for tc in resposta["tool_calls"]:
        nome = tc["name"]
        if nome not in TOOL_REGISTRY:
            continue
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
        "rag_chunks": chunks,
    }
