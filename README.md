# BluaDiagnostics

> **Assistente clínico digital da Care Plus** — chatbot multi-agente em
> Português Brasileiro nativo, integrado ao app Blua, que apoia triagem
> conversacional de sintomas e prescrição remota assistida (sempre com
> aprovação médica humana). Sprint 1 de PoC acadêmica FIAP.
>
> **Projeto Colab-first**: o ponto de entrada canônico é o notebook
> [`notebooks/sprint1_poc.ipynb`](notebooks/sprint1_poc.ipynb), executado no
> Google Colab.

## Integrantes

- Lucas Gabriel Alvarenga e Meireles — RM 567305
- Gabriel Augusto da Silva — RM 567057
- Leonardo Kenji Kubo Barboza — RM 567518
- Lucas Koiti Uyeno de Souza — RM 568128
- Lucas Morio Ikeda — RM 567616

## Persona escolhida e justificativa

**Persona principal**: beneficiário Care Plus em autoavaliação (paciente
leigo). É o público mais sensível e com maior volume — qualquer ganho de
qualidade na triagem reduz custo, salva vidas e melhora o NPS do app
Blua. A arquitetura é **dual-persona-ready**: o Agente de Prescrição
atende secundariamente o médico Care Plus pós-teleconsulta, organizando
histórico e validando interações como rascunho aguardando assinatura.

A Care Plus tem mais de 600 mil beneficiários no Brasil, do grupo
internacional Bupa. Hoje o app Blua é majoritariamente reativo. O
BluaDiagnostics transforma o app numa plataforma proativa de cuidado,
reduzindo barreiras de acesso à teleconsulta e detectando red flags
clínicas precocemente — sempre respeitando a regra inegociável de **não
substituir o médico**.

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Ambiente de execução | **Google Colab** (Python 3.11, CPU runtime gratuito) |
| LLM principal | Qwen (`qwen-plus` via DashScope International) |
| SDK | `openai` Python (Qwen é OpenAI-compatible) + `qwen-agent` (uma demo) |
| Orquestração multi-agente | LangGraph (`StateGraph` + `MemorySaver`) |
| RAG utilitários | `langchain-text-splitters` (apenas o splitter) |
| Vector DB | ChromaDB (persistência local em `/content/bluadiagnostics/chroma_db/`) |
| Embeddings | `intfloat/multilingual-e5-large` via `sentence-transformers` |
| Reranker | Interface pluggável (default desligado na PoC) |
| Memória curto prazo | LangGraph `MemorySaver` |
| Memória longo prazo | JSON estruturado por `beneficiario_id` |
| Validação | Pydantic v2 |
| Logging estruturado | `structlog` (output JSON em `logs/`) |
| Avaliação | LLM-as-a-judge com Qwen sobre 15 casos |
| Diagramação | Mermaid + PNG exportado |
| Segredos | **Google Colab Secrets** (preferencial) ou `python-dotenv` em local |

## Arquitetura

A arquitetura completa está em [`docs/arquitetura.mermaid`](docs/arquitetura.mermaid)
e renderizada em [`docs/arquitetura.png`](docs/arquitetura.png).

```mermaid
flowchart TD
    Usuario([Usuário Care Plus]) --> Roteador{Roteador<br/>thinking=OFF}
    Roteador --> Checkup[Check-up<br/>thinking=OFF]
    Roteador --> Triagem[Triagem<br/>thinking=ON]
    Roteador --> Prescricao[Prescrição<br/>thinking=ON]
    Checkup --> Tools[(Tools mockadas)]
    Triagem --> RAG[(ChromaDB)]
    Triagem --> Tools
    Prescricao --> RAG
    Prescricao --> Tools
    Tools --> Safety{Safety Layer}
    RAG --> Safety
    Safety --> Audit[(Audit log<br/>structlog)]
    Audit --> Resposta([Resposta + disclaimer])
```

Cinco nós principais: **Roteador → (Check-up | Triagem | Prescrição |
Dúvida | Fora-de-escopo) → Safety Layer → Audit Log**, com `thread_id`
preservando memória multi-turno.

## Comparação de modelos: Qwen vs Llama 3.3

Detalhes em [`docs/decisao_modelo.md`](docs/decisao_modelo.md). Resumo:

