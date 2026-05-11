"""Wrapper unificado para Qwen — backends DashScope e Ollama via OpenAI SDK.

DashScope e Ollama expõem endpoint OpenAI-compatible, então o mesmo SDK
serve para os dois. A `DASHSCOPE_API_KEY` é resolvida na ordem
os.environ → Colab Secrets → .env. A resolução acontece dentro de
`_build_client`, então importar este módulo não dispara leitura de
secrets.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

from openai import OpenAI

# Endpoints OpenAI-compatible
_DASHSCOPE_BASE = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
_OLLAMA_BASE_DEFAULT = "http://localhost:11434/v1"


def _carregar_chave_dashscope() -> str | None:
    """Resolve DASHSCOPE_API_KEY: os.environ → Colab Secrets → .env."""
    chave = os.getenv("DASHSCOPE_API_KEY")
    if chave:
        return chave

    try:
        from google.colab import userdata  # type: ignore

        chave = userdata.get("DASHSCOPE_API_KEY")
        if chave:
            os.environ["DASHSCOPE_API_KEY"] = chave
            return chave
    except Exception:
        pass

    try:
        from dotenv import load_dotenv  # type: ignore

        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
            return os.getenv("DASHSCOPE_API_KEY")
    except ImportError:
        pass

    return None


def _modelo_padrao(backend: str) -> str:
    """Lê o modelo no momento da chamada (não no import).

    Necessário porque `colab_setup.preparar_ambiente()` pode rodar
    depois do primeiro `import` deste módulo.
    """
    if backend == "dashscope":
        return os.getenv("QWEN_DASHSCOPE_MODEL", "qwen-plus")
    return os.getenv("QWEN_OLLAMA_MODEL", "qwen:9b")


# Regex para isolar o bloco <think>...</think> e o conteúdo limpo
_THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def _build_client(backend: Literal["dashscope", "ollama"]) -> OpenAI:
    """Constrói o client OpenAI-compatible apontando para o backend correto."""
    if backend == "dashscope":
        api_key = _carregar_chave_dashscope()
        if not api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY não configurada. No Colab, adicione-a em "
                "Secrets (ícone 🔑) com Notebook access habilitado. Em ambiente "
                "local, defina via shell ou crie um arquivo .env na raiz."
            )
        return OpenAI(api_key=api_key, base_url=_DASHSCOPE_BASE)

    if backend == "ollama":
        # api_key é placeholder — Ollama aceita qualquer string não vazia.
        base_url = os.getenv("OLLAMA_BASE_URL", _OLLAMA_BASE_DEFAULT)
        return OpenAI(api_key="ollama-local", base_url=base_url)

    raise ValueError(f"Backend desconhecido: {backend}")


def _separar_thinking(content: str | None) -> tuple[str, str | None]:
    """Extrai o bloco <think> e devolve (conteúdo_limpo, thinking_ou_None).

    O conteúdo do <think> nunca deve ser exposto ao usuário.
    """
    if not content:
        return "", None

    match = _THINK_PATTERN.search(content)
    if not match:
        return content.strip(), None

    thinking = match.group(1).strip()
    visivel = _THINK_PATTERN.sub("", content).strip()
    return visivel, thinking


def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    enable_thinking: bool = False,
    temperature: float = 0.3,
    response_format: dict[str, Any] | None = None,
    backend: Literal["dashscope", "ollama"] = "dashscope",
    model: str | None = None,
) -> dict[str, Any]:
    """Interface única usada por todos os agentes do BluaDiagnostics.

    Args:
        messages: histórico no formato OpenAI ({role, content}).
        tools: lista de tool specs no padrão OpenAI tools (opcional).
        enable_thinking: ativa hybrid thinking mode do Qwen.
        temperature: temperatura de amostragem.
        response_format: pode ser ``{"type": "json_object"}`` para saída JSON.
        backend: ``"dashscope"`` (cloud, padrão no Colab) ou ``"ollama"``.
        model: força um modelo específico — caso contrário usa default do backend.

    Returns:
        Dicionário com chaves ``content`` (texto limpo, sem <think>),
        ``thinking`` (conteúdo do bloco <think> ou None), ``tool_calls`` (lista
        de chamadas de função, se houver) e ``raw`` (resposta crua do SDK).
    """
    client = _build_client(backend)
    chosen_model = model or _modelo_padrao(backend)

    kwargs: dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
        # `enable_thinking` é específico do Qwen; passamos via extra_body
        # porque não faz parte da API OpenAI padrão.
        "extra_body": {"enable_thinking": enable_thinking},
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if response_format:
        kwargs["response_format"] = response_format

    raw = client.chat.completions.create(**kwargs)
    msg = raw.choices[0].message

    content_clean, thinking = _separar_thinking(msg.content)

    tool_calls: list[dict[str, Any]] = []
    if getattr(msg, "tool_calls", None):
        for tc in msg.tool_calls:
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            )

    return {
        "content": content_clean,
        "thinking": thinking,
        "tool_calls": tool_calls,
        "raw": raw.model_dump() if hasattr(raw, "model_dump") else raw,
    }


class QwenClient:
    """Versão OO da `chat`, útil para fixar o backend uma vez."""

    def __init__(self, backend: Literal["dashscope", "ollama"] = "dashscope") -> None:
        self.backend = backend

    def chat(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("backend", self.backend)
        return chat(**kwargs)
