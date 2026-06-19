# Exemplos de Variáveis de Ambiente — GCP Vertex AI Lab

## Como usar

```bash
# 1. Copie o template versionado
cp .env.example .env

# 2. Edite e preencha pelo menos GOOGLE_CLOUD_PROJECT
#    (as demais têm padrões sensatos)

# 3. Rode normalmente — o Makefile carrega o .env automaticamente
make compare
```

> O `.env` está no `.gitignore` e **nunca** deve ser versionado. Apenas o
> `.env.example` (sem segredos) vai para o repositório.

## Variáveis

### Obrigatória
| Variável | Descrição |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | ID do projeto GCP onde os modelos e o BigQuery rodam |

### Opcionais (têm valor padrão)
| Variável | Padrão | Descrição |
|---|---|---|
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Região do Vertex AI (Gemini/Embeddings) |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Caminho do JSON da service account (se não usar ADC) |
| `BQ_LOCATION` | `US` | Região do dataset/queries do BigQuery |
| `VERTEX_EMBED_MODEL` | `textembedding-gecko@003` | Modelo de embeddings do RAG |

### AWS Bedrock (opcionais — só para comparar com o Claude 3 Haiku)
| Variável | Padrão | Descrição |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | — | Habilita a chamada ao Bedrock no `compare_models.py` |
| `AWS_SECRET_ACCESS_KEY` | — | Par da chave acima |
| `AWS_DEFAULT_REGION` | `us-east-1` | Região do Bedrock |

## Template completo (`.env`)

```bash
# === GCP (obrigatório) ===
GOOGLE_CLOUD_PROJECT=seu-project-id
GOOGLE_CLOUD_LOCATION=us-central1
# Caminho do JSON da service account (gcloud iam service-accounts keys create ...)
# Alternativa recomendada: usar ADC (gcloud auth application-default login) e omitir.
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
# Região do BigQuery (US ou us-central1)
BQ_LOCATION=US
# Modelo de embeddings do Vertex AI (gecko@003 ou text-embedding-004)
VERTEX_EMBED_MODEL=textembedding-gecko@003

# === AWS Bedrock (opcional — comparação Claude 3 Haiku) ===
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_key_here
AWS_DEFAULT_REGION=us-east-1
```

## Autenticação: ADC vs Service Account

Há duas formas de autenticar os SDKs Python da Google:

1. **ADC (recomendado p/ dev local)** — `gcloud auth application-default login`.
   Não precisa de `GOOGLE_APPLICATION_CREDENTIALS`; deixe a variável vazia.
2. **Service Account (CI/servidores)** — crie uma chave JSON e aponte
   `GOOGLE_APPLICATION_CREDENTIALS` para ela:
   ```bash
   gcloud iam service-accounts keys create credentials.json \
     --iam-account=NOME@SEU_PROJECT_ID.iam.gserviceaccount.com
   ```

## Notas de segurança

- **Nunca** versione `.env`, `credentials.json` ou qualquer chave — já cobertos
  pelo `.gitignore` (`.env`, `credentials*.json`).
- Conceda à service account apenas os papéis mínimos: `roles/aiplatform.user` e
  `roles/bigquery.user` (+ `bigquery.dataEditor` para criar o dataset).
- As variáveis AWS são opcionais; sem elas, o `compare_models.py` roda só o Gemini.

## Diferenças por ambiente

| Ambiente | Autenticação | Observação |
|---|---|---|
| Dev local | ADC (`application-default login`) | mais simples; sem arquivo de chave |
| CI (GitHub Actions) | nenhuma | os testes não tocam a nuvem; só `pytest` |
| Execução real em servidor | Service Account JSON | use `GOOGLE_APPLICATION_CREDENTIALS` |
