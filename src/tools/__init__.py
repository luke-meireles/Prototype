"""Tools (function calling) do BluaDiagnostics — todas com dados mockados."""

from src.tools.historico import consultar_historico_paciente
from src.tools.interacoes import verificar_interacoes_medicamentosas
from src.tools.agendamento import agendar_teleconsulta
from src.tools.wearable import consultar_sinais_vitais_wearable
from src.tools.classificador_risco import classificar_risco_clinico

# Mapeamento usado pelo executor de tool calls do LangGraph
TOOL_REGISTRY = {
    "consultar_historico_paciente": consultar_historico_paciente,
    "verificar_interacoes_medicamentosas": verificar_interacoes_medicamentosas,
    "agendar_teleconsulta": agendar_teleconsulta,
    "consultar_sinais_vitais_wearable": consultar_sinais_vitais_wearable,
    "classificar_risco_clinico": classificar_risco_clinico,
}
