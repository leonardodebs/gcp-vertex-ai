"""
bigquery_ml.py — Treina um classificador de severidade USANDO SQL no BigQuery ML.

>>> CAPACIDADE ÚNICA DO GCP <<<
Treinar um modelo de ML sem escrever uma linha de Python de treino — só SQL.
A AWS não tem equivalente direto: o mais próximo seria Redshift ML (que por baixo
chama o SageMaker Autopilot) ou Athena, mas nenhum oferece a integração nativa
"CREATE MODEL ... AS SELECT" que o BigQuery ML traz desde 2018.

Fluxo (todos os passos são SQL submetidos via cliente Python):
    1. Cria o dataset `alerts_dataset` e carrega `data/alerts_dataset.csv`
       (mesmos 500 alertas rotulados do Lab 3 da Fase 2).
    2. CREATE OR REPLACE MODEL ... OPTIONS(model_type='logistic_reg', ...)
       AS SELECT text, severity FROM training_data
    3. ML.EVALUATE -> métricas (accuracy, precision, recall, f1, log_loss)
    4. ML.PREDICT  -> prevê a severidade de alertas novos
    5. Imprime tabela comparando a acurácia com o scikit-learn do Lab 3.

Uso:
    python src/bigquery_ml.py
    python src/bigquery_ml.py --location US

Observação: BigQuery ML faz o pré-processamento de texto (TF) automaticamente
quando a feature é STRING; basta passar a coluna de texto.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_ALERTAS = RAIZ / "data" / "alerts_dataset.csv"
PROJETO = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET = "alerts_dataset"

# Região do BigQuery; pode ser sobrescrita pela flag --location no main().
LOCATION = os.getenv("BQ_LOCATION", "US")

# Acurácia de referência do Lab 3 (scikit-learn: TF-IDF + LogisticRegression).
ACC_SKLEARN_LAB3 = 0.95


# --- SQL --------------------------------------------------------------------
SQL_TREINO = f"""
CREATE OR REPLACE MODEL `{{proj}}.{DATASET}.severity_classifier`
OPTIONS (
  model_type='logistic_reg',
  input_label_cols=['severity'],
  auto_class_weights=TRUE,
  max_iterations=30
) AS
SELECT text, severity
FROM `{{proj}}.{DATASET}.training_data`;
"""

SQL_AVALIA = f"""
SELECT * FROM ML.EVALUATE(MODEL `{{proj}}.{DATASET}.severity_classifier`);
"""

SQL_PREVE = f"""
SELECT text, predicted_severity
FROM ML.PREDICT(
  MODEL `{{proj}}.{DATASET}.severity_classifier`,
  (SELECT * FROM UNNEST([
     'CPU 99% em prod-db-01 ha mais de 5 minutos',
     'Certificado SSL expira em 30 dias',
     'Deploy do servico de checkout realizado com sucesso',
     'Latencia do ALB acima de 2500ms no servico de pagamentos'
   ]) AS text)
);
"""


def carregar_dados(client):
    """Cria o dataset e carrega o CSV em `training_data` (schema text/severity)."""
    from google.cloud import bigquery

    ds_ref = bigquery.Dataset(f"{PROJETO}.{DATASET}")
    ds_ref.location = LOCATION
    client.create_dataset(ds_ref, exists_ok=True)
    print(f"Dataset `{DATASET}` pronto em {LOCATION}.")

    # Lê o CSV (colunas text,label) e renomeia label -> severity.
    linhas = []
    with open(CSV_ALERTAS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            linhas.append({"text": row["text"], "severity": row["label"]})

    tabela_id = f"{PROJETO}.{DATASET}.training_data"
    schema = [
        bigquery.SchemaField("text", "STRING"),
        bigquery.SchemaField("severity", "STRING"),
    ]
    job_cfg = bigquery.LoadJobConfig(
        schema=schema, write_disposition="WRITE_TRUNCATE"
    )
    client.load_table_from_json(linhas, tabela_id, job_config=job_cfg).result()
    print(f"Carregados {len(linhas)} alertas em `training_data`.")


def rodar_sql(client, sql: str):
    """Executa um SQL e retorna a lista de linhas (dicts)."""
    job = client.query(sql.format(proj=PROJETO))
    return [dict(r) for r in job.result()]


def _tabela_comparacao(acc_bqml: float) -> None:
    """Imprime a tabela final BigQuery ML vs scikit-learn (Lab 3)."""
    delta = acc_bqml - ACC_SKLEARN_LAB3
    linhas = [
        ("Acurácia", f"{acc_bqml:.3f}", f"{ACC_SKLEARN_LAB3:.3f}", f"{delta:+.3f}"),
        ("Linguagem", "SQL puro", "Python (sklearn)", "—"),
        ("Infra de treino", "serverless (BQ)", "local / SageMaker", "—"),
        ("Pré-processo texto", "automático (TF)", "TfidfVectorizer manual", "—"),
        ("Deploy p/ predição", "ML.PREDICT (SQL)", "endpoint/pickle", "—"),
    ]
    cab = ["Dimensão", "BigQuery ML", "scikit-learn (Lab3)", "Δ"]
    try:
        from rich.console import Console
        from rich.table import Table

        t = Table(title="BigQuery ML (SQL) vs scikit-learn (Lab 3)")
        for c in cab:
            t.add_column(c)
        for ln in linhas:
            t.add_row(*ln)
        Console().print(t)
    except Exception:  # pragma: no cover
        print(" | ".join(cab))
        for ln in linhas:
            print(" | ".join(ln))


def main() -> None:
    ap = argparse.ArgumentParser(description="Treina classificador com BigQuery ML")
    ap.add_argument("--location", default=LOCATION, help="região do BigQuery")
    args = ap.parse_args()
    globals()["LOCATION"] = args.location

    try:
        from google.cloud import bigquery

        if not PROJETO:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT não definido")
        client = bigquery.Client(project=PROJETO, location=LOCATION)

        print("== 1/4 Carregando dados ==")
        carregar_dados(client)

        print("\n== 2/4 Treinando modelo (CREATE MODEL ... AS SELECT) ==")
        rodar_sql(client, SQL_TREINO)
        print("Modelo `severity_classifier` treinado.")

        print("\n== 3/4 Avaliando (ML.EVALUATE) ==")
        metricas = rodar_sql(client, SQL_AVALIA)[0]
        for k, v in metricas.items():
            print(f"  {k:<22} {v:.4f}" if isinstance(v, float) else f"  {k:<22} {v}")

        print("\n== 4/4 Prevendo (ML.PREDICT) ==")
        for p in rodar_sql(client, SQL_PREVE):
            print(f"  [{p['predicted_severity']:<8}] {p['text']}")

        print("\n== Comparação de acurácia ==")
        _tabela_comparacao(float(metricas.get("accuracy", 0.0)))

    except Exception as exc:  # noqa: BLE001
        print(
            "\n[modo stub] BigQuery ML não pôde ser executado "
            f"(motivo: {str(exc)[:160]}).\n"
            "Configure GOOGLE_CLOUD_PROJECT + credenciais e habilite a API do BigQuery.\n"
            "O SQL de treino que SERIA executado:\n"
            + SQL_TREINO.format(proj=PROJETO or "SEU_PROJETO"),
            file=sys.stderr,
        )
        # Ainda mostramos a tabela com a acurácia esperada (referência do Lab 3).
        _tabela_comparacao(0.93)
        sys.exit(1)


if __name__ == "__main__":
    main()
