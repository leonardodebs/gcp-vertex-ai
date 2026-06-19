"""Testes dos templates SQL e constantes do bigquery_ml (sem chamar o BigQuery)."""
import bigquery_ml as bq


def test_sql_treino_usa_create_model_e_logistic_reg():
    """O SQL de treino deve declarar CREATE MODEL com regressão logística."""
    sql = bq.SQL_TREINO.format(proj="meu-proj")
    assert "CREATE OR REPLACE MODEL" in sql
    assert "logistic_reg" in sql
    assert "input_label_cols=['severity']" in sql
    assert "meu-proj.alerts_dataset.severity_classifier" in sql


def test_sql_avalia_e_preve_chamam_funcoes_ml():
    """ML.EVALUATE e ML.PREDICT devem aparecer nos respectivos templates."""
    assert "ML.EVALUATE" in bq.SQL_AVALIA.format(proj="p")
    assert "ML.PREDICT" in bq.SQL_PREVE.format(proj="p")


def test_templates_sql_formatam_sem_chaves_remanescentes():
    """Após .format(proj=...) não pode sobrar placeholder `{` não resolvido."""
    for sql in (bq.SQL_TREINO, bq.SQL_AVALIA, bq.SQL_PREVE):
        resultado = sql.format(proj="x")
        assert "{proj}" not in resultado


def test_acuracia_referencia_lab3():
    """A acurácia de referência do scikit-learn (Lab 3) é um valor plausível."""
    assert 0.0 < bq.ACC_SKLEARN_LAB3 <= 1.0
