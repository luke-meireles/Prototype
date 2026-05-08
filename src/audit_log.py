"""Audit log estruturado em JSON — base de auditoria LGPD do BluaDiagnostics."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

# Pasta de logs (gitignored)
_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _configurar_structlog() -> None:
    """Configura structlog para emitir JSON na stdlib logger."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


_configurar_structlog()
_logger = structlog.get_logger("bluadiagnostics.audit")


class AuditLog:
    """Acumula e persiste o registro de uma sessão BluaDiagnostics."""

    def __init__(self, beneficiario_id: str | None = None) -> None:
        self.session_id = str(uuid.uuid4())
        self.beneficiario_id = beneficiario_id
        self._inicio = time.time()

        self.payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "beneficiario_id": beneficiario_id,
            "agente_ativo": None,
            "input_usuario": None,
            "intent_classificada": None,
            "rag_chunks_recuperados": [],
            "tools_invocadas": [],
            "classificacao_risco": {},
            "thinking_mode_usado": False,
            "safety_layer_passou": True,
            "safety_layer_motivo": None,
            "resposta_final": None,
            "tempo_total_ms": 0,
        }

    # --- API encadeável usada pelos nós do grafo ---
    def set_input(self, texto: str) -> "AuditLog":
        self.payload["input_usuario"] = texto
        return self

    def set_intent(self, intent: str) -> "AuditLog":
        self.payload["intent_classificada"] = intent
        return self

    def set_agente(self, nome: str) -> "AuditLog":
        self.payload["agente_ativo"] = nome
        return self

    def add_rag_chunk(self, fonte: str, score: float) -> "AuditLog":
        self.payload["rag_chunks_recuperados"].append({"fonte": fonte, "score": score})
        return self

    def add_tool_call(self, nome: str, entrada: dict, saida: dict) -> "AuditLog":
        self.payload["tools_invocadas"].append(
            {"nome": nome, "input": entrada, "output": saida}
        )
        return self

    def set_classificacao_risco(self, classificacao: dict) -> "AuditLog":
        self.payload["classificacao_risco"] = classificacao
        return self

    def set_thinking(self, usado: bool) -> "AuditLog":
        self.payload["thinking_mode_usado"] = usado
        return self

    def set_safety(self, passou: bool, motivo: str | None = None) -> "AuditLog":
        self.payload["safety_layer_passou"] = passou
        self.payload["safety_layer_motivo"] = motivo
        return self

    def set_resposta(self, texto: str) -> "AuditLog":
        self.payload["resposta_final"] = texto
        return self

    # --- persistência ---
    def finalizar(self) -> dict[str, Any]:
        self.payload["tempo_total_ms"] = int((time.time() - self._inicio) * 1000)
        arquivo = _LOG_DIR / f"session_{self.session_id}.json"
        with arquivo.open("w", encoding="utf-8") as fp:
            json.dump(self.payload, fp, ensure_ascii=False, indent=2)
        # Replica em log estruturado para coleta por agregador (ELK, Datadog, etc.)
        _logger.info("audit_log_finalizado", **self.payload)
        return self.payload

    def caminho_arquivo(self) -> Path:
        return _LOG_DIR / f"session_{self.session_id}.json"
