"""BluaDiagnostics — assistente clínico digital Care Plus.

Estrutura do pacote ``src``:

- ``llm/``      → wrappers Qwen (DashScope + Ollama)
- ``agents/``   → 5 agentes especializados (router, checkup, triagem,
                  prescricao, safety)
- ``rag/``      → indexação + retrieval + reranker (ChromaDB)
- ``tools/``    → 5 tools mockadas que o LLM chama via function calling
- ``graph.py``  → grafo LangGraph que orquestra tudo
- ``audit_log.py`` → registro estruturado JSON para auditoria LGPD

O ponto de entrada do projeto é o notebook
``notebooks/sprint1_poc.ipynb`` (rodar no Google Colab).
"""

__version__ = "0.1.0"
