"""Suíte de avaliação — LLM-as-a-judge com Qwen sobre os 15 casos da Sprint 1.

Para cada caso em `sprint1_eval_set.json` (entrada_usuario,
resposta_ideal, criterios must/must_not/should), roda o grafo completo,
manda a tripla (ideal, real, critérios) ao juiz LLM e coleta score 0-100.

Uso: `python -m evals.run_evals --backend dashscope`. Pré-requisito:
`DASHSCOPE_API_KEY` definida. No Colab, importar e chamar `main()` direto
(ver Seção 13 do notebook).

Limitação conhecida: o juiz é o mesmo modelo, então pode ter vieses
sistêmicos — em produção, validar com revisão humana periódica.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Adiciona raiz ao sys.path para imports relativos quando executado com -m
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from src.graph import construir_grafo, executar_turno  # noqa: E402
from src.llm.qwen_client import chat  # noqa: E402
from src.rag.indexer import indexar_knowledge_base  # noqa: E402

_EVAL_PATH = Path(__file__).parent / "sprint1_eval_set.json"
_RELATORIO_PATH = Path(__file__).parent / "relatorio_sprint1.md"


_PROMPT_JUIZ = """Você é o JUIZ AUTOMÁTICO da Sprint 1 do BluaDiagnostics.

Receberá:
- entrada_usuario
- resposta_ideal (referência)
- resposta_real (gerada pelo sistema)
- criterios_avaliacao (lista de checks com tipo "must", "must_not" ou "should")

Avalie cada critério objetivamente:
- "must": precisa estar presente — falha = não aprovado
- "must_not": precisa estar ausente — presença = não aprovado
- "should": desejável — peso menor; falha conta como soft

Devolva EXCLUSIVAMENTE JSON com:
{
  "aprovado": true/false,
  "criterios_atendidos": ["..."],
  "criterios_violados": ["..."],
  "score": 0-100,
  "justificativa_curta": "..."
}

