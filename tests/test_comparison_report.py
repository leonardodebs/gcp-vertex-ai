"""Testes da geração do relatório final (comparison_report)."""
import json

import comparison_report as cr


def test_mapa_servicos_tem_dez_pares():
    """O mapa de serviços Bedrock<->Vertex deve ter 10 entradas (cap, aws, gcp)."""
    assert len(cr.MAPA_SERVICOS) == 10
    for linha in cr.MAPA_SERVICOS:
        assert len(linha) == 3


def test_ler_latencias_sem_arquivo(tmp_path, monkeypatch):
    """Sem o JSON de comparação, a seção de latência traz aviso amigável."""
    monkeypatch.setattr(cr, "JSON_COMP", tmp_path / "inexistente.json")
    texto = cr._ler_latencias()
    assert "Sem dados" in texto


def test_ler_latencias_com_arquivo(tmp_path, monkeypatch):
    """Com JSON válido, monta a tabela markdown com os modelos."""
    fake = {
        "resultados": [
            {
                "prompt": "Pergunta de teste sobre infraestrutura na nuvem",
                "modelos": [
                    {
                        "modelo": "gemini-1.5-flash",
                        "modo": "real",
                        "latencia_s": 0.42,
                        "tokens_total": 123,
                        "custo_usd": 0.000045,
                        "qualidade": 5,
                    }
                ],
            }
        ]
    }
    arq = tmp_path / "model_comparison.json"
    arq.write_text(json.dumps(fake), encoding="utf-8")
    monkeypatch.setattr(cr, "JSON_COMP", arq)

    texto = cr._ler_latencias()
    assert "gemini-1.5-flash" in texto
    assert "| Prompt | Modelo |" in texto


def test_gerar_escreve_relatorio(tmp_path, monkeypatch):
    """gerar() cria o arquivo .md com as seções esperadas."""
    saida = tmp_path / "aws_vs_gcp_ai_comparison.md"
    monkeypatch.setattr(cr, "REPORTS", tmp_path)
    monkeypatch.setattr(cr, "SAIDA", saida)
    monkeypatch.setattr(cr, "JSON_COMP", tmp_path / "inexistente.json")

    cr.gerar()

    conteudo = saida.read_text(encoding="utf-8")
    assert "# AWS Bedrock vs GCP Vertex AI" in conteudo
    assert "Mapa de serviços" in conteudo
    assert "Developer Experience" in conteudo
