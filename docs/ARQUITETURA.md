# Documentação de Arquitetura — GCP Vertex AI Lab

## 1. Visão geral

Projeto de portfólio que **replica na Google Cloud (Vertex AI) os experimentos de
IA já feitos na AWS (Bedrock/SageMaker)** e os compara com as mesmas métricas
(custo, latência, qualidade, developer experience).

Não é uma aplicação de produção: é um conjunto de **scripts CLI independentes**
mais um **dashboard estático** que lê os relatórios gerados. Cada script funciona
de forma autônoma e tem fallback "stub" — se não houver credenciais de nuvem, ele
imprime o que *seria* executado em vez de quebrar.

```
                 ┌──────────────────────────────────────────────┐
                 │              gcp-vertex-ai (repo)             │
                 ├──────────────────────────────────────────────┤
   data/  ──────►│  src/compare_models.py   → reports/*.json     │
 (runbooks,      │  src/vertex_rag.py       (FAISS em memória)   │
  alertas)       │  src/bigquery_ml.py      → BigQuery (SQL)     │
                 │  src/comparison_report.py→ reports/*.md       │
                 └───────────────┬──────────────────────────────┘
                                 │ lê reports/model_comparison.json
                                 ▼
                 ┌──────────────────────────────────────────────┐
                 │  web/  (dashboard estático, GitHub Pages)     │
                 └──────────────────────────────────────────────┘
```

## 2. Componentes

| Componente | Arquivo | Responsabilidade | Serviço GCP | Equivalente AWS |
|---|---|---|---|---|
| Comparador de LLMs | `src/compare_models.py` | roda 5 prompts no Gemini (e Claude opcional), mede latência/tokens/custo/qualidade | Vertex AI (Gemini) | Bedrock `invoke_model` |
| RAG | `src/vertex_rag.py` | embeddings + FAISS + geração ancorada nos runbooks | Vertex AI Embeddings + Gemini | Bedrock Knowledge Bases |
| ML via SQL | `src/bigquery_ml.py` | treina/avalia/prediz classificador de severidade | BigQuery ML | *(sem equivalente nativo)* |
| Gerador de relatório | `src/comparison_report.py` | consolida tudo em markdown | — | — |
| Dashboard | `web/` | visualização estática (lê o JSON) | GitHub Pages | — |
| Testes | `tests/` | valida a lógica determinística (pytest) | GitHub Actions (CI) | — |

### Diagrama de dependências (imports de nuvem)

Os imports pesados (`vertexai`, `faiss`, `google-cloud-bigquery`) ficam **dentro
das funções**, nunca no topo do módulo. Consequência: os módulos são importáveis
(e testáveis) sem nenhuma lib de nuvem instalada — essencial para o CI rodar com
apenas `pip install pytest`.

## 3. Fluxo — comparação de modelos

1. `compare_models.py` itera sobre os 5 `PROMPTS` (temática de infraestrutura).
2. Para cada prompt, chama `chamar_gemini()` (e `chamar_bedrock()` se houver
   `AWS_ACCESS_KEY_ID`), cada um protegido por try/except → registro padrão.
3. Métricas calculadas:
   - **latência**: `time.perf_counter()` em volta da chamada;
   - **tokens**: `usage_metadata` (Gemini) / `usage` (Bedrock);
   - **custo**: `_custo()` aplica a tabela `PRECOS` (US$/1M tokens);
   - **qualidade (1–5)**: `_qualidade()` mede cobertura de palavras-chave esperadas.
4. Resultado serializado em `reports/model_comparison.json` e renderizado em tabela.

## 4. Fluxo — RAG (`vertex_rag.py`)

1. `carregar_chunks()` lê os 8 runbooks `.md` e quebra por parágrafo (≥40 chars).
2. `embeddings_vertex()` gera vetores via `TextEmbeddingModel` (lotes de 5).
3. `construir_indice()` normaliza (L2) e cria um `IndexFlatIP` do FAISS (cosseno).
4. `buscar()` embeda a pergunta e recupera os `top_k` chunks.
5. `gerar_resposta()` monta o prompt com os contextos e chama o Gemini 1.5 Flash.

> O índice é construído **em memória a cada execução** (exemplo autocontido). Em
> produção, persistir-se-ia o índice ou usar-se-ia o Vertex AI Vector Search.

## 5. Fluxo — BigQuery ML (`bigquery_ml.py`)

1. `carregar_dados()` cria o dataset `alerts_dataset` e carrega o CSV (500 alertas)
   em `training_data` (colunas `text`, `severity`).
2. `SQL_TREINO` → `CREATE OR REPLACE MODEL ... OPTIONS(model_type='logistic_reg')`.
3. `SQL_AVALIA` → `ML.EVALUATE` (accuracy, precision, recall, f1, log_loss).
4. `SQL_PREVE` → `ML.PREDICT` sobre alertas novos.
5. `_tabela_comparacao()` confronta a acurácia com o scikit-learn do Lab 3.

## 6. Decisões de design

| Decisão | Motivo |
|---|---|
| Imports de nuvem dentro das funções | módulos testáveis sem SDKs; CI barato |
| Fallback "stub" em todo script | portfólio funciona sem conta GCP ativa |
| FAISS local em vez de Vector Search | sem custo, sem recurso ligado, reuso da Fase 1 |
| Dashboard estático (sem backend) | hospeda no GitHub Pages, zero manutenção |
| Preços em constantes (`PRECOS`) | custo estimável offline, sem chamar billing API |
| Região fixa `us-central1` | consistência e disponibilidade dos modelos |

## 7. Contratos de dados

### `reports/model_comparison.json`
```json
{
  "regiao": "us-central1",
  "bedrock_habilitado": false,
  "resultados": [
    {
      "prompt": "…",
      "modelos": [
        {
          "modelo": "gemini-1.5-flash",
          "modo": "real|stub",
          "latencia_s": 0.42, "tokens_in": 12, "tokens_out": 340,
          "tokens_total": 352, "custo_usd": 0.000045, "qualidade": 5,
          "resposta": "…"
        }
      ]
    }
  ]
}
```

### Tabela de treino do BigQuery (`alerts_dataset.training_data`)
| coluna | tipo | descrição |
|---|---|---|
| `text` | STRING | mensagem do alerta (pt-BR) |
| `severity` | STRING | rótulo: CRITICAL / HIGH / MEDIUM / LOW |

## 8. Pontos de extensão

- **Novos modelos**: adicionar entrada em `PRECOS` e uma função `chamar_*`.
- **Embeddings**: trocar `VERTEX_EMBED_MODEL` (gecko@003 → text-embedding-004).
- **Persistir índice FAISS**: salvar/recarregar `faiss.write_index` em `data/index/`.
- **RAG gerenciado**: substituir FAISS pelo Vertex AI Vector Search.
- **CD do dashboard**: migrar do Pages clássico para workflow `deploy-pages`.
