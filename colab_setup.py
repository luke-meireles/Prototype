"""Bootstrap do BluaDiagnostics para Google Colab.

Uma chamada a ``preparar_ambiente()`` cuida de tudo: localiza/clona a
raiz, ajusta `sys.path`, carrega `DASHSCOPE_API_KEY` (env → Colab Secrets
→ .env), fixa o modelo Qwen e cria `logs/` e `chroma_db/`. Idempotente.

Uso na primeira célula do notebook:

    >>> from colab_setup import preparar_ambiente
    >>> preparar_ambiente()
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Modelos fixados — o projeto inteiro espera a família Qwen.
_MODELO_DASHSCOPE = "qwen-plus"
_MODELO_OLLAMA = "qwen:9b"

_REPO_URL_PADRAO = "https://github.com/luke-meireles/bluadiagnostics.git"


def em_colab() -> bool:
    """True se rodando no Google Colab."""
    try:
        import google.colab  # type: ignore # noqa: F401
        return True
    except ImportError:
        return False


def _localizar_raiz(repo_url: str | None = None) -> Path:
    """Encontra (ou clona) a raiz do projeto.

    Ordem: pasta do próprio arquivo → CWD e ancestrais → `/content/bluadiagnostics`
    no Colab (clonando se `repo_url` foi fornecido).
    """
    aqui = Path(__file__).resolve().parent
    if (aqui / "src" / "graph.py").exists():
        return aqui

    cwd = Path.cwd()
    for candidato in [cwd, *cwd.parents]:
        if (candidato / "src" / "graph.py").exists():
            return candidato

    if em_colab():
        destino = Path("/content/bluadiagnostics")
        if (destino / "src" / "graph.py").exists():
            return destino
        if repo_url:
            import subprocess
            print(f"[colab_setup] Clonando {repo_url} em {destino}...")
            subprocess.run(
                ["git", "clone", repo_url, str(destino)],
                check=True,
            )
            return destino

    raise FileNotFoundError(
        "Não consegui localizar a raiz do projeto bluadiagnostics. "
        "No Colab, faça upload manual ou passe repo_url= explícito."
    )


def _carregar_chave_dashscope() -> str | None:
    """Resolve DASHSCOPE_API_KEY: env → Colab Secrets → .env."""
    chave = os.getenv("DASHSCOPE_API_KEY")
    if chave:
        return chave

    if em_colab():
        try:
            from google.colab import userdata  # type: ignore
            chave = userdata.get("DASHSCOPE_API_KEY")
            if chave:
                os.environ["DASHSCOPE_API_KEY"] = chave
                return chave
        except Exception as exc:
            print(f"[colab_setup] Aviso: Colab Secrets indisponível ({exc}).")

    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(override=False)
        return os.getenv("DASHSCOPE_API_KEY")
    except ImportError:
        return None


def preparar_ambiente(
    repo_url: str | None = None,
    exigir_chave: bool = True,
    forcar_modelo: bool = True,
) -> dict[str, Any]:
    """Configura o ambiente do BluaDiagnostics de forma idempotente.

    Args:
        repo_url: URL do repositório a clonar caso o projeto não esteja
            presente no Colab. Se None, assume upload manual.
        exigir_chave: levanta `RuntimeError` quando a chave não é
            resolvida (default True, falha cedo em vez de erro confuso
            no LLM depois).
        forcar_modelo: sobrescreve `QWEN_DASHSCOPE_MODEL` e
            `QWEN_OLLAMA_MODEL` com os valores fixados.

    Returns:
        Diagnóstico do ambiente: raiz, chave_carregada, modo, versão do
        Python, etc.
    """
    raiz = _localizar_raiz(repo_url)

    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    os.chdir(raiz)

    chave = _carregar_chave_dashscope()
    if exigir_chave and not chave:
        raise RuntimeError(
            "DASHSCOPE_API_KEY não encontrada. No Colab, adicione-a em "
            "Secrets (ícone de chave 🔑 na barra lateral) com o nome "
            "DASHSCOPE_API_KEY e habilite 'Notebook access'."
        )

    if forcar_modelo:
        os.environ["QWEN_DASHSCOPE_MODEL"] = _MODELO_DASHSCOPE
        os.environ.setdefault("QWEN_OLLAMA_MODEL", _MODELO_OLLAMA)

    (raiz / "logs").mkdir(parents=True, exist_ok=True)
    chroma_dir = Path(os.getenv("CHROMA_PERSIST_DIR", str(raiz / "chroma_db")))
    chroma_dir.mkdir(parents=True, exist_ok=True)

    diagnostico = {
        "modo": "colab" if em_colab() else "local",
        "raiz_projeto": str(raiz),
        "chave_carregada": bool(chave),
        "modelo_dashscope": os.environ.get("QWEN_DASHSCOPE_MODEL"),
        "modelo_ollama": os.environ.get("QWEN_OLLAMA_MODEL"),
        "python_version": sys.version.split()[0],
        "chroma_dir": str(chroma_dir),
    }

    print("[colab_setup] Ambiente preparado:")
    for k, v in diagnostico.items():
        print(f"  - {k}: {v}")

    return diagnostico


__all__ = ["preparar_ambiente", "em_colab"]
