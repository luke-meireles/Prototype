"""Agente Prescrição — apoio ao médico, sempre como rascunho.

ATENÇÃO REGULATÓRIA: pela Resolução CFM 2.314/22, prescrição médica no
Brasil exige assinatura por profissional habilitado (ICP-Brasil). O
BluaDiagnostics nunca emite prescrição final — toda saída começa com a
tag `[RASCUNHO_AGUARDANDO_REVISAO_MEDICA]`.

Atende o caminho secundário (persona médica). Entrada esperada: o
médico descreve hipótese diagnóstica e medicação considerada. Thinking
ON porque verificar interações e dose por idade/peso/comorbidade
exige raciocínio.
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

# Tag obrigatória — em maiúsculas para facilitar string match em auditoria.
_TAG_RASCUNHO = "[RASCUNHO_AGUARDANDO_REVISAO_MEDICA]"


def _carregar_prompts() -> str:
    principal = (_PROMPTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    sub = (_PROMPTS_DIR / "agente_prescricao.md").read_text(encoding="utf-8")
    return f"{principal}\n\n---\n\n{sub}"


def _tools_filtradas() -> list[dict[str, Any]]:
    todas = json.loads(_TOOLS_PATH.read_text(encoding="utf-8"))
    permitidas = {
        "consultar_historico_paciente",
        "verificar_interacoes_medicamentosas",
    }
    return [t for t in todas if t["function"]["name"] in permitidas]


def _formatar_chunks(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"### {c.get('fonte')} (tipo={c.get('tipo')})\n{c.get('documento')}"
        for c in chunks
    ) or "(sem contexto)"


def executar_prescricao(
    mensagens: list[dict[str, Any]],
    beneficiario_id: str,
    medicacao_proposta: list[str] | None = None,
    backend: str = "dashscope",
) -> dict[str, Any]:
    """Gera rascunho de prescrição assistida.

    A entrada esperada é uma mensagem do médico contendo a hipótese
    diagnóstica e a medicação considerada. Toda saída começa com a tag
    `[RASCUNHO_AGUARDANDO_REVISAO_MEDICA]`.
    """
    system = _carregar_prompts()
    system += f"\n\n## Contexto da sessão\n- beneficiario_id: {beneficiario_id}"
    if medicacao_proposta:
        system += f"\n- medicação proposta pelo médico: {medicacao_proposta}"

    query_rag = " ".join(medicacao_proposta) if medicacao_proposta else "prescrição"
    chunks = recuperar_chunks(
        query=query_rag,
        top_k=3,
        filtro_tipo=["bula", "politica"],
    )
    system += "\n\n## Contexto RAG\n" + _formatar_chunks(chunks)

    payload_msgs: list[dict[str, Any]] = [{"role": "system", "content": system}]
    payload_msgs.extend(mensagens)

    resposta = chat(
        messages=payload_msgs,
        tools=_tools_filtradas(),
        enable_thinking=True,
        temperature=0.2,
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

    # Defense in depth: a tag é pedida no prompt, mas reforçada aqui no
    # código caso o modelo a omita.
    content = resposta["content"]
    if _TAG_RASCUNHO not in content:
        content = f"{_TAG_RASCUNHO}\n\n{content}"

    return {
        "content": content,
        "tool_calls": tool_outputs,
        "thinking": resposta["thinking"],
        "rag_chunks": chunks,
    }
