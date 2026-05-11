"""Agentes do BluaDiagnostics — orquestrados via LangGraph.

Cada arquivo nesta pasta é UM agente especializado. Eles compartilham a
mesma interface: recebem mensagens, chamam o LLM com seu sub-prompt
específico, opcionalmente invocam tools/RAG, e devolvem a resposta.

O grafo em ``src/graph.py`` é quem decide QUAL agente executar para
cada turno — esses arquivos só implementam o "trabalho" de cada um.

Re-exports neste ``__init__`` permitem ``from src.agents import
classificar_intent`` em vez de ``from src.agents.router import ...``.
"""

from src.agents.router import classificar_intent
from src.agents.checkup import executar_checkup
from src.agents.triagem import executar_triagem
from src.agents.prescricao import executar_prescricao
from src.agents.safety import auditar_resposta

__all__ = [
    "classificar_intent",
    "executar_checkup",
    "executar_triagem",
    "executar_prescricao",
    "auditar_resposta",
]
