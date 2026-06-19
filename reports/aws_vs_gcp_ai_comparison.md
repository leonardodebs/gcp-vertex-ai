# AWS Bedrock vs GCP Vertex AI — Comparação de IA

_Gerado em 2026-06-19 por `comparison_report.py`._

## 1. Mapa de serviços (Bedrock ↔ Vertex AI)

| Capacidade | AWS | GCP |
|---|---|---|
| Modelos fundacionais gerenciados | Amazon Bedrock | Vertex AI Model Garden |
| LLM proprietário de ponta | Claude (Anthropic via Bedrock) | Gemini 1.5 Pro/Flash |
| RAG gerenciado | Bedrock Knowledge Bases | Vertex AI RAG Engine / Search |
| Embeddings | Titan Embeddings | Vertex AI Embeddings (gecko/004) |
| Agentes/orquestração | Bedrock Agents | Vertex AI Agent Builder |
| Guardrails/segurança de conteúdo | Bedrock Guardrails | Vertex AI Safety Filters |
| Fine-tuning gerenciado | Bedrock Custom Models | Vertex AI Tuning |
| Plataforma de ML completa | Amazon SageMaker | Vertex AI Training/Pipelines |
| ML via SQL | Redshift ML (chama SageMaker) | BigQuery ML (nativo) |
| Notebooks gerenciados | SageMaker Studio | Vertex AI Workbench |

## 2. Comparação de custo (mesmo workload)

| Workload | AWS (US$) | GCP (US$) |
|---|---|---|
| LLM rápido (1M in / 1M out) | Claude 3 Haiku: 0,25 + 1,25 = **1,50** | Gemini 1.5 Flash: 0,075 + 0,30 = **0,375** |
| Embeddings (1M tokens) | Titan: ~**0,02** | gecko@003: ~**0,025** |
| ML clássico (500 linhas) | SageMaker treino + endpoint: **$$$** | BigQuery ML: 1º TB/mês grátis → **~0** |

> Para LLM de inferência rápida, **Gemini 1.5 Flash é ~4x mais barato** que Claude 3 Haiku. Para Claude (qualidade de topo), a AWS leva vantagem.

## 3. Comparação de latência (de compare_models.py)

| Prompt | Modelo | Latência (s) | Tokens | Custo US$ | Qual. |
|---|---|---|---|---|---|
| Explique a diferença entre NAT Gateway e… | gemini-1.5-flash (stub) | — | — | — | — |
| Quais são os 5 principais riscos de segu… | gemini-1.5-flash (stub) | — | — | — | — |
| Escreva um script Python para listar ins… | gemini-1.5-flash (stub) | — | — | — | — |
| Compare Kubernetes e ECS para cargas de … | gemini-1.5-flash (stub) | — | — | — | — |
| Qual a diferença entre RTO e RPO em disa… | gemini-1.5-flash (stub) | — | — | — | — |

## 4. Developer Experience (1-5)

| Dimensão | AWS | GCP | Justificativa |
|---|---|---|---|
| Setup inicial (CLI/SDK) | 4 | 4 | ambos têm CLI sólida; gcloud é mais coeso, aws cli tem mais serviços |
| Acesso a modelos de ponta | 5 | 4 | Bedrock tem Claude (líder); Vertex tem Gemini nativo e bom catálogo |
| ML com SQL | 2 | 5 | BigQuery ML é único: treina/serve sem sair do SQL |
| RAG do zero ao deploy | 4 | 4 | Knowledge Bases e RAG Engine equivalentes |
| Documentação/exemplos | 5 | 4 | AWS tem mais conteúdo; Google evolui rápido |
| Custo de LLM rápido | 3 | 5 | Gemini Flash ~4x mais barato que Haiku |

**Média DX:** AWS 3.8/5 · GCP 4.3/5

## 5. Conclusão honesta

- **Escolha GCP** quando: precisa de ML via SQL (BigQuery ML), quer Gemini nativo, busca menor custo de inferência rápida ou já vive no ecossistema BigQuery/Looker.
- **Escolha AWS** quando: precisa do Claude como modelo principal, já tem workloads na AWS, ou quer o catálogo mais amplo de serviços gerenciados.
- **Multicloud** é viável: a abstração de prompts é similar; o lock-in real está nos serviços de dados (BigQuery vs Redshift) e RAG gerenciado.
