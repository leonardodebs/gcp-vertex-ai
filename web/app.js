/* app.js — popula o dashboard estático.
   Lê reports/model_comparison.json (ao vivo) e usa dados de referência embutidos
   para as seções estáticas (custo, 20 dimensões, DX, acurácia). */

"use strict";

// ---- helpers de DOM -------------------------------------------------------
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  return e;
};
const $ = (id) => document.getElementById(id);

// Barra horizontal proporcional ao valor (val) sobre o máximo (max).
function barra(label, val, max, cor, sufixo = "") {
  const row = el("div", "bar-row");
  row.appendChild(el("div", "label", label));
  const track = el("div", "bar-track");
  const pct = max > 0 ? Math.max(4, (val / max) * 100) : 0;
  const fill = el("div", `bar-fill ${cor}`, val + sufixo);
  fill.style.width = pct + "%";
  track.appendChild(fill);
  row.appendChild(track);
  row.appendChild(el("div", "val", val + sufixo));
  return row;
}

// ---- dados de referência (espelham os scripts Python) ---------------------
const SKILLS = ["Vertex AI", "Gemini API", "Vertex AI Embeddings", "BigQuery ML",
  "RAG (FAISS)", "AWS Bedrock", "Multicloud", "Python", "FinOps"];

// Custo: 1M in + 1M out (US$). Haiku 0,25+1,25=1,50 · Flash 0,075+0,30=0,375.
const CUSTO = [
  { label: "Claude 3 Haiku (AWS)", val: 1.5, cor: "aws" },
  { label: "Gemini 1.5 Flash (GCP)", val: 0.375, cor: "gcp" },
];

// Acurácia do classificador de severidade (mesmos 500 alertas).
const ACURACIA = [
  { label: "scikit-learn (Lab 3)", val: 0.95, cor: "aws" },
  { label: "BigQuery ML (SQL)", val: 0.93, cor: "gcp2" },
];

// 20 dimensões: [dimensão, AWS, GCP, destaque?].
const DIMENSOES = [
  ["LLM proprietário de ponta", "Claude 3.x", "Gemini 1.5 Pro/Flash"],
  ["Catálogo de modelos", "Bedrock (Anthropic, Meta, Mistral…)", "Model Garden (150+)"],
  ["LLM rápido — preço 1M in/out", "$0,25 / $1,25", "$0,075 / $0,30"],
  ["Janela de contexto", "até 200k (Claude)", "até 1M–2M (Gemini)"],
  ["Embeddings", "Titan Embeddings", "gecko@003 / text-embedding-004"],
  ["RAG gerenciado", "Knowledge Bases", "RAG Engine / Vertex Search"],
  ["Vector store nativo", "OpenSearch Serverless", "Vector Search"],
  ["Agentes", "Bedrock Agents", "Agent Builder"],
  ["Guardrails", "Bedrock Guardrails", "Safety Filters"],
  ["Fine-tuning", "Custom Models", "Vertex AI Tuning"],
  ["Plataforma ML completa", "SageMaker", "Vertex AI Training/Pipelines"],
  ["ML via SQL ⭐", "Redshift ML (usa SageMaker)", "BigQuery ML (nativo)", true],
  ["Notebooks", "SageMaker Studio", "Vertex AI Workbench"],
  ["AutoML", "SageMaker Autopilot", "Vertex AI AutoML"],
  ["Integração com warehouse", "Redshift (separado)", "BigQuery (mesma engine)"],
  ["CLI", "aws (amplo)", "gcloud (coeso)"],
  ["Multimodal nativo", "Claude (texto+visão)", "Gemini (texto/img/áudio/vídeo)"],
  ["Free tier de entrada", "pay-per-use", "$300 / 90 dias"],
  ["Maturidade do ecossistema", "maior", "crescendo rápido"],
  ["Lock-in de dados", "Redshift / S3", "BigQuery / GCS"],
];

// Developer Experience (1–5): [dimensão, AWS, GCP].
const DX = [
  ["Setup inicial (CLI/SDK)", 4, 4],
  ["Acesso a modelos de ponta", 5, 4],
  ["ML com SQL", 2, 5],
  ["RAG do zero ao deploy", 4, 4],
  ["Documentação/exemplos", 5, 4],
  ["Custo de LLM rápido", 3, 5],
];

// ---- render ---------------------------------------------------------------
function renderSkills() {
  const c = $("skills");
  SKILLS.forEach((s) => c.appendChild(el("span", null, s)));
}

function renderCusto() {
  const max = Math.max(...CUSTO.map((d) => d.val));
  const c = $("custo-bars");
  CUSTO.forEach((d) => c.appendChild(barra(d.label, d.val, max, d.cor, " US$")));
}

