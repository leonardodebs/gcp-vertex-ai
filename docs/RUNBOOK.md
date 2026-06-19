# Runbook Operacional — GCP Vertex AI Lab

Procedimentos de setup, operação do dia a dia e troubleshooting.

## 1. Setup inicial

### Pré-requisitos
- Python 3.12+
- Conta GCP com o **Free Trial (US$ 300)** e um projeto criado
- `gcloud` CLI instalado
- (opcional) credenciais AWS, só para comparar com o Claude 3 Haiku no Bedrock

### Passos
```bash
# 1. Autenticar e selecionar o projeto
gcloud auth login
gcloud config set project SEU_PROJECT_ID
gcloud auth application-default login        # credenciais p/ os SDKs Python

# 2. Habilitar as APIs necessárias
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com

# 3. Ambiente Python
python3 -m venv .venv && source .venv/bin/activate
make install                                 # pip install -r requirements.txt

# 4. Configurar variáveis (ver docs/VARIAVEIS-DE-AMBIENTE.md)
cp .env.example .env
#   edite GOOGLE_CLOUD_PROJECT (obrigatório)

# 5. Validar (sem nuvem)
make test                                     # 19 testes devem passar
```

## 2. Operações do dia a dia

### Rodar a comparação de modelos
```bash
make compare                  # Gemini (+ Claude se houver cred. AWS)
# saída: reports/model_comparison.json + tabela no terminal
```

### Consultar os runbooks via RAG
```bash
make rag Q="Como resolver erro 502 no ALB?"
```

### Treinar o classificador no BigQuery ML
```bash
make bigquery                 # CREATE MODEL → ML.EVALUATE → ML.PREDICT
```

### Gerar o relatório consolidado
```bash
make report                   # reports/aws_vs_gcp_ai_comparison.md
make all                      # compare + bigquery + report
```

### Subir o dashboard local
```bash
make serve                    # http://localhost:8000/web/
```

### Saber se está em modo real ou stub
- Tabela do `compare_models.py`: coluna **`Modo`** = `real` ou `stub`.
- RAG/BigQuery: imprimem **`[modo stub]`** em vermelho quando não alcançam a nuvem.

## 3. Troubleshooting

### 3.1 `python: command not found`
Use `python3`. O Makefile já usa `PY ?= python3`; se sobrescreveu com
`make PY=python`, remova.

### 3.2 `[modo stub] … No module named 'vertexai'`
Dependências não instaladas. Rode `make install` dentro do venv ativo.

### 3.3 `DefaultCredentialsError` / `Could not automatically determine credentials`
Falta autenticar os SDKs:
```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=SEU_PROJECT_ID
```

### 3.4 `GOOGLE_CLOUD_PROJECT não definido` (bigquery_ml)
Defina no `.env` ou exporte na sessão. O BigQuery exige o projeto explicitamente.

### 3.5 `403 … API has not been used / is disabled`
A API não foi habilitada. Rode o `gcloud services enable …` do passo 2 e aguarde
~1 min para propagar.

### 3.6 `404 … Publisher Model gemini-1.5-flash was not found` / região
O modelo pode não estar disponível na região. Mantenha `GOOGLE_CLOUD_LOCATION=us-central1`.

### 3.7 Embeddings falham com `textembedding-gecko@003`
O gecko@003 está em fim de vida. Troque no `.env`:
```bash
VERTEX_EMBED_MODEL=text-embedding-004
```

### 3.8 BigQuery: `Not found: Dataset` ou erro de location
O dataset e a tabela precisam estar na mesma região da query. Ajuste
`BQ_LOCATION` (US por padrão) ou rode `python3 src/bigquery_ml.py --location US`.

### 3.9 Dashboard: tabela vazia / "Não foi possível carregar … model_comparison.json"
1. Você abriu via `file://` — o navegador bloqueia o `fetch`. Use `make serve`.
2. O JSON ainda não existe — rode `make compare` (ou `make report`) antes.

### 3.10 GitHub Pages mostra a listagem de arquivos
O dashboard fica em `/web/`, não na raiz. Acesse `…github.io/gcp-vertex-ai/web/`.

### 3.11 Porta 8000 já em uso
```bash
make serve PY="python3 -m http.server 8080"   # ou troque a porta
```

### 3.12 Testes falhando após mudanças
```bash
make test                     # leia o --tb=short; ajuste o código ou o teste
```

### 3.13 Custos inesperados no GCP
A IA deste lab custa centavos. O risco real são recursos *ligados* (endpoints do
Vertex, instâncias do Workbench). Este projeto **não cria** nenhum — usa inferência
on-demand e FAISS local. Confira em **Billing → Reports** no console.

## 4. Verificação de integridade (health checks)

```bash
# 1. Testes passam (lógica local)
make test                     # 19 passed

# 2. Scripts rodam ao menos em stub (sem credenciais)
python3 src/comparison_report.py   # gera o .md sempre

# 3. Dashboard serve e carrega o JSON
make serve                    # abra /web/ e confira a tabela

# 4. CI verde no GitHub
#    https://github.com/leonardodebs/gcp-vertex-ai/actions
```

## 5. Limpeza

```bash
make clean                    # remove reports/*.json e *.md gerados

# BigQuery: remover o dataset criado (evita qualquer storage residual)
bq rm -r -f -d SEU_PROJECT_ID:alerts_dataset
```
