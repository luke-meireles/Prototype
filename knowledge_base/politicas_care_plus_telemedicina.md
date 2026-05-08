# Políticas Care Plus de telemedicina

> Documento de referência para o agente Blua. Resume o funcionamento do
> programa de teleconsulta da operadora Care Plus, suas especialidades
> elegíveis, regras de cobertura e fluxos de emergência.

## Princípios gerais

A Care Plus oferece teleconsulta como modalidade complementar ao atendimento
presencial, regulada pela CFM Resolução 2.314/2022 (Telemedicina) e pela
LGPD (Lei 13.709/2018). Toda teleconsulta:

- É registrada com gravação criptografada armazenada por cinco anos.
- Gera prontuário digital integrado ao histórico do beneficiário.
- Permite emissão de receituário, atestado e SADT digitais com assinatura
  via ICP-Brasil ou padrão equivalente.
- Pode ser convertida em encaminhamento presencial quando o médico julgar
  necessário.

## Especialidades cobertas em telemedicina

### 1. Clínica geral

Porta de entrada do programa. Atende sintomas inespecíficos, dúvidas sobre
medicação, renovação de receita e triagem de queixas. Disponibilidade 24/7
para urgência. Tempo médio de espera em horário comercial: até 8 minutos.

### 2. Pediatria

Atende crianças de 0 a 14 anos. Inclui acompanhamento longitudinal,
orientação a pais e responsáveis, manejo de quadros agudos como febre,
diarreia, dermatite, otite. Restrição: lactentes < 3 meses com febre devem
ser direcionados a atendimento presencial.

### 3. Ginecologia

Atende dúvidas sobre ciclo menstrual, contracepção, sintomas urinários,
acompanhamento pré-natal de baixo risco e renovação de receitas. Coletas
e exames físicos (ex.: Papanicolau, ultrassom transvaginal) ficam fora do
escopo digital — agendados em rede presencial.

### 4. Dermatologia

Atende lesões cutâneas com fotos enviadas previamente pelo app. Não
substitui dermatoscopia presencial em lesões suspeitas de malignidade. Útil
para acne, dermatite, psoríase estável, alopecia, orientação cosmiátrica.

### 5. Psiquiatria

Atende transtornos de humor, ansiedade, sono e dependências leves a
moderadas. Inclui prescrição de psicotrópicos não controlados via tarja
preta digital quando a normativa permite. Encaminhamento para emergência em
ideação suicida ativa, surto psicótico ou quadros de violência.

### 6. Endocrinologia

Acompanhamento de diabetes, dislipidemia, distúrbios da tireoide e
obesidade. Integra dados do wearable do paciente (glicemia capilar via app
parceiro, passos, sono) na consulta. Solicitações de exame seguem fluxo
laboratorial Care Plus.

### 7. Cardiologia

Avaliação de hipertensão controlada, dislipidemia, acompanhamento pós-IAM
ou pós-cirúrgico estável. Eletrocardiograma e ecocardiograma exigem
presencial. Em caso de dor torácica em curso, o agente direciona
imediatamente para SAMU 192 e não tenta agendar consulta digital.

### 8. Nutrição

Atendimento por nutricionista cadastrado no programa, com plano alimentar
personalizado, integração com diário alimentar do app Blua e
acompanhamento mensal.

## Regras de cobertura

- **Inclusos no plano Care Plus Premium**: teleconsulta ilimitada em todas
  as especialidades acima.
- **Care Plus Essencial**: teleconsulta ilimitada em clínica geral,
  pediatria e psiquiatria; demais especialidades sob coparticipação simbólica
  de R$ 25 por consulta.
- **Care Plus Sênior**: teleconsulta ilimitada e visita domiciliar
  programada para acamados (fora do escopo digital).

## Fluxo de emergência

A teleconsulta **não substitui** pronto atendimento em situações de
emergência. O agente Blua deve, sempre que houver red flag:

1. Interromper a triagem.
2. Orientar SAMU 192 e/ou pronto-socorro mais próximo.
3. Informar o endereço de retaguarda Care Plus quando houver na localização
   do paciente.
4. Registrar evento no audit log com `manchester=vermelho`.
5. Oferecer permanecer na conversa até o atendimento humano assumir.
6. Disparar notificação automatizada à equipe médica plantonista da Care
   Plus (em produção; PoC simula).

## Fluxo de prescrição remota inteligente

