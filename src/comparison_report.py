"""
comparison_report.py — Gera o documento final de comparação AWS x GCP.

Lê reports/model_comparison.json (se existir, produzido por compare_models.py) e
escreve reports/aws_vs_gcp_ai_comparison.md com:
    - Mapa de serviços Bedrock <-> Vertex AI (10 serviços)
    - Comparação de custo do mesmo workload em cada plataforma
    - Comparação de latência a partir dos resultados do compare_models.py
    - Avaliação de developer experience (1-5) com justificativa

Uso:
    python src/comparison_report.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPORTS = RAIZ / "reports"
JSON_COMP = REPORTS / "model_comparison.json"
SAIDA = REPORTS / "aws_vs_gcp_ai_comparison.md"

# Mapa de serviços equivalentes (10 pares) AWS Bedrock/IA  <->  GCP Vertex AI.
MAPA_SERVICOS = [
    ("Modelos fundacionais gerenciados", "Amazon Bedrock", "Vertex AI Model Garden"),
    ("LLM proprietário de ponta", "Claude (Anthropic via Bedrock)", "Gemini 1.5 Pro/Flash"),
    ("RAG gerenciado", "Bedrock Knowledge Bases", "Vertex AI RAG Engine / Search"),
    ("Embeddings", "Titan Embeddings", "Vertex AI Embeddings (gecko/004)"),
    ("Agentes/orquestração", "Bedrock Agents", "Vertex AI Agent Builder"),
    ("Guardrails/segurança de conteúdo", "Bedrock Guardrails", "Vertex AI Safety Filters"),
    ("Fine-tuning gerenciado", "Bedrock Custom Models", "Vertex AI Tuning"),
    ("Plataforma de ML completa", "Amazon SageMaker", "Vertex AI Training/Pipelines"),
    ("ML via SQL", "Redshift ML (chama SageMaker)", "BigQuery ML (nativo)"),
    ("Notebooks gerenciados", "SageMaker Studio", "Vertex AI Workbench"),
]

# Custo de referência do mesmo workload (1M tokens entrada + 1M saída) — US$.
CUSTO_WORKLOAD = [
    ("LLM rápido (1M in / 1M out)", "Claude 3 Haiku: 0,25 + 1,25 = **1,50**",
     "Gemini 1.5 Flash: 0,075 + 0,30 = **0,375**"),
    ("Embeddings (1M tokens)", "Titan: ~**0,02**", "gecko@003: ~**0,025**"),
    ("ML clássico (500 linhas)", "SageMaker treino + endpoint: **$$$**",
     "BigQuery ML: 1º TB/mês grátis → **~0**"),
]

# Developer experience (1-5) por dimensão, com justificativa.
DX = [
    ("Setup inicial (CLI/SDK)", 4, 4,
     "ambos têm CLI sólida; gcloud é mais coeso, aws cli tem mais serviços"),
    ("Acesso a modelos de ponta", 5, 4,
     "Bedrock tem Claude (líder); Vertex tem Gemini nativo e bom catálogo"),
    ("ML com SQL", 2, 5,
     "BigQuery ML é único: treina/serve sem sair do SQL"),
    ("RAG do zero ao deploy", 4, 4, "Knowledge Bases e RAG Engine equivalentes"),
    ("Documentação/exemplos", 5, 4, "AWS tem mais conteúdo; Google evolui rápido"),
    ("Custo de LLM rápido", 3, 5, "Gemini Flash ~4x mais barato que Haiku"),
]


def _ler_latencias() -> str:
    """Monta a seção de latência a partir do JSON do compare_models.py."""
    if not JSON_COMP.exists():
        return ("_Sem dados — rode `make compare` para gerar "
                "reports/model_comparison.json._\n")
    dados = json.loads(JSON_COMP.read_text(encoding="utf-8"))
    linhas = ["| Prompt | Modelo | Latência (s) | Tokens | Custo US$ | Qual. |",
              "|---|---|---|---|---|---|"]
    for item in dados["resultados"]:
        for m in item["modelos"]:
            lat = m["latencia_s"] if m["latencia_s"] is not None else "—"
            tok = m["tokens_total"] if m["tokens_total"] is not None else "—"
            cus = f'{m["custo_usd"]:.6f}' if m["custo_usd"] is not None else "—"
            qua = m["qualidade"] if m["qualidade"] is not None else "—"
            linhas.append(
                f'| {item["prompt"][:40]}… | {m["modelo"]} ({m["modo"]}) '
                f'| {lat} | {tok} | {cus} | {qua} |'
            )
    return "\n".join(linhas) + "\n"


def gerar() -> None:
    REPORTS.mkdir(exist_ok=True)
    p = []
    p.append(f"# AWS Bedrock vs GCP Vertex AI — Comparação de IA\n")
    p.append(f"_Gerado em {date.today().isoformat()} por `comparison_report.py`._\n")

    p.append("## 1. Mapa de serviços (Bedrock ↔ Vertex AI)\n")
    p.append("| Capacidade | AWS | GCP |")
    p.append("|---|---|---|")
    for cap, aws, gcp in MAPA_SERVICOS:
        p.append(f"| {cap} | {aws} | {gcp} |")
    p.append("")

    p.append("## 2. Comparação de custo (mesmo workload)\n")
    p.append("| Workload | AWS (US$) | GCP (US$) |")
    p.append("|---|---|---|")
    for w, aws, gcp in CUSTO_WORKLOAD:
        p.append(f"| {w} | {aws} | {gcp} |")
    p.append("\n> Para LLM de inferência rápida, **Gemini 1.5 Flash é ~4x mais barato** "
             "que Claude 3 Haiku. Para Claude (qualidade de topo), a AWS leva vantagem.\n")

    p.append("## 3. Comparação de latência (de compare_models.py)\n")
    p.append(_ler_latencias())

    p.append("## 4. Developer Experience (1-5)\n")
    p.append("| Dimensão | AWS | GCP | Justificativa |")
    p.append("|---|---|---|---|")
    for dim, a, g, just in DX:
        p.append(f"| {dim} | {a} | {g} | {just} |")
    med_a = sum(x[1] for x in DX) / len(DX)
    med_g = sum(x[2] for x in DX) / len(DX)
    p.append(f"\n**Média DX:** AWS {med_a:.1f}/5 · GCP {med_g:.1f}/5\n")

    p.append("## 5. Conclusão honesta\n")
    p.append(
        "- **Escolha GCP** quando: precisa de ML via SQL (BigQuery ML), quer Gemini "
        "nativo, busca menor custo de inferência rápida ou já vive no ecossistema "
        "BigQuery/Looker.\n"
        "- **Escolha AWS** quando: precisa do Claude como modelo principal, já tem "
        "workloads na AWS, ou quer o catálogo mais amplo de serviços gerenciados.\n"
        "- **Multicloud** é viável: a abstração de prompts é similar; o lock-in real "
        "está nos serviços de dados (BigQuery vs Redshift) e RAG gerenciado.\n"
    )

    SAIDA.write_text("\n".join(p), encoding="utf-8")
    print(f"Relatório gerado: {SAIDA}")


if __name__ == "__main__":
    gerar()
