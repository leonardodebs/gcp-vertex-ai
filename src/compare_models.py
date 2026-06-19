"""
compare_models.py — Comparação lado a lado de LLMs gerenciados.

Equivalente AWS: invocar modelos via Amazon Bedrock (bedrock-runtime.invoke_model).
Aqui usamos o Vertex AI (Gemini 1.5 Flash) e, opcionalmente, o Bedrock
(Claude 3 Haiku) quando houver credenciais AWS disponíveis.

Para cada um dos 5 prompts (temática de infraestrutura) medimos:
    - latência (segundos)
    - contagem de tokens (entrada + saída)
    - custo estimado (US$) com base no preço público por 1M de tokens
    - qualidade da resposta (1-5), avaliada por heurística simples de cobertura

Saída:
    reports/model_comparison.json  -> dados crus de cada execução
    tabela lado a lado no terminal (Rich, com fallback texto puro)

Uso:
    python src/compare_models.py
    python src/compare_models.py --no-bedrock   # força só Vertex AI

Observação de design: se as bibliotecas/credenciais de nuvem não estiverem
disponíveis, o script cai em modo "stub" determinístico para que a estrutura
do relatório possa ser gerada mesmo sem conta ativa (útil em CI/portfólio).
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPORTS = RAIZ / "reports"
REGIAO = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
PROJETO = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Os 5 prompts de infraestrutura definidos no enunciado do laboratório.
PROMPTS = [
    "Explique a diferença entre NAT Gateway e Internet Gateway na AWS",
    "Quais são os 5 principais riscos de segurança em uma VPC pública?",
    "Escreva um script Python para listar instâncias EC2 paradas",
    "Compare Kubernetes e ECS para cargas de trabalho de produção",
    "Qual a diferença entre RTO e RPO em disaster recovery?",
]

# Preços públicos (US$ por 1M de tokens) — atualizados para referência de custo.
# Gemini 1.5 Flash: 0,075 entrada / 0,30 saída.  Claude 3 Haiku: 0,25 / 1,25.
PRECOS = {
    "gemini-1.5-flash": {"in": 0.075, "out": 0.30},
    "claude-3-haiku": {"in": 0.25, "out": 1.25},
}

# Palavras-chave esperadas por prompt para a heurística de qualidade (1-5).
ESPERADO = [
    ["nat", "internet gateway", "privada", "saída", "público"],
    ["exposição", "porta", "security group", "ssh", "público", "iam"],
    ["boto3", "ec2", "stopped", "describe_instances", "filter"],
    ["kubernetes", "ecs", "fargate", "produção", "escala"],
    ["rto", "rpo", "recuperação", "tempo", "dados"],
]


def _qualidade(resposta: str, esperado: list[str]) -> int:
    """Nota 1-5 = fração de palavras-chave cobertas, normalizada para [1,5]."""
    if not resposta:
        return 1
    texto = resposta.lower()
    cobertas = sum(1 for kw in esperado if kw in texto)
    frac = cobertas / len(esperado)
    return max(1, min(5, round(1 + frac * 4)))


# ---------------------------------------------------------------------------
# Backend Vertex AI (Gemini)
# ---------------------------------------------------------------------------
def chamar_gemini(prompt: str) -> dict:
    """Invoca o Gemini 1.5 Flash via Vertex AI SDK. Retorna métricas + texto."""
    from vertexai.generative_models import GenerativeModel
    import vertexai

    vertexai.init(project=PROJETO, location=REGIAO)
    modelo = GenerativeModel("gemini-1.5-flash")

    inicio = time.perf_counter()
    resp = modelo.generate_content(prompt)
    latencia = time.perf_counter() - inicio

    uso = resp.usage_metadata
    tin, tout = uso.prompt_token_count, uso.candidates_token_count
    return {
        "texto": resp.text,
        "latencia_s": round(latencia, 3),
        "tokens_in": tin,
        "tokens_out": tout,
    }


# ---------------------------------------------------------------------------
# Backend AWS Bedrock (Claude 3 Haiku) — opcional
# ---------------------------------------------------------------------------
def chamar_bedrock(prompt: str) -> dict:
    """Invoca o Claude 3 Haiku via Bedrock. Requer credenciais AWS."""
    import boto3

    regiao_aws = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    cliente = boto3.client("bedrock-runtime", region_name=regiao_aws)
    corpo = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    inicio = time.perf_counter()
    resp = cliente.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(corpo),
    )
    latencia = time.perf_counter() - inicio
    payload = json.loads(resp["body"].read())
    uso = payload["usage"]
    return {
        "texto": payload["content"][0]["text"],
        "latencia_s": round(latencia, 3),
        "tokens_in": uso["input_tokens"],
        "tokens_out": uso["output_tokens"],
    }


def _custo(modelo: str, tin: int, tout: int) -> float:
    p = PRECOS[modelo]
    return round((tin * p["in"] + tout * p["out"]) / 1_000_000, 8)


def _executar(nome_modelo: str, fn, prompt: str, esperado: list[str]) -> dict:
    """Executa uma chamada protegida por try/except e monta o registro padrão."""
    try:
        r = fn(prompt)
        return {
            "modelo": nome_modelo,
            "modo": "real",
            "latencia_s": r["latencia_s"],
            "tokens_in": r["tokens_in"],
            "tokens_out": r["tokens_out"],
            "tokens_total": r["tokens_in"] + r["tokens_out"],
            "custo_usd": _custo(nome_modelo, r["tokens_in"], r["tokens_out"]),
            "qualidade": _qualidade(r["texto"], esperado),
            "resposta": r["texto"],
        }
    except Exception as exc:  # noqa: BLE001 — qualquer falha vira modo stub
        return {
            "modelo": nome_modelo,
            "modo": "stub",
            "erro": str(exc)[:200],
            "latencia_s": None,
            "tokens_in": None,
            "tokens_out": None,
            "tokens_total": None,
            "custo_usd": None,
            "qualidade": None,
            "resposta": "",
        }


def _render_tabela(resultados: list[dict]) -> None:
    """Imprime a tabela lado a lado (Rich se disponível, senão texto puro)."""
    linhas = []
    for item in resultados:
        for m in item["modelos"]:
            linhas.append(
                (
                    item["prompt"][:42] + "…",
                    m["modelo"],
                    m["modo"],
                    f'{m["latencia_s"]}' if m["latencia_s"] is not None else "-",
                    f'{m["tokens_total"]}' if m["tokens_total"] is not None else "-",
                    f'{m["custo_usd"]:.6f}' if m["custo_usd"] is not None else "-",
                    f'{m["qualidade"]}' if m["qualidade"] is not None else "-",
                )
            )
    cabecalho = ["Prompt", "Modelo", "Modo", "Latência(s)", "Tokens", "Custo US$", "Qual."]
    try:
        from rich.console import Console
        from rich.table import Table

        t = Table(title="Vertex AI (Gemini) vs Bedrock (Claude) — comparação")
        for c in cabecalho:
            t.add_column(c)
        for ln in linhas:
            t.add_row(*ln)
        Console().print(t)
    except Exception:  # pragma: no cover — fallback sem Rich
        print(" | ".join(cabecalho))
        for ln in linhas:
            print(" | ".join(ln))


def main() -> None:
    ap = argparse.ArgumentParser(description="Compara Vertex AI Gemini e Bedrock Claude")
    ap.add_argument("--no-bedrock", action="store_true", help="não chamar a AWS")
    args = ap.parse_args()

    usar_bedrock = not args.no_bedrock and bool(os.getenv("AWS_ACCESS_KEY_ID"))

    resultados = []
    for i, prompt in enumerate(PROMPTS):
        modelos = [_executar("gemini-1.5-flash", chamar_gemini, prompt, ESPERADO[i])]
        if usar_bedrock:
            modelos.append(_executar("claude-3-haiku", chamar_bedrock, prompt, ESPERADO[i]))
        resultados.append({"prompt": prompt, "modelos": modelos})
        print(f"[{i+1}/{len(PROMPTS)}] processado: {prompt[:50]}…")

    REPORTS.mkdir(exist_ok=True)
    saida = REPORTS / "model_comparison.json"
    saida.write_text(
        json.dumps(
            {"regiao": REGIAO, "bedrock_habilitado": usar_bedrock, "resultados": resultados},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados salvos em {saida}\n")
    _render_tabela(resultados)


if __name__ == "__main__":
    main()
