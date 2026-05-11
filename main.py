"""CLI mínima do BluaDiagnostics — execução pontual fora do notebook.

A forma canônica de rodar o projeto é o notebook
`notebooks/sprint1_poc.ipynb`. Este script existe para chamadas rápidas
via `!python main.py ...` numa célula do Colab ou em shell local.

Uso:
    !python main.py --smoke                       # ping no LLM
    !python main.py --once "tenho dor lombar"     # 1 turno e sai
    !python main.py --beneficiario BENEF-001      # modo interativo (local)

O bootstrap (paths, secrets, modelo) é delegado ao `colab_setup`,
funcionando igual em ambos ambientes.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# Permite `import src.*` sem `pip install -e .`.
_RAIZ = Path(__file__).resolve().parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

# Mesmo bootstrap usado pelo notebook. `exigir_chave=False` evita quebrar
# `--help` quando a chave ainda não foi configurada.
try:
    from colab_setup import preparar_ambiente

    preparar_ambiente(exigir_chave=False)
except Exception as exc:
    print(f"[main] Aviso de bootstrap: {exc}")


def _smoke_test(backend: str) -> int:
    """Faz uma única chamada ao LLM para validar conectividade e quota."""
    from src.llm.qwen_client import chat

    print(f"[smoke] Backend={backend}")
    print(
        "[smoke] Modelo="
        f"{os.getenv('QWEN_DASHSCOPE_MODEL') if backend == 'dashscope' else os.getenv('QWEN_OLLAMA_MODEL')}"
    )
    print("[smoke] Enviando ping ao modelo...")

    try:
        resposta = chat(
            messages=[
                {"role": "system", "content": "Responda em uma frase, em português brasileiro."},
                {"role": "user", "content": "Olá! Você está funcionando?"},
            ],
            enable_thinking=False,
            temperature=0.2,
            backend=backend,  # type: ignore[arg-type]
        )
        print(f"[smoke] OK — resposta: {resposta['content']!r}")
        return 0
    except Exception as exc:  # pragma: no cover — depende de credencial real
        print(f"[smoke] FALHOU: {type(exc).__name__}: {exc}")
        _imprimir_dicas(backend, exc)
        return 1


def _imprimir_dicas(backend: str, exc: Exception) -> None:
    """Sugere correções comuns conforme a exceção observada."""
    msg = str(exc).lower()
    print("\n[dica] Possíveis causas:")

    if backend == "dashscope":
        if "401" in msg or "unauthor" in msg:
            print("  - DASHSCOPE_API_KEY inválida ou expirada. Gere uma nova no Bailian Console.")
        elif "403" in msg or "accessdenied" in msg or "unpurchased" in msg:
            print("  - Sua conta DashScope International ainda não ativou o Model Studio.")
            print("    1. Acesse https://bailian.console.alibabacloud.com/")
            print("    2. Clique em 'Activate Model Studio' / 'Free Trial'")
            print("    3. Após ativar, ganha-se 1 milhão de tokens grátis nos primeiros 90 dias.")
        elif "quota" in msg or "rate" in msg:
            print("  - Limite de quota/RPM atingido. Aguarde alguns segundos.")
        else:
            print("  - Verifique se o secret DASHSCOPE_API_KEY está habilitado no Colab.")
    elif backend == "ollama":
        print("  - Ollama não está disponível por padrão no Colab — use --backend dashscope.")
        if "connection" in msg or "refused" in msg:
            print("  - Em ambiente local, instale em https://ollama.com e rode 'ollama serve'.")


def _modo_interativo(backend: str, beneficiario: str | None) -> int:
    from src.graph import construir_grafo, executar_turno

    print(f"BluaDiagnostics — modo interativo (backend={backend})")
    print("Digite 'sair' para encerrar. (No Colab, use o notebook em vez deste modo.)\n")

    grafo = construir_grafo()
    thread_id = str(uuid.uuid4())
    historico: list[dict] = []

    while True:
        try:
            entrada = input("Você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            return 0
        if not entrada:
            continue
        if entrada.lower() in {"sair", "exit", "quit"}:
            return 0

        try:
            estado = executar_turno(
                grafo=grafo,
                mensagem_usuario=entrada,
                thread_id=thread_id,
                beneficiario_id=beneficiario,
                backend=backend,
                historico=historico,
            )
            resposta = estado.get("resposta_final") or "(sem resposta)"
            historico.append({"role": "assistant", "content": resposta})
            agente = estado.get("agente_ativo")
            intent = estado.get("intent_classificada")
            print(f"\nBlua [{agente} | intent={intent}]\n{resposta}\n")
        except Exception as exc:
            print(f"[erro] {type(exc).__name__}: {exc}")
            _imprimir_dicas(backend, exc)
            return 2


def _modo_unica_pergunta(backend: str, beneficiario: str | None, pergunta: str) -> int:
    from src.graph import construir_grafo, executar_turno

    grafo = construir_grafo()
    estado = executar_turno(
        grafo=grafo,
        mensagem_usuario=pergunta,
        thread_id=str(uuid.uuid4()),
        beneficiario_id=beneficiario,
        backend=backend,
    )
    print(estado.get("resposta_final"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CLI BluaDiagnostics (Colab-friendly)")
    parser.add_argument(
        "--backend",
        choices=["dashscope", "ollama"],
        default=os.getenv("BLUA_BACKEND", "dashscope"),
        help="Backend LLM (default: dashscope — único suportado no Colab)",
    )
    parser.add_argument(
        "--beneficiario",
        default=None,
        help="ID do beneficiário a usar (BENEF-001, BENEF-002, BENEF-003)",
    )
    parser.add_argument(
        "--once",
        default=None,
        help="Executa um único turno com a pergunta dada e sai",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Roda apenas um ping no LLM para verificar credenciais e quota",
    )
    args = parser.parse_args()

    if args.smoke:
        return _smoke_test(args.backend)
    if args.once:
        return _modo_unica_pergunta(args.backend, args.beneficiario, args.once)
    return _modo_interativo(args.backend, args.beneficiario)


if __name__ == "__main__":
    sys.exit(main())
