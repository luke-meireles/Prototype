"""Orquestração multi-agente do BluaDiagnostics via LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.checkup import executar_checkup
from src.agents.prescricao import executar_prescricao
from src.agents.router import classificar_intent
from src.agents.safety import auditar_resposta
from src.agents.triagem import executar_triagem
from src.audit_log import AuditLog


class EstadoBlua(TypedDict, total=False):
    """Estado compartilhado entre os nós do grafo.

    Cada nó lê o que precisa e escreve sua contribuição. Tudo é serializável
    para o ``MemorySaver``, que permite continuação de sessão multi-turno.
    """

    mensagens: list[dict[str, Any]]
    beneficiario_id: str | None
    intent_classificada: str | None
    agente_ativo: str | None
    dossie_queixas: dict[str, Any]
    classificacao_risco: dict[str, Any] | None
    rag_chunks: list[dict[str, Any]]
    tools_invocadas: list[dict[str, Any]]
    safety_aprovado: bool
    safety_motivos: list[str]
    resposta_final: str | None
    audit_log: dict[str, Any]
    backend: str  # "dashscope" ou "ollama"
    medicacao_proposta: list[str] | None


# ---------- Nós do grafo ----------


def no_roteador(state: EstadoBlua) -> dict[str, Any]:
    """Classifica a intent da última mensagem do usuário."""
    mensagens = state["mensagens"]
    ultimo_usuario = next(
        (m["content"] for m in reversed(mensagens) if m.get("role") == "user"),
        "",
    )
    backend = state.get("backend", "dashscope")
    classificacao = classificar_intent(
        mensagem_usuario=ultimo_usuario,
        historico=[m for m in mensagens if m.get("role") != "system"],
        backend=backend,
    )
    return {
        "intent_classificada": classificacao["intent"],
        "agente_ativo": "roteador",
    }


def no_checkup(state: EstadoBlua) -> dict[str, Any]:
    backend = state.get("backend", "dashscope")
    saida = executar_checkup(
        mensagens=state["mensagens"],
        beneficiario_id=state.get("beneficiario_id"),
        backend=backend,
    )
    return {
        "agente_ativo": "checkup",
        "resposta_final": saida["content"],
        "tools_invocadas": (state.get("tools_invocadas") or []) + saida["tool_calls"],
    }


def no_triagem(state: EstadoBlua) -> dict[str, Any]:
    backend = state.get("backend", "dashscope")
    saida = executar_triagem(
        mensagens=state["mensagens"],
        dossie_queixas=state.get("dossie_queixas") or {},
        beneficiario_id=state.get("beneficiario_id"),
        backend=backend,
    )

    classificacao = None
    for tc in saida["tool_calls"]:
        if tc["nome"] == "classificar_risco_clinico":
            classificacao = tc["output"]
            break

    return {
        "agente_ativo": "triagem",
        "resposta_final": saida["content"],
        "rag_chunks": saida["rag_chunks"],
        "tools_invocadas": (state.get("tools_invocadas") or []) + saida["tool_calls"],
        "classificacao_risco": classificacao,
    }


def no_prescricao(state: EstadoBlua) -> dict[str, Any]:
    backend = state.get("backend", "dashscope")
    beneficiario_id = state.get("beneficiario_id") or "BENEF-DESCONHECIDO"
    saida = executar_prescricao(
        mensagens=state["mensagens"],
        beneficiario_id=beneficiario_id,
        medicacao_proposta=state.get("medicacao_proposta"),
        backend=backend,
    )
    return {
        "agente_ativo": "prescricao",
        "resposta_final": saida["content"],
        "rag_chunks": saida["rag_chunks"],
        "tools_invocadas": (state.get("tools_invocadas") or []) + saida["tool_calls"],
    }


def no_duvida_geral(state: EstadoBlua) -> dict[str, Any]:
    """Atalho leve para perguntas educacionais sem necessidade de triagem."""
    from src.llm.qwen_client import chat
    from pathlib import Path

    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.md"
    system = prompt_path.read_text(encoding="utf-8")
    backend = state.get("backend", "dashscope")
    resposta = chat(
        messages=[{"role": "system", "content": system}] + state["mensagens"],
        enable_thinking=False,
        temperature=0.4,
        backend=backend,  # type: ignore[arg-type]
    )
    return {
        "agente_ativo": "duvida_geral",
        "resposta_final": resposta["content"],
    }


def no_fora_escopo(state: EstadoBlua) -> dict[str, Any]:
    """Resposta padrão para pedidos fora do escopo clínico."""
    mensagem = (
        "Sou o assistente clínico digital da Care Plus e meu papel é apoiar "
        "questões de saúde — triagem de sintomas, dúvidas sobre medicação "
        "(de forma educacional), agendamento de teleconsulta e orientação "
        "preventiva. Esse pedido sai do meu escopo, então preciso te "
        "redirecionar. Posso ajudar com algo relacionado à sua saúde?"
    )
    return {
        "agente_ativo": "fora_escopo",
        "resposta_final": mensagem,
    }


def no_safety(state: EstadoBlua) -> dict[str, Any]:
    """Auditoria final antes da resposta sair."""
    backend = state.get("backend", "dashscope")
    mensagens = state["mensagens"]
    ultimo_usuario = next(
        (m["content"] for m in reversed(mensagens) if m.get("role") == "user"),
        "",
    )
    classificacao = state.get("classificacao_risco") or {}
    red_flag = bool(classificacao.get("red_flag_detectada"))

    auditoria = auditar_resposta(
        pergunta_usuario=ultimo_usuario,
        resposta_candidata=state.get("resposta_final") or "",
        intent_classificada=state.get("intent_classificada") or "desconhecida",
        red_flag_detectada=red_flag,
        agente_origem=state.get("agente_ativo"),
        backend=backend,
    )

    aprovado = bool(auditoria["aprovado"])
    motivos = auditoria.get("motivos_reprovacao", [])

    # Se reprovado, anexamos uma nota — o regenerador é a próxima passagem
    # do grafo na PoC. Aqui simplificamos: marcamos a reprovação no estado.
    return {
        "safety_aprovado": aprovado,
        "safety_motivos": motivos,
    }


def no_audit(state: EstadoBlua) -> dict[str, Any]:
    """Persiste o audit log estruturado e finaliza o turno."""
    log = AuditLog(beneficiario_id=state.get("beneficiario_id"))
    mensagens = state["mensagens"]
    ultimo_usuario = next(
        (m["content"] for m in reversed(mensagens) if m.get("role") == "user"),
        "",
    )
    log.set_input(ultimo_usuario)
    log.set_intent(state.get("intent_classificada") or "desconhecida")
    log.set_agente(state.get("agente_ativo") or "desconhecido")
    for chunk in state.get("rag_chunks") or []:
        log.add_rag_chunk(chunk.get("fonte", ""), chunk.get("score", 0.0))
    for tc in state.get("tools_invocadas") or []:
        log.add_tool_call(tc["nome"], tc.get("input", {}), tc.get("output", {}))
    if state.get("classificacao_risco"):
        log.set_classificacao_risco(state["classificacao_risco"])
    log.set_thinking(state.get("agente_ativo") in {"triagem", "prescricao"})
    log.set_safety(
        passou=bool(state.get("safety_aprovado", True)),
        motivo="; ".join(state.get("safety_motivos") or []) or None,
    )
    log.set_resposta(state.get("resposta_final") or "")
    log.finalizar()

    return {"audit_log": log.payload}


# ---------- Routing condicional ----------


def _rotear_intent(state: EstadoBlua) -> str:
    intent = state.get("intent_classificada")
    if intent == "checkup":
        return "checkup"
    if intent == "triagem_sintoma":
        return "triagem"
    if intent == "prescricao":
        return "prescricao"
    if intent == "fora_escopo":
        return "fora_escopo"
    return "duvida_geral"


# ---------- Construção do grafo ----------


def construir_grafo() -> Any:
    """Compõe o ``StateGraph`` com os 5 nós principais + audit + memória."""
    grafo = StateGraph(EstadoBlua)

    grafo.add_node("roteador", no_roteador)
    grafo.add_node("checkup", no_checkup)
    grafo.add_node("triagem", no_triagem)
    grafo.add_node("prescricao", no_prescricao)
    grafo.add_node("duvida_geral", no_duvida_geral)
    grafo.add_node("fora_escopo", no_fora_escopo)
    grafo.add_node("safety", no_safety)
    grafo.add_node("audit", no_audit)

    grafo.set_entry_point("roteador")
    grafo.add_conditional_edges(
        "roteador",
        _rotear_intent,
        {
            "checkup": "checkup",
            "triagem": "triagem",
            "prescricao": "prescricao",
            "duvida_geral": "duvida_geral",
            "fora_escopo": "fora_escopo",
        },
    )

    for no_resposta in ("checkup", "triagem", "prescricao", "duvida_geral", "fora_escopo"):
        grafo.add_edge(no_resposta, "safety")

    grafo.add_edge("safety", "audit")
    grafo.add_edge("audit", END)

    # Checkpoint em memória — habilita continuação multi-turno por thread_id
    return grafo.compile(checkpointer=MemorySaver())


def executar_turno(
    grafo: Any,
    mensagem_usuario: str,
    thread_id: str,
    beneficiario_id: str | None = None,
    backend: str = "dashscope",
    historico: list[dict[str, Any]] | None = None,
    medicacao_proposta: list[str] | None = None,
) -> dict[str, Any]:
    """Helper que envia um turno do usuário ao grafo e retorna o estado final."""
    historico = historico or []
    historico.append({"role": "user", "content": mensagem_usuario})

    estado_inicial: EstadoBlua = {
        "mensagens": historico,
        "beneficiario_id": beneficiario_id,
        "intent_classificada": None,
        "agente_ativo": None,
        "dossie_queixas": {},
        "classificacao_risco": None,
        "rag_chunks": [],
        "tools_invocadas": [],
        "safety_aprovado": True,
        "safety_motivos": [],
        "resposta_final": None,
        "audit_log": {},
        "backend": backend,
        "medicacao_proposta": medicacao_proposta,
    }

    config = {"configurable": {"thread_id": thread_id}}
    return grafo.invoke(estado_inicial, config=config)
