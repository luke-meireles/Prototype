"""Camada LLM — wrappers Qwen via DashScope (cloud) e Ollama (on-prem).

Toda chamada a LLM no projeto passa por aqui. Manter UMA fachada
(função ``chat`` / classes ``*Client``) facilita:

- Trocar de backend sem mexer no resto do código (dashscope ↔ ollama).
- Centralizar logging, retry, rate limit etc. quando precisarmos.
- Manipular o bloco <think> em um lugar só (regra inegociável: nunca
  expor para o usuário).

No Colab, use sempre ``backend="dashscope"`` — o ``OllamaClient`` está
aqui apenas para uso fora do Colab.
"""

from src.llm.qwen_client import QwenClient, chat
from src.llm.ollama_client import OllamaClient

__all__ = ["QwenClient", "OllamaClient", "chat"]
