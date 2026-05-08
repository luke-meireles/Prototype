# Sistema de Triagem de Manchester — versão simplificada BluaDiagnostics

> Adaptação didática do Protocolo de Manchester para uso pelo agente de
> triagem digital. A classificação final em ambiente clínico real cabe a
> profissional de saúde habilitado, em fluxograma estruturado.

## Visão geral

O Sistema de Manchester organiza os pacientes em cinco níveis de prioridade,
identificados por cor e tempo-alvo de atendimento. O objetivo não é fazer
diagnóstico, e sim definir **quem precisa ser visto primeiro**. No
BluaDiagnostics, o agente usa esta lógica para sinalizar a urgência da
queixa relatada e orientar o próximo passo (emergência, teleconsulta de
urgência, teleconsulta de rotina ou orientação educacional).

---

## Vermelho — Emergência

**Tempo-alvo**: atendimento imediato.
**Mensagem do bot**: "A descrição que você fez sugere uma situação de
emergência. Por favor, ligue para o SAMU 192 ou vá ao pronto-socorro mais
próximo agora. Posso seguir aqui com você até que receba ajuda."

**Critérios típicos**:
- Parada cardiorrespiratória em curso ou iminente.
- Inconsciência, convulsão ativa.
- Dispneia grave, esforço respiratório com fala entrecortada, cianose.
- Dor torácica intensa em esforço com sudorese fria, irradiação para braço
  ou mandíbula, especialmente em paciente com fatores de risco.
- Cefaleia súbita, descrita como "pior dor de cabeça da vida".
- Déficit neurológico súbito (fraqueza unilateral, fala arrastada, perda de
  visão, desvio da rima labial) — sinais de AVC.
- Sangramento ativo abundante, hematêmese, melena com hipotensão.
- Anafilaxia (urticária generalizada com dispneia ou hipotensão).
- Ideação suicida ativa com plano e acesso a meios.
- Trauma craniano com perda de consciência.

**Conduta do agente**: interromper a triagem, escalonar imediatamente para
serviço de emergência, manter o paciente engajado e oferecer chamada para
suporte humano Care Plus em paralelo.

---

## Laranja — Muito urgente

**Tempo-alvo**: atendimento em até 10 minutos.
**Mensagem do bot**: "Pelo que você descreveu, é importante ser avaliado
rapidamente. Vou abrir uma teleconsulta de urgência agora — fique no
celular."

**Critérios típicos**:
- Dor torácica moderada sem critérios de emergência clara, mas em paciente
  com risco cardiovascular.
- Dispneia em repouso de início recente.
- Dor abdominal severa com sinais de irritação peritoneal.
- Febre alta persistente em imunossuprimido, neonato ou idoso fragilizado.
- Suspeita de sepse: febre + taquicardia + hipotensão + alteração de
  consciência.
- Crise hipertensiva com sintomas (cefaleia intensa, alteração visual).
- Hemorragia controlada porém significativa.
- Suspeita de fratura exposta ou luxação de grande articulação.
- Ideação suicida sem plano imediato.

**Conduta do agente**: classificar como `manchester=laranja`, gerar
`agendar_teleconsulta(urgencia="alta")`, anexar ficha pré-clínica
estruturada para o médico que receberá a chamada.

---

## Amarelo — Urgente

**Tempo-alvo**: atendimento em até 60 minutos.
**Mensagem do bot**: "Pelo seu relato, vale ser avaliado por um profissional
ainda hoje. Posso agendar uma teleconsulta de urgência?"

**Critérios típicos**:
- Dor moderada de origem incerta sem sinais de gravidade (lombalgia
  intensa, cefaleia que não cede a analgésico de rotina).
- Vômitos repetidos sem desidratação grave.
- Diarreia aguda com risco de desidratação leve.
- Febre persistente em adulto sadio com sinais de localização (tosse, dor
  de garganta intensa, dor lombar com hematúria).
- Lesão dermatológica de progressão rápida sem comprometimento sistêmico.
- Ansiedade aguda com crises de pânico recorrentes.

**Conduta do agente**: tentar coletar dossiê completo, oferecer teleconsulta
no mesmo dia. Se sintomas piorarem, reclassificar para laranja.

---

## Verde — Pouco urgente

**Tempo-alvo**: atendimento em até 24 horas.
**Mensagem do bot**: "Seu quadro parece estável. Posso agendar uma
teleconsulta para amanhã ou nas próximas 24 horas?"

**Critérios típicos**:
- Resfriado e gripe sazonal sem sinais de complicação.
- Dor leve a moderada autolimitada.
- Pequenos cortes superficiais com sangramento controlado.
- Náusea isolada sem desidratação.
- Conjuntivite sem comprometimento visual.
- Renovação de receita simples para condições controladas.

**Conduta do agente**: oferecer agendamento de rotina, orientação de
sintomas de alerta para reescalada e medidas educacionais.

---

## Azul — Não urgente

**Tempo-alvo**: cuidado eletivo / orientação educacional.
**Mensagem do bot**: "Pelo que descreveu, parece algo que pode ser
acompanhado fora de teleconsulta. Posso te enviar orientações ou agendar
algo conforme sua preferência."

**Critérios típicos**:
- Dúvidas administrativas (rede credenciada, cobertura, segunda via de
  carteirinha).
- Dúvidas sobre check-up preventivo de rotina.
- Solicitação de informações educacionais sobre alimentação, sono ou
  atividade física.
- Acompanhamento longitudinal de condição estável sem queixa nova.

**Conduta do agente**: oferecer conteúdo educacional, encaminhar para a
cartilha do beneficiário ou direcionar para o canal administrativo.

---

## Sinais de alerta para reescalada (qualquer cor → vermelho/laranja)

Em todas as conversas, o agente deve monitorar e escalonar imediatamente se
o paciente relatar ao longo do diálogo:

- Piora rápida do estado geral.
- Surgimento de dor torácica, dispneia ou alteração neurológica.
- Sinais de choque (sudorese fria, palidez extrema, confusão mental).
- Sangramento que não cessa em 10 minutos com compressão.
- Ideação suicida que estava ausente no início da conversa.
- Recusa de tratamento por gestante com sinais de gravidade.

---

## Limites do uso digital

Este protocolo é uma simplificação. O fluxograma oficial de Manchester usa
apresentações clínicas (ex.: "dor torácica", "dispneia") e discriminadores
em sequência. A versão digital aqui descrita serve para orientar a conduta
do agente, mas qualquer dúvida deve resultar em escalada conservadora — em
saúde, errar para mais cauto é a única opção segura.