| Critério | Qwen (escolhido) | Llama 3.3 70B |
|---|---|---|
| Lançamento | 2025–2026 | dez/2024 |
| PT-BR clínico | nativo, 201 idiomas | bom, sem foco médico |
| Function calling | nativo OpenAI-compatible | suportado, mais reescrita |
| IFBench | 76,5 | ~71 |
| Licença | **Apache 2.0** | Llama Community License (restrições) |
| Hybrid thinking mode | **sim, toggle por chamada** | não |
| Contexto | até 1M | 128K |
| Arquitetura | dense + MoE 35B-A3B | dense 70B |
| Disponibilidade Colab | DashScope (cloud) — funciona em CPU runtime | exige GPU robusta on-prem |
| Frameworks de agente | `qwen-agent` oficial + LangGraph | LangGraph |

**Cinco motivos para Qwen**:

1. **Instruction following (IFBench 76,5)** — crítico para guardrails
   clínicos respeitarem a regra inegociável.
2. **PT-BR nativo de qualidade clínica** — reduz alucinação terminológica
   em bulas e protocolos.
3. **Hybrid thinking mode** — toggle por agente sem trocar de modelo.
4. **Licença Apache 2.0** — sem restrições comerciais.
5. **Compatível com Colab** — toda inferência roda em cloud (DashScope), o
   notebook não precisa de GPU paga.

## Modos de deployment

Detalhes em [`docs/deployment_modes.md`](docs/deployment_modes.md).

| Modo | Quando usar | Backend |
|---|---|---|
| **A — Cloud DashScope** (padrão Colab) | PoC, homologação, primeira fase de produção | `qwen-plus` em `dashscope-intl.aliyuncs.com` |
| **B — On-prem Ollama** (fora do Colab) | clientes com isolamento total, contingência | `qwen:9b` em `localhost:11434` |

Troca via parâmetro: `chat(..., backend="dashscope" or "ollama")`. **No Colab,
use sempre `dashscope`** — o Ollama exige um servidor local, indisponível
no runtime do Colab por padrão.

## Mapeamento de riscos clínicos e LGPD

| Risco | Origem | Mitigação no BluaDiagnostics |
|---|---|---|
| Alucinação clínica | LLM gera fato falso | RAG com KB curada (7 docs) + Safety Layer + disclaimer obrigatório |
| Viés algorítmico | Treino do modelo | Lógica determinística de risco em `classificar_risco_clinico`; auditoria periódica |
| LGPD art. 7º/11/18 (dado sensível de saúde) | Tratamento de dado clínico | Consentimento explícito no app, dados em território nacional, DPO formal, direitos de acesso/portabilidade/exclusão |
| Responsabilidade sobre prescrição (CFM Res. 2.314/22) | Prescrição digital | Agente nunca emite receita final; tag `[RASCUNHO_AGUARDANDO_REVISAO_MEDICA]`; assinatura ICP-Brasil pelo médico |
| Atrasar atendimento de emergência | Triagem digital lenta | Detecção de red flag → escalada SAMU 192 imediata, sem coleta extra |
| Dependência emocional | Usuário substitui suporte humano | Mensagens recorrentes oferecendo "Atendente humano"; encaminhamento ativo em ideação suicida (CVV 188) |
| Overtrust do usuário | Confiança excessiva no bot | Disclaimer obrigatório em toda resposta; linguagem probabilística; recusa de fechamento de diagnóstico |

## Como rodar a PoC no Google Colab

### Pré-requisitos

