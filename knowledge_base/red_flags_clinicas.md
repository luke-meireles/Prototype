# Red flags clínicas — guia rápido por sistema

> Conteúdo de referência para o agente de triagem do BluaDiagnostics. Toda
> red flag aqui listada exige interrupção imediata da triagem e escalada
> conforme o protocolo Manchester (vermelho ou laranja).

## Sistema cardiovascular

### Dor torácica de alto risco
- Dor opressiva retroesternal em esforço, com duração maior que 10 minutos.
- Irradiação para braço esquerdo, mandíbula ou dorso.
- Acompanhada de sudorese fria, palidez, náusea ou síncope.
- Em paciente com fatores de risco: idade > 45 (homens) ou > 55 (mulheres),
  hipertensão, diabetes, tabagismo, dislipidemia, doença coronariana
  prévia, histórico familiar precoce.

### Síncope
- Perda súbita da consciência, principalmente sem pródromos.
- Em esforço ou na posição supina.
- Acompanhada de dor torácica ou palpitações.

### Sinais de insuficiência cardíaca aguda
- Dispneia paroxística noturna recente.
- Edema importante, ortopneia, ganho de peso súbito.
- Saturação periférica de oxigênio < 92% sem doença respiratória prévia.

## Sistema neurológico

### Suspeita de AVC (mnemônico SAMU)
- **S**orriso assimétrico.
- **A**brace os dois braços e veja se um cai.
- **M**úsica/fala enrolada ao repetir frase simples.
- **U**rgente ligar 192 — tempo é cérebro.

Outros sinais: alteração súbita da visão (amaurose, diplopia), tontura
intensa de início abrupto, perda de equilíbrio descoordenada, parestesia
unilateral.

### Cefaleia de alto risco
- "A pior dor de cabeça da vida", início súbito (cefaleia em trovoada).
- Cefaleia + febre + rigidez de nuca (suspeita de meningite).
- Cefaleia progressiva em paciente imunossuprimido ou oncológico.
- Cefaleia após trauma craniano recente.

### Convulsão de novo
- Crise convulsiva em paciente sem história prévia.
- Crise prolongada (> 5 minutos) ou múltipla sem retorno de consciência
  entre elas (estado de mal epiléptico).

## Sistema respiratório

- Dispneia súbita em repouso, especialmente com dor torácica (pensar em
  TEP).
- Hemoptise volumosa (mais que escarro raiado).
- Sibilância grave, fala entrecortada, retração intercostal.
- Saturação periférica < 92% em ar ambiente.
- Suspeita de aspiração de corpo estranho com asfixia.

## Sistema gastrointestinal

- Dor abdominal severa de início súbito, especialmente com defesa
  abdominal.
- Hematêmese (vômito com sangue) ou melena (fezes pretas, fétidas).
- Icterícia com dor abdominal (pensar em colangite).
- Distensão abdominal com parada de eliminação de gases e fezes (suboclusão
  ou obstrução intestinal).
- Dor abdominal em gestante a partir do 2º trimestre (descolamento, pré-eclâmpsia).

## Sistema renal/urinário

- Anúria (ausência de urina) > 12 horas.
- Hematúria volumosa com coágulos.
- Cólica renal com febre alta (suspeita de pielonefrite com obstrução).

## Sistema obstétrico

- Sangramento vaginal abundante na gestação.
- Dor abdominal severa com hipertensão gestacional.
- Cefaleia + alteração visual + edema importante (pré-eclâmpsia).
- Convulsão em gestante (eclâmpsia).
- Diminuição súbita de movimentos fetais a partir da 28ª semana.

## Sistema psiquiátrico

- Ideação suicida ativa, com plano e meios disponíveis.
- Tentativa de suicídio recente.
- Surto psicótico com agitação, agressividade, alucinações.
- Suspeita de violência doméstica em curso.
- Recusa alimentar grave em paciente com transtorno alimentar prévio.

## Sistema dermatológico

- Lesões com necrose ou crepitação subcutânea (fasceíte necrosante).
- Síndrome de Stevens-Johnson / NET (descolamento epidérmico, mucosas
  acometidas, febre alta após início recente de medicação).
- Anafilaxia (urticária generalizada + dispneia + hipotensão).
- Erisipela ou celulite com sinais sistêmicos (febre alta, taquicardia).

## Sistema musculoesquelético

- Trauma com deformidade óssea aparente.
- Fratura exposta.
- Suspeita de luxação articular.
- Compressão medular: dor lombar súbita + déficit motor + alteração
  esfincteriana (síndrome da cauda equina).

## Sistema oftalmológico

- Perda súbita de visão.
- Trauma ocular penetrante.
- Olho vermelho com dor intensa e fotofobia importante.

## Sistema endocrinológico

- Glicemia capilar > 400 mg/dL com sinais de cetoacidose (Kussmaul, hálito
  cetônico, desidratação).
- Hipoglicemia grave (glicemia < 50 mg/dL com alteração de consciência).
- Crise tireotóxica (taquicardia, agitação, febre).

## Sintomas inespecíficos que merecem cautela

- Confusão mental aguda em idoso (pode ser delirium por causa grave).
- Perda de peso involuntária > 5% em 6 meses.
- Febre persistente > 7 dias sem foco identificado.
- Astenia desproporcional ao esforço habitual.

## Conduta padrão do agente em qualquer red flag

1. Interromper protocolo atual.
2. Comunicar com clareza e empatia: "O que você descreveu pode ser sério.
   Preciso pedir que ligue para o SAMU 192 ou vá agora ao pronto-socorro
   mais próximo."
3. Não solicitar mais sinais vitais ou histórico nesse momento — a prioridade
   é o paciente buscar atendimento.
4. Manter o canal aberto para apoio emocional até a confirmação de socorro.
5. Disparar audit log com `safety_layer_passou=true` apenas após validar
   que o disclaimer e a escalada constam na mensagem final.