Quando médico atendente solicita apoio do agente Blua para prescrição:

1. Agente consulta histórico via `consultar_historico_paciente`.
2. Verifica interações com `verificar_interacoes_medicamentosas`.
3. Sugere prescrição estruturada **marcada como
   `RASCUNHO_AGUARDANDO_REVISAO_MEDICA`**.
4. Médico revisa, edita, assina digitalmente e libera ao paciente.
5. O sistema **nunca** dispara prescrição final sem aprovação humana
   explícita, conforme CFM Res. 2.314/22.

## Direitos do beneficiário

- Solicitar a qualquer momento que a interação seja transferida a um humano.
- Pedir cópia do histórico de interações no padrão LGPD (portabilidade).
- Solicitar exclusão de dados não obrigatórios para fins assistenciais.
- Receber explicação clara sobre uso de IA antes de iniciar a conversa
  (consentimento informado).
- Recusar gravação e seguir apenas com atendimento presencial.

## Limites operacionais

A teleconsulta Care Plus não cobre:

- Procedimentos invasivos ou cirurgias.
- Atendimento obstétrico em trabalho de parto.
- Acompanhamento intensivo de pacientes graves domiciliares.
- Atestado para fins judiciais ou periciais.
- Solicitação de exames de alto custo sem indicação clínica documentada.

## Indicadores de qualidade monitorados

- Tempo médio de espera por especialidade.
- NPS pós-consulta.
- Taxa de reagendamento ou conversão a presencial.
- Eventos adversos relatados.
- Aderência ao protocolo de red flags pelo agente Blua (auditado mensalmente
  via amostragem de logs).

## Integração com a jornada do beneficiário

A teleconsulta Care Plus não é uma ilha — está integrada à jornada
contínua do beneficiário no app Blua. A operadora monitora cinco pontos
de contato principais:

1. **Pré-consulta**: o agente Blua coleta a queixa, organiza dossiê
   estruturado e antecipa ao médico um resumo das últimas três consultas
   relevantes, alergias, medicações em uso e dados de wearable
   relevantes. O médico recebe esse pacote 5 minutos antes da chamada,
   reduzindo tempo de anamnese e aumentando a qualidade do encontro.

2. **Durante a consulta**: o sistema oferece ao médico (em painel
   lateral) sugestões de protocolos, alertas de interações
   medicamentosas e referências da knowledge base — sempre como apoio
   informativo, nunca como substituto da decisão clínica.

3. **Pós-consulta**: a prescrição passa pelo agente de Prescrição, que
   verifica interações com medicações em uso, alerta sobre alergias e
   compatibilidade com função renal/hepática quando há registro. O
   médico recebe o rascunho, revisa, edita se necessário e assina
   digitalmente.

4. **Aderência terapêutica**: 7, 14 e 30 dias após a consulta, o agente
   reabre canal proativo perguntando como o beneficiário está, se
   conseguiu tomar as medicações, se houve efeito adverso. As respostas
   são logadas e devolvidas ao médico em painel longitudinal.

5. **Conversão presencial**: quando o médico decide converter para
   atendimento presencial, o agente facilita o agendamento na rede
   credenciada Care Plus, com transporte sanitário disponível para
   beneficiários elegíveis (Sênior, Premium).

## Garantia institucional Care Plus

A operadora se compromete formalmente com:

- **Disponibilidade 24/7** de clínica geral em telemedicina.
- **Tempo máximo de espera** de 10 minutos em horário comercial para
  clínica geral, conforme acordo de nível de serviço (SLA) auditável.
- **Sigilo absoluto** dos dados clínicos, com armazenamento em data
  centers em território nacional.
- **Direito de recusa** de teleconsulta em qualquer momento — o
  beneficiário sempre pode optar por presencial.
- **Encaminhamento gratuito** para emergência quando indicado, com cobertura
  total de remoção pelo SAMU credenciado.

## Auditoria interna periódica

A cada trimestre, o time de qualidade clínica Care Plus audita uma
amostra aleatória de 200 atendimentos. Critérios:

- Aderência ao protocolo de triagem.
- Adequação da especialidade indicada.
- Segurança da prescrição emitida.
- Tempo de resposta a red flags.
- Qualidade do registro em prontuário.

Resultados auditados são compartilhados com a Diretoria Médica e geram
plano de ação trimestral. Em casos de divergência crítica (ex.: red flag
não escalonada), há revisão imediata e treinamento do agente.
