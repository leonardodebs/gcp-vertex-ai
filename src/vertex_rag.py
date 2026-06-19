"""
vertex_rag.py — RAG com Vertex AI sobre os runbooks de operação.

Equivalente AWS: Amazon Bedrock Knowledge Bases (ingestão + OpenSearch + retrieve).
Aqui montamos o pipeline "na mão" para evidenciar cada etapa:

    1. Carrega os 8 runbooks de data/runbooks (reaproveitados do projeto3 da Fase 1).
    2. Quebra em chunks por parágrafo.
    3. Gera embeddings com a Vertex AI Embeddings API (text-embedding model).
    4. Indexa em FAISS local (mesma estratégia da Fase 1).
    5. Na consulta: embeda a pergunta, recupera top_k chunks e gera a resposta
       com o Gemini 1.5 Flash, citando as fontes.

Comparação com a Fase 1: lá os embeddings vinham de sentence-transformers
(all-MiniLM-L6-v2, 384 dims, local/grátis). Aqui usamos o modelo gerenciado da
Google (768 dims, pago por token). O índice é reconstruído em memória a cada
execução para manter o exemplo autocontido.

Uso:
    python src/vertex_rag.py "Como resolver erro 502 no ALB?"
    python src/vertex_rag.py --top-k 4 "Passos para failover do RDS?"
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUNBOOKS = RAIZ / "data" / "runbooks"
REGIAO = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
PROJETO = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Modelo de embeddings do Vertex AI. O enunciado pede textembedding-gecko@003;
# usamos a variável de ambiente para permitir o sucessor text-embedding-004.
MODELO_EMBED = os.getenv("VERTEX_EMBED_MODEL", "textembedding-gecko@003")
MODELO_GEN = "gemini-1.5-flash"


def carregar_chunks() -> list[dict]:
    """Lê os runbooks .md e os divide em chunks por parágrafo (>40 chars)."""
    chunks = []
    for arquivo in sorted(RUNBOOKS.glob("*.md")):
        texto = arquivo.read_text(encoding="utf-8")
        for bloco in re.split(r"\n\s*\n", texto):
            bloco = bloco.strip()
            if len(bloco) >= 40:
                chunks.append({"file": arquivo.name, "text": bloco})
    return chunks


def embeddings_vertex(textos: list[str]) -> "list[list[float]]":
    """Gera embeddings em lote via Vertex AI. Levanta exceção se indisponível."""
    import vertexai
    from vertexai.language_models import TextEmbeddingModel

    vertexai.init(project=PROJETO, location=REGIAO)
    modelo = TextEmbeddingModel.from_pretrained(MODELO_EMBED)
    # A API aceita lotes; quebramos de 5 em 5 para respeitar limites de payload.
    vetores = []
    for i in range(0, len(textos), 5):
        lote = textos[i : i + 5]
        resp = modelo.get_embeddings(lote)
        vetores.extend([e.values for e in resp])
    return vetores


def construir_indice(chunks: list[dict]):
    """Embeda todos os chunks e cria um índice FAISS (produto interno normalizado)."""
    import faiss
    import numpy as np

    vetores = embeddings_vertex([c["text"] for c in chunks])
    mat = np.array(vetores, dtype="float32")
    faiss.normalize_L2(mat)  # normaliza p/ usar produto interno como cosseno
    indice = faiss.IndexFlatIP(mat.shape[1])
    indice.add(mat)
    return indice, mat.shape[1]


def buscar(indice, chunks, pergunta: str, top_k: int) -> list[dict]:
    """Embeda a pergunta e retorna os top_k chunks mais relevantes."""
    import faiss
    import numpy as np

    q = np.array(embeddings_vertex([pergunta]), dtype="float32")
    faiss.normalize_L2(q)
    scores, idxs = indice.search(q, top_k)
    saida = []
    for score, idx in zip(scores[0], idxs[0]):
        c = chunks[int(idx)]
        saida.append({"file": c["file"], "text": c["text"], "score": float(score)})
    return saida


def gerar_resposta(pergunta: str, contextos: list[dict]) -> str:
    """Gera a resposta final com Gemini, ancorada nos contextos recuperados."""
    import vertexai
    from vertexai.generative_models import GenerativeModel

    vertexai.init(project=PROJETO, location=REGIAO)
    modelo = GenerativeModel(MODELO_GEN)
    blocos = "\n\n".join(f"[{c['file']}]\n{c['text']}" for c in contextos)
    prompt = (
        "Você é um assistente de SRE. Responda à pergunta usando APENAS o contexto "
        "dos runbooks abaixo. Cite os arquivos usados. Se não houver resposta no "
        "contexto, diga isso claramente.\n\n"
        f"=== CONTEXTO ===\n{blocos}\n\n=== PERGUNTA ===\n{pergunta}\n\n=== RESPOSTA ==="
    )
    return modelo.generate_content(prompt).text


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG com Vertex AI sobre runbooks")
    ap.add_argument("pergunta", help="pergunta em linguagem natural")
    ap.add_argument("--top-k", type=int, default=3, help="nº de chunks a recuperar")
    args = ap.parse_args()

    chunks = carregar_chunks()
    print(f"Runbooks carregados: {len(set(c['file'] for c in chunks))} arquivos, "
          f"{len(chunks)} chunks.")

    try:
        inicio = time.perf_counter()
        indice, dims = construir_indice(chunks)
        fontes = buscar(indice, chunks, args.pergunta, args.top_k)
        resposta = gerar_resposta(args.pergunta, fontes)
        dur = time.perf_counter() - inicio
    except Exception as exc:  # noqa: BLE001
        print(
            "\n[modo stub] Não foi possível chamar o Vertex AI "
            f"(motivo: {str(exc)[:160]}).\n"
            "Configure GOOGLE_CLOUD_PROJECT e credenciais para executar de verdade.\n"
            f"Embeddings seriam gerados com '{MODELO_EMBED}' (768 dims) e a resposta "
            f"com '{MODELO_GEN}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nEmbeddings: {MODELO_EMBED} ({dims} dims) | tempo total: {dur:.2f}s\n")
    print("=" * 70)
    print(resposta)
    print("=" * 70)
    print("\nFontes consultadas:")
    for f in fontes:
        print(f"  - {f['file']:<26} relevância={f['score']:.4f}")
    print(
        "\nComparação com a Fase 1 (sentence-transformers all-MiniLM-L6-v2, 384 dims, "
        "local/grátis): o gecko@003 entrega 768 dims e melhor captura semântica em "
        "pt-BR, ao custo de ~US$0,025/1M tokens e dependência de rede."
    )


if __name__ == "__main__":
    main()