function renderAcuracia() {
  const c = $("acuracia");
  ACURACIA.forEach((d) => c.appendChild(barra(d.label, d.val, 1, d.cor)));
}

function renderDimensoes() {
  const tbl = el("table");
  tbl.innerHTML =
    "<thead><tr><th>#</th><th>Dimensão</th><th>AWS</th><th>GCP</th></tr></thead>";
  const tb = el("tbody");
  DIMENSOES.forEach((d, i) => {
    const tr = el("tr");
    if (d[3]) tr.style.background = "rgba(245,197,24,.08)";
    tr.appendChild(el("td", null, String(i + 1)));
    tr.appendChild(el("td", null, d[0]));
    tr.appendChild(el("td", "aws-col", d[1]));
    tr.appendChild(el("td", "gcp-col", d[2]));
    tb.appendChild(tr);
  });
  tbl.appendChild(tb);
  $("tabela-dim").appendChild(tbl);
}

function renderDX() {
  const c = $("dx-bars");
  c.appendChild(
    Object.assign(el("div", "bar-row"), {
      innerHTML:
        '<div class="label" style="font-weight:600;color:var(--txt)">Dimensão</div>' +
        '<div class="label" style="color:var(--aws)">AWS</div>' +
        '<div class="label" style="color:var(--gcp)">GCP</div>',
    })
  );
  let somaA = 0, somaG = 0;
  DX.forEach(([dim, a, g]) => {
    somaA += a; somaG += g;
    const row = el("div", "bar-row");
    row.appendChild(el("div", "label", dim));
    const mk = (v, cor) => {
      const t = el("div", "bar-track");
      const f = el("div", `bar-fill ${cor}`, v + "/5");
      f.style.width = (v / 5) * 100 + "%";
      t.appendChild(f);
      return t;
    };
    row.appendChild(mk(a, "aws"));
    row.appendChild(mk(g, "gcp"));
    c.appendChild(row);
  });
  const mA = (somaA / DX.length).toFixed(1);
  const mG = (somaG / DX.length).toFixed(1);
  $("dx-media").innerHTML =
    `<strong>Média DX:</strong> AWS ${mA}/5 · GCP ${mG}/5 — ` +
    "GCP ganha em ML-via-SQL e custo de inferência; AWS ganha em acesso ao Claude.";
}

// Tabela de modelos: carrega o JSON ao vivo (com fallback amigável).
async function renderModelos() {
  const alvo = $("tabela-modelos");
  try {
    const resp = await fetch("../reports/model_comparison.json", { cache: "no-store" });
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();

    const algumStub = data.resultados.some((r) =>
      r.modelos.some((m) => m.modo === "stub")
    );
    $("modo-aviso").innerHTML = algumStub
      ? '<span class="tag stub">modo stub</span> — rode <code>make compare</code> ' +
        "com credenciais GCP para preencher latência, tokens e custo reais."
      : '<span class="tag real">modo real</span> — métricas obtidas da API.';

    const tbl = el("table");
    tbl.innerHTML =
      "<thead><tr><th>Prompt</th><th>Modelo</th><th>Modo</th><th>Latência (s)</th>" +
      "<th>Tokens</th><th>Custo US$</th><th>Qual.</th></tr></thead>";
    const tb = el("tbody");
    data.resultados.forEach((item) => {
      item.modelos.forEach((m) => {
        const tr = el("tr");
        const cel = (v) => el("td", null, v == null ? "—" : v);
        tr.appendChild(el("td", null, item.prompt.slice(0, 46) + "…"));
        tr.appendChild(el("td", "gcp-col", m.modelo));
        tr.appendChild(
          Object.assign(el("td"), {
            innerHTML: `<span class="tag ${m.modo}">${m.modo}</span>`,
          })
        );
        tr.appendChild(cel(m.latencia_s));
        tr.appendChild(cel(m.tokens_total));
        tr.appendChild(cel(m.custo_usd != null ? m.custo_usd.toFixed(6) : null));
        tr.appendChild(cel(m.qualidade));
        tb.appendChild(tr);
      });
    });
    tbl.appendChild(tb);
    alvo.innerHTML = "";
    alvo.appendChild(tbl);
  } catch (e) {
    alvo.innerHTML =
      '<p class="muted" style="padding:16px">Não foi possível carregar ' +
      "<code>reports/model_comparison.json</code> (" +
      e.message +
      "). Sirva o projeto via <code>python3 -m http.server</code> na raiz " +
      "(o protocolo <code>file://</code> bloqueia o fetch) e rode " +
      "<code>make compare</code> antes.</p>";
    $("modo-aviso").textContent = "";
  }
}

// ---- init -----------------------------------------------------------------
renderSkills();
renderCusto();
renderAcuracia();
renderDimensoes();
renderDX();
renderModelos();
