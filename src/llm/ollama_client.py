"""Cliente Ollama — invólucro fino sobre QwenClient para a Configuração B (on-prem)."""

from __future__ import annotations

from typing import Any

from src.llm.qwen_client import QwenClient


class OllamaClient(QwenClient):
    """Mesmo contrato do QwenClient, mas fixa backend Ollama por padrão.

    Essa classe existe para deixar explícito, no código consumidor, que se
    está usando o modo on-prem — útil para auditoria de segurança/LGPD."""

    def __init__(self) -> None:
        super().__init__(backend="ollama")

    def chat(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["backend"] = "ollama"
        return super().chat(**kwargs)
