# Makefile — gcp-vertex-ai-lab
# Carrega variáveis do .env (se existir) para os comandos.
ifneq (,$(wildcard .env))
include .env
export
endif

PY ?= python3
Q ?= Como resolver erro 502 no ALB?

.PHONY: help install compare rag bigquery report all serve test clean

help:  ## Lista os alvos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

install:  ## Instala dependências do requirements.txt
	$(PY) -m pip install -r requirements.txt

compare:  ## Compara Gemini 1.5 Flash vs Claude 3 Haiku nos 5 prompts
	$(PY) src/compare_models.py

rag:  ## RAG sobre runbooks. Uso: make rag Q="sua pergunta"
	$(PY) src/vertex_rag.py "$(Q)"

bigquery:  ## Treina classificador de severidade com BigQuery ML (SQL)
	$(PY) src/bigquery_ml.py

report:  ## Gera reports/aws_vs_gcp_ai_comparison.md
	$(PY) src/comparison_report.py

all: compare bigquery report  ## Roda comparação, BigQuery ML e relatório final

serve:  ## Sobe o dashboard estático em http://localhost:8000/web/
	@echo "Abra http://localhost:8000/web/  (Ctrl+C para parar)"
	$(PY) -m http.server 8000

test:  ## Roda a suíte de testes (pytest) — lógica determinística, sem nuvem
	$(PY) -m pytest

clean:  ## Remove relatórios gerados
	rm -f reports/model_comparison.json reports/aws_vs_gcp_ai_comparison.md
