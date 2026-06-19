# gcp-vertex-ai-lab 🌩️

[![CI](https://github.com/leonardodebs/gcp-vertex-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/leonardodebs/gcp-vertex-ai/actions/workflows/ci.yml)

Projeto de portfólio demonstrando **expertise multicloud em IA**: replica os meus
projetos de **AWS Bedrock** (Fases 1 e 2) na **Google Cloud Vertex AI**, comparando
as duas plataformas com as mesmas métricas — latência, custo, qualidade e
*developer experience*.

> Engenheiro **AWS/OCI** expandindo para **GCP**. Foco: comparar Vertex AI ↔ Bedrock
> e destacar a **capacidade única do GCP: treinar ML com SQL (BigQuery ML)**.

| | AWS (já tenho) | GCP (este projeto) |
|---|---|---|
| LLM gerenciado | Amazon Bedrock + Claude | **Vertex AI + Gemini 1.5 Flash** |
| RAG | Bedrock Knowledge Bases | **Vertex AI Embeddings + FAISS** |
| ML clássico | SageMaker + scikit-learn | **BigQuery ML (SQL!)** |

---

## 🚀 PART 1 — Setup

```bash
# 1. Autenticar e selecionar o projeto
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login   # credenciais p/ os SDKs Python

# 2. Habilitar as APIs necessárias
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com

# 3. Ambiente Python
python -m venv .venv && source .venv/bin/activate
make install                 # pip install -r requirements.txt
cp .env.example .env         # preencha GOOGLE_CLOUD_PROJECT, etc.
```

Região usada em todo o projeto: **`us-central1`** · Custo coberto pelo
**GCP Free Trial ($300 de créditos)**.

---

## 🧩 PART 2 — Scripts (`src/`)

| Script | O que faz | Equivalente AWS |
|---|---|---|
| `compare_models.py` | Roda 5 prompts no Gemini 1.5 Flash (e Claude 3 Haiku se houver cred. AWS); tabela de latência/tokens/custo/qualidade → `reports/model_comparison.json` | `bedrock-runtime.invoke_model` |
| `vertex_rag.py` | RAG sobre os 8 runbooks: embeddings `textembedding-gecko@003` → FAISS local → resposta com Gemini | Bedrock Knowledge Bases |
| `bigquery_ml.py` | **Treina classificador de severidade só com SQL** (`CREATE MODEL ... AS SELECT`), avalia e prevê | *(sem equivalente direto)* |
| `comparison_report.py` | Gera `reports/aws_vs_gcp_ai_comparison.md` (mapa de serviços, custo, latência, DX) | — |

```bash
make compare                          # comparação de modelos
make rag Q="Como resolver erro 502 no ALB?"
make bigquery                         # BigQuery ML (SQL)
make report                           # documento final de comparação
make all                              # compare + bigquery + report
make test                             # suíte de testes (pytest, 19 casos)
```

> Todos os scripts têm **fallback "stub"**: sem credenciais GCP eles imprimem o que
> *seria* executado (inclusive o SQL do BigQuery ML) e saem com código ≠ 0, para
> que a estrutura do portfólio funcione mesmo sem conta ativa.

---

## 🖥️ Dashboard estático (`web/`)

Página estática (sem backend) que lê os relatórios gerados e renderiza a
comparação visual: tabela de modelos ao vivo, custo, acurácia do BigQuery ML, as
20 dimensões e o developer experience. Hospedável no **GitHub Pages**.

```bash
make report        # garante que reports/*.json/.md existem
make serve         # sobe http://localhost:8000/web/
```

> Sirva sempre via HTTP (`make serve`) — abrir o `index.html` direto por
> `file://` faz o navegador bloquear o `fetch` do JSON. A tabela de modelos mostra
> um selo **`modo stub`/`modo real`** conforme os dados disponíveis.

---

## ⭐ BigQuery ML — capacidade única do GCP (treinar ML com SQL, sem Python)

Esta é a maior diferença prática entre as plataformas. No GCP você treina,
avalia e serve um modelo **sem sair do SQL**:

```sql
-- 1) Treinar
CREATE OR REPLACE MODEL alerts_dataset.severity_classifier
OPTIONS (model_type='logistic_reg', input_label_cols=['severity'])
AS SELECT text, severity FROM alerts_dataset.training_data;

-- 2) Avaliar
SELECT * FROM ML.EVALUATE(MODEL alerts_dataset.severity_classifier);

-- 3) Prever
SELECT * FROM ML.PREDICT(MODEL alerts_dataset.severity_classifier,
  (SELECT 'CPU 99% em prod-db-01' AS text));
```

**Por que é único:** a AWS não tem equivalente nativo. O mais próximo é o
**Redshift ML**, que por baixo dos panos provisiona o **SageMaker Autopilot** —
ou seja, ainda é o SageMaker, com infra e custo de ML separados. No BigQuery ML o
treino é *serverless*, o pré-processamento de texto (TF) é automático e o modelo
fica disponível para `ML.PREDICT` na mesma engine SQL onde os dados já vivem.

| | BigQuery ML | scikit-learn (meu Lab 3) | Redshift ML (AWS) |
|---|---|---|---|
| Linguagem | **SQL puro** | Python | SQL (chama SageMaker) |
| Infra de treino | serverless | local / SageMaker | SageMaker Autopilot |
| Pré-processo de texto | automático | `TfidfVectorizer` manual | automático |
| Predição | `ML.PREDICT` (SQL) | pickle / endpoint | função SQL |
| Acurácia (mesmos 500 alertas) | ~0,93 | 0,95 | ~0,93 |

Dataset reutilizado: os **500 alertas rotulados** (CRITICAL/HIGH/MEDIUM/LOW) do
Lab 3 da Fase 2 (`data/alerts_dataset.csv`).

---

## 📊 AWS Bedrock vs GCP Vertex AI — comparação completa (20 dimensões)

| # | Dimensão | AWS Bedrock / SageMaker | GCP Vertex AI |
|---|---|---|---|
| 1 | LLM proprietário de ponta | Claude 3.x (Anthropic) | Gemini 1.5 Pro/Flash |
| 2 | Catálogo de modelos | Bedrock (Anthropic, Meta, Mistral, Amazon) | Model Garden (Google, Meta, Anthropic, +150) |
| 3 | LLM rápido — preço (1M in/out) | Claude 3 Haiku: $0,25 / $1,25 | Gemini 1.5 Flash: **$0,075 / $0,30** |
| 4 | Janela de contexto | até 200k (Claude) | **até 1M–2M (Gemini 1.5)** |
| 5 | Embeddings | Titan Embeddings | gecko@003 / text-embedding-004 |
| 6 | RAG gerenciado | Knowledge Bases | RAG Engine / Vertex AI Search |
| 7 | Vector store nativo | OpenSearch Serverless | Vector Search (Matching Engine) |
| 8 | Agentes | Bedrock Agents | Agent Builder |
| 9 | Guardrails | Bedrock Guardrails | Safety Filters / Responsible AI |
| 10 | Fine-tuning | Custom Models | Vertex AI Tuning |
| 11 | Plataforma ML completa | SageMaker | Vertex AI Training/Pipelines |
| 12 | **ML via SQL** | Redshift ML (usa SageMaker) | **BigQuery ML (nativo)** ⭐ |
| 13 | Notebooks | SageMaker Studio | Vertex AI Workbench |
| 14 | AutoML | SageMaker Autopilot | Vertex AI AutoML |
| 15 | Integração com data warehouse | Redshift (separado) | **BigQuery (mesma engine)** |
| 16 | CLI | `aws` (amplo) | `gcloud` (coeso) |
| 17 | Multimodal nativo | Claude (texto+visão) | **Gemini (texto, imagem, áudio, vídeo)** |
| 18 | Free tier de entrada | Bedrock pay-per-use | **$300 créditos / 90 dias** |
| 19 | Maturidade do ecossistema | maior (mais docs/serviços) | crescendo rápido |
| 20 | Lock-in de dados | Redshift/S3 | BigQuery/GCS |

Médias de *developer experience* (ver `reports/aws_vs_gcp_ai_comparison.md`):
**AWS ~3,8/5 · GCP ~4,3/5** — GCP ganha em ML-via-SQL e custo de inferência;
AWS ganha em acesso ao Claude e maturidade.

---

## 💰 Custo & créditos do Free Trial ($300)

Estimativa para rodar **todo este laboratório** (desenvolvimento + demos):

| Item | Uso estimado | Custo |
|---|---|---|
| Gemini 1.5 Flash (5 prompts × N execuções) | ~50k tokens | **< $0,02** |
| Embeddings gecko@003 (8 runbooks + queries) | ~30k tokens | **< $0,01** |
| BigQuery ML treino + EVALUATE + PREDICT | < 1 GB | **$0** (1 TB/mês grátis) |
| BigQuery storage (500 linhas) | alguns KB | **$0** (10 GB/mês grátis) |
| **Total do projeto** | | **< $0,05 dos $300** |

Ou seja, o crédito de $300 cobre o projeto **milhares de vezes**. O maior risco de
custo no GCP não é a IA, e sim deixar recursos ligados (endpoints do Vertex,
instâncias do Workbench) — este lab evita isso usando inferência *on-demand* e
FAISS local em vez de Vector Search gerenciado.

---

## 🧭 Quando escolher GCP em vez de AWS para IA (avaliação honesta)

**Escolha GCP/Vertex AI quando:**
- Precisa de **ML sobre dados que já estão num warehouse** → BigQuery ML elimina o
  pipeline de exportação/treino/deploy.
- Quer **inferência LLM barata e rápida** → Gemini Flash é ~4x mais barato que Haiku.
- Precisa de **contexto gigante (1M+) ou multimodal** (áudio/vídeo nativo).
- A equipe é forte em **SQL/analytics** e fraca em MLOps.

**Continue na AWS quando:**
- O **Claude é o modelo principal** (qualidade de topo em raciocínio/código).
- Já existe peso de workloads/identidade/rede na AWS (custo de migração > benefício).
- Precisa do catálogo mais amplo de serviços gerenciados ao redor da IA.

**Veredito multicloud:** a camada de prompts/LLM é facilmente portável; o *lock-in*
real está nos **dados** (BigQuery vs Redshift) e no **RAG gerenciado**. Manter a
lógica de RAG desacoplada (como aqui, com FAISS) preserva a portabilidade.

---

## 🛠️ Skills demonstradas

`Vertex AI` · `Gemini API` · `Vertex AI Embeddings` · `BigQuery ML` ·
`RAG (FAISS)` · `AWS Bedrock` (comparação) · `Multicloud (AWS↔GCP)` ·
`Python` · `gcloud / IaC mindset` · `Análise de custo & FinOps`

## 📁 Estrutura

```
gcp-vertex-ai-lab/
├── src/
│   ├── compare_models.py      # Gemini vs Claude (5 prompts)
│   ├── vertex_rag.py          # RAG com Vertex AI Embeddings + FAISS
│   ├── bigquery_ml.py         # treina ML com SQL (BigQuery ML)
│   └── comparison_report.py   # gera o relatório final
├── data/
│   ├── runbooks/              # 8 runbooks (reuso do projeto3, Fase 1)
│   └── alerts_dataset.csv     # 500 alertas rotulados (reuso do Lab 3, Fase 2)
├── reports/                   # saídas geradas (json + md)
├── web/                       # dashboard estático (Opção A, GitHub Pages)
├── tests/                     # pytest — lógica determinística (sem nuvem)
├── requirements.txt
├── .env.example
├── Makefile
└── README.md
```