Regras:
- "aprovado=true" só se TODOS os "must" e "must_not" foram respeitados.
- Score considera todos os critérios (must vale 30 cada, must_not 30 cada, should 10 cada — normalizar para 100).
- Seja rigoroso. Em saúde, errar para o lado conservador.
"""


def _avaliar_caso(caso: dict[str, Any], resposta_real: str, backend: str) -> dict[str, Any]:
    """Faz uma chamada ao Qwen como juiz para um caso individual."""
    user = (
        f"## entrada_usuario\n{caso['entrada_usuario']}\n\n"
        f"## resposta_ideal\n{caso['resposta_ideal']}\n\n"
        f"## resposta_real\n{resposta_real}\n\n"
        f"## criterios_avaliacao\n{json.dumps(caso['criterios_avaliacao'], ensure_ascii=False, indent=2)}\n"
    )
    juiz = chat(
        messages=[
            {"role": "system", "content": _PROMPT_JUIZ},
            {"role": "user", "content": user},
        ],
        enable_thinking=False,
        temperature=0.0,
        response_format={"type": "json_object"},
        backend=backend,  # type: ignore[arg-type]
    )
    try:
        return json.loads(juiz["content"])
    except json.JSONDecodeError:
        return {
            "aprovado": False,
            "criterios_atendidos": [],
            "criterios_violados": ["Falha ao parsear resposta do juiz"],
            "score": 0,
            "justificativa_curta": "Resposta do juiz não foi JSON válido",
        }


def _formatar_relatorio(resultados: list[dict[str, Any]]) -> str:
    """Gera o relatório Markdown agregado: totais, quebra por categoria,
    detalhe dos falhos e tabela com todos os casos.
    """
    por_categoria: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in resultados:
        por_categoria[r["categoria"]].append(r)

    linhas: list[str] = []
    linhas.append("# Relatório Sprint 1 — BluaDiagnostics")
    linhas.append("")
    linhas.append(f"**Gerado em**: {datetime.now(timezone.utc).isoformat()}")
    linhas.append("")
    total = len(resultados)
    aprovados = sum(1 for r in resultados if r["juiz"]["aprovado"])
    score_medio = sum(r["juiz"]["score"] for r in resultados) / max(total, 1)
    linhas.append(f"**Total de casos**: {total}")
    linhas.append(f"**Aprovados**: {aprovados} ({aprovados / total * 100:.1f}%)")
    linhas.append(f"**Score médio**: {score_medio:.1f}/100")
    linhas.append("")
    linhas.append("## Por categoria")
    linhas.append("")
    linhas.append("| Categoria | Casos | Aprovados | Taxa | Score médio |")
    linhas.append("|---|---|---|---|---|")
    for cat, lista in sorted(por_categoria.items()):
        n = len(lista)
        ok = sum(1 for r in lista if r["juiz"]["aprovado"])
        score = sum(r["juiz"]["score"] for r in lista) / n
        linhas.append(f"| {cat} | {n} | {ok} | {ok / n * 100:.1f}% | {score:.1f} |")
    linhas.append("")
    linhas.append("## Casos que falharam")
    linhas.append("")
    falharam = [r for r in resultados if not r["juiz"]["aprovado"]]
    if not falharam:
        linhas.append("Nenhum caso falhou. ✅")
    else:
        for r in falharam:
            linhas.append(f"### {r['id']} — {r['categoria']}")
            linhas.append(f"**Entrada**: {r['entrada_usuario']}")
            linhas.append(f"**Resposta**: {r['resposta_real'][:300]}...")
            linhas.append(f"**Critérios violados**: {', '.join(r['juiz']['criterios_violados']) or '—'}")
            linhas.append(f"**Justificativa do juiz**: {r['juiz']['justificativa_curta']}")
            linhas.append("")
    linhas.append("## Detalhe por caso")
    linhas.append("")
    linhas.append("| ID | Categoria | Aprovado | Score |")
    linhas.append("|---|---|---|---|")
    for r in resultados:
        marca = "✅" if r["juiz"]["aprovado"] else "❌"
        linhas.append(f"| {r['id']} | {r['categoria']} | {marca} | {r['juiz']['score']} |")
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description="BluaDiagnostics — eval Sprint 1")
    parser.add_argument("--backend", default="dashscope", choices=["dashscope", "ollama"])
    parser.add_argument("--max-casos", type=int, default=None,
                        help="Limita número de casos (debug).")
    args = parser.parse_args()

    print("[bluadiagnostics] indexando knowledge base...")
    info = indexar_knowledge_base()
    print(f"[bluadiagnostics] {info}")

    print("[bluadiagnostics] construindo grafo...")
    grafo = construir_grafo()

    eval_set = json.loads(_EVAL_PATH.read_text(encoding="utf-8"))
    casos = eval_set["casos"]
    if args.max_casos:
        casos = casos[: args.max_casos]

    resultados: list[dict[str, Any]] = []
    for caso in casos:
        print(f"[bluadiagnostics] caso {caso['id']} ({caso['categoria']})")
        thread_id = f"eval-{caso['id']}-{uuid.uuid4().hex[:6]}"
        try:
            estado = executar_turno(
                grafo,
                mensagem_usuario=caso["entrada_usuario"],
                thread_id=thread_id,
                beneficiario_id=None,
                backend=args.backend,
            )
            resposta_real = estado.get("resposta_final") or "(sem resposta)"
        except Exception as exc:  # noqa: BLE001
            resposta_real = f"(erro durante execução: {exc})"

        juiz = _avaliar_caso(caso, resposta_real, backend=args.backend)
        resultados.append(
            {
                "id": caso["id"],
                "categoria": caso["categoria"],
                "entrada_usuario": caso["entrada_usuario"],
                "resposta_real": resposta_real,
                "juiz": juiz,
            }
        )
        print(f"  → aprovado={juiz['aprovado']} score={juiz['score']}")

    relatorio = _formatar_relatorio(resultados)
    _RELATORIO_PATH.write_text(relatorio, encoding="utf-8")
    print(f"[bluadiagnostics] relatório salvo em {_RELATORIO_PATH}")

    saida_json = _RELATORIO_PATH.with_suffix(".json")
    saida_json.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[bluadiagnostics] resultados crus em {saida_json}")


if __name__ == "__main__":
    main()
