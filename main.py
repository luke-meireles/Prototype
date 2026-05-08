"""CLI mínima para rodar o BluaDiagnostics localmente.

Uso:
    python main.py                              # modo interativo, backend dashscope
    python main.py --backend ollama             # usa Ollama local
    python main.py --beneficiario BENEF-001     # já injeta um perfil mockado
    python main.py --once "tenho dor lombar"    # roda um único turno e sai
    python main.py --smoke                      # smoke test que faz 1 chamada e sai

Lê automaticamente o .env na raiz do projeto.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# Garante que o .env é carregado antes de qualquer import que use os.getenv
_RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(_RAIZ))

try:
    from dotenv import load_dotenv

    load_dotenv(_RAIZ / ".env", override=False)
except ImportError:
    print("[aviso] python-dotenv não instalado — variáveis precisam estar no shell.")


def _smoke_test(backend: str) -> int:
    """Faz uma única chamada ao LLM para validar conectividade e quota."""
    from src.llm.qwen_client import chat

    print(f"[smoke] Backend={backend}")
    print(f"[smoke] Modelo={os.getenv('QWEN_DASHSCOPE_MODEL') if backend=='dashscope' else os.getenv('QWEN_OLLAMA_MODEL')}")
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
            print("  - DASHSCOPE_API_KEY inválida ou expirada. Gere uma nova no console Bailian.")
        elif "403" in msg or "accessdenied" in msg or "unpurchased" in msg:
            print("  - Sua conta DashScope International ainda não ativou o serviço Model Studio.")
            print("    1. Acesse https://bailian.console.alibabacloud.com/")
            print("    2. Clique em 'Activate Model Studio' / 'Free Trial'")
            print("    3. Após ativar, ganha-se 1 milhão de tokens grátis nos primeiros 90 dias.")
            print("  - Alternativa: rodar com --backend ollama (modo on-prem).")
        elif "quota" in msg or "rate" in msg:
            print("  - Limite de quota/RPM atingido. Aguarde alguns segundos.")
    elif backend == "ollama":
        if "connection" in msg or "refused" in msg:
            print("  - Ollama não está rodando. Instale em https://ollama.com")
            print("  - Em seguida: `ollama pull qwen2.5:7b` e `ollama serve`.")
        elif "model" in msg and "not found" in msg:
            modelo = os.getenv("QWEN_OLLAMA_MODEL", "qwen3.5:9b")
            print(f"  - Modelo '{modelo}' não baixado. Rode: `ollama pull {modelo}`")
            print("  - Ou ajuste QWEN_OLLAMA_MODEL no .env para um modelo já presente.")


def _modo_interativo(backend: str, beneficiario: str | None) -> int:
    from src.graph import construir_grafo, executar_turno

    print(f"BluaDiagnostics — modo interativo (backend={backend})")
    print("Digite 'sair' para encerrar.\n")

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
    parser = argparse.ArgumentParser(description="CLI BluaDiagnostics")
    parser.add_argument(
        "--backend",
        choices=["dashscope", "ollama"],
        default=os.getenv("BLUA_BACKEND", "dashscope"),
        help="Backend LLM (default: dashscope)",
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