- Conta Google (para o Colab).
- Chave **DashScope International** (<https://bailian.console.alibabacloud.com>)
  com o **Model Studio** ativado (1 milhão de tokens grátis por 90 dias).
- Repositório do projeto disponível no GitHub (próprio fork) **ou** o `.zip`
  da pasta `bluadiagnostics/` para upload manual.

### Passo-a-passo

1. **Suba o projeto ao Colab** — duas opções:
   - **GitHub** (recomendado): no notebook, edite a constante `REPO_URL` na
     Seção 1.1 e a célula faz `git clone` automaticamente em
     `/content/bluadiagnostics`.
   - **Upload manual**: comprima a pasta `bluadiagnostics/` em `.zip`, suba
     pela aba **Arquivos** do Colab e descompacte com
     `!unzip bluadiagnostics.zip -d /content/`.
2. **Configure o Colab Secret**:
   - Ícone de **chave** (🔑) na barra lateral esquerda do Colab.
   - **+ Add new secret** → Name: `DASHSCOPE_API_KEY` → Value: sua chave
     (do **Bailian Console**).
   - Habilite o toggle **Notebook access**.
3. **Abra `notebooks/sprint1_poc.ipynb`** no Colab e execute as células em
   ordem (`Runtime → Run all` funciona):
   - **Seção 1**: clona o repo (se necessário), instala deps (~3 min) e
     carrega o secret. Não exige GPU — Qwen roda em cloud.
   - **Seção 2**: baixa `intfloat/multilingual-e5-large` (~1 GB) e indexa
     a KB (~30 s).
   - **Seções 3–6**: validam tools, wrapper Qwen e o grafo LangGraph.
   - **Seções 7–12**: 6 demos clínicas (happy path, multi-turno, red flag,
     tool, safety, qwen-agent).
   - **Seção 13**: roda o eval set (15 casos) com Qwen como juiz e renderiza
     o relatório.

### Solução de problemas comuns no Colab

| Erro | Causa | Como resolver |
|---|---|---|
| `DASHSCOPE_API_KEY não encontrada` | Secret não configurado ou sem Notebook access | Reabra o painel 🔑 e habilite **Notebook access** no secret |
| `403 AccessDenied.Unpurchased` | Conta DashScope sem free trial ativada | Ative o **Model Studio** em <https://bailian.console.alibabacloud.com/> |
| `401 Unauthorized` | Chave inválida ou expirada | Gere nova chave no Bailian Console e atualize o Secret |
| `ModuleNotFoundError` após restart | Runtime foi desconectado | Re-execute a Seção 1 (instalação de deps) |
| `OSError: HTTP error... e5-large` | Cache de embeddings corrompido | `!rm -rf ~/.cache/huggingface` e re-execute a Seção 2 |
| `429 quota` / `rate limit` | Free trial atingiu RPM | Aguarde alguns segundos ou divida a execução |

### Execução local (alternativa fora do Colab)

Se preferir rodar fora do Colab — Linux/macOS/Windows com Python 3.11+:

```bash
git clone <repo> bluadiagnostics
cd bluadiagnostics
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
cp .env.example .env             # edite com sua DASHSCOPE_API_KEY
python main.py --smoke           # ping no LLM
python main.py --once "Sinto dor lombar há dois dias."
python -m evals.run_evals        # eval set
```

A CLI `main.py` reaproveita o mesmo módulo `colab_setup.py`, então funciona
igual em ambos ambientes.

## Estrutura de pastas

```
bluadiagnostics/
├── README.md
├── .gitignore
├── requirements.txt          # deps Colab-friendly
├── .env.example              # referência para uso local (Colab usa Secrets)
├── colab_setup.py            # bootstrap idempotente para o notebook
├── main.py                   # CLI fina (útil em local e em !python)
├── docs/                     # arquitetura, decisão de modelo, deployment
├── prompts/                  # system + 4 sub-prompts (.md)
├── tools/                    # tools_spec.json (5 tools)
├── knowledge_base/           # 7 documentos .md (PT-BR, 800–1500 palavras cada)
├── evals/                    # eval set + runner LLM-as-a-judge
├── notebooks/                # PoC interativa Colab (13 seções)
├── data/mocks/               # 4 mocks JSON
├── logs/                     # audit log estruturado (gitignored)
├── ollama/                   # Modelfile + README on-prem (uso fora do Colab)
└── src/
    ├── llm/                  # qwen_client + ollama_client
    ├── agents/               # router, checkup, triagem, prescricao, safety
    ├── tools/                # 5 implementações Python
    ├── rag/                  # indexer + retriever + reranker (interface)
    ├── graph.py              # StateGraph LangGraph
    └── audit_log.py          # logging JSON estruturado
```

## Roadmap das próximas sprints

| Sprint | Entregas previstas |
|---|---|
| Sprint 2 | Integração com base de bulas oficial (ANVISA), reranker Qwen3-Reranker ativado, knowledge base expandida |
| Sprint 3 | Piloto com 200 beneficiários reais, dashboard de qualidade clínica, integração com prontuário Care Plus |
| Sprint 4 | Decisão entre cloud privada e on-prem definitivo, fine-tuning leve em protocolos Care Plus |
| Sprint 5 | Rollout completo, com ambos backends em produção, monitoramento clínico contínuo |

## Licença e disclaimers

- Código sob **Apache 2.0**.
- Conteúdo da knowledge base é **didático e original**, elaborado para
  fins acadêmicos. Não substitui a bula oficial autorizada pela ANVISA
  nem protocolos institucionais.
- Mocks claramente identificáveis (sobrenome "Fictício", IDs
  `BENEF-XXX`).
- O sistema é **acadêmico e demonstrativo**. Em produção, exigiria
  homologação clínica, parecer jurídico LGPD/CFM, certificação SBIS e
  contrato de processamento de dados.
- O assistente **nunca substitui** avaliação médica. Em emergência,
  **ligue 192 (SAMU)** ou vá ao pronto-socorro mais próximo. Em crise
  emocional, **ligue 188 (CVV)**.
