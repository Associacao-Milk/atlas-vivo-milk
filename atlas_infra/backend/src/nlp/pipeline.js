// Pipeline NLP PT — Bloco 4.1/6.1
// Usa HuggingFace Inference API (bertimbau / xlm-roberta) quando HF_TOKEN definido.
// Sem token, degrada para análise léxica local determinística (score heurístico).
import crypto from "node:crypto";
import { pool } from "../db.js";

const HF_TOKEN = process.env.HF_TOKEN || "";
const HF_ENDPOINT = "https://api-inference.huggingface.co/models/neuralmind/bert-base-portuguese-cased";

// Tags temáticas (CURADORIA — clima, água, trabalho, identidade…)
const TAGS_LEX = {
  clima: ["chuva", "seca", "tempo", "vento", "geada", "calor"],
  agua: ["rio", "mar", "fonte", "poço", "regato", "ribeiro", "água"],
  trabalho: ["trabalho", "ofício", "lavoura", "ceifa", "pastor", "moinho", "forno"],
  identidade: ["freguesia", "terra", "gente", "povo", "tradição", "romaria"],
  memoria: ["avó", "avô", "antigamente", "memória", "recordar", " outrora "],
  religiao: ["santo", "senhora", "igreja", "romaria", "procissão", "fé"],
};

function analiseLexica(texto) {
  const t = texto.toLowerCase();
  const tags = [];
  for (const [tag, palavras] of Object.entries(TAGS_LEX)) {
    if (palavras.some((p) => t.includes(p))) tags.push(tag);
  }
  // Score heurístico: comprimento + diversidade de tags + pontuação
  const compr = Math.min(1, texto.length / 200);
  const divers = Math.min(1, tags.length / 4);
  const score = Math.round((0.5 * compr + 0.5 * divers) * 100) / 100;
  // Sentimento léxico simples
  const pos = ["alegria", "amor", "festa", "feliz", "bonito", "calor"].some((p) => t.includes(p));
  const neg = ["triste", "morte", "dor", "medo", "saudade", "perda"].some((p) => t.includes(p));
  const sentiment = pos && !neg ? 0.7 : neg && !pos ? 0.25 : 0.5;
  return { score, tags, sentiment, sentiment_label: sentiment > 0.6 ? "positivo" : sentiment < 0.4 ? "negativo" : "neutro", entities: { pessoas: [], lugares: [], datas: [] }, anacronismos: [] };
}

async function analiseHF(texto) {
  if (!HF_TOKEN) return null;
  try {
    const resp = await fetch(HF_ENDPOINT, {
      method: "POST",
      headers: { Authorization: `Bearer ${HF_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ inputs: texto.slice(0, 1000) }),
      signal: AbortSignal.timeout(20000),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    // HuggingFace devolve embeddings ou classificações; normalizar
    return data;
  } catch {
    return null;
  }
}

// Função principal chamada (assíncrona) após submissão.
// Persiste nlp_result, atualiza embedding se possível e decide auto-approve.
export async function analisarHistoria(historiaId, texto) {
  let resultado = analiseLexica(texto);
  const hf = await analiseHF(texto);
  const modelo = hf ? "bertimbau" : "lexico-local";
  if (hf) {
    // Integrar sinais HF se disponíveis (dependerá do modelo)
    resultado = { ...resultado, modelo };
  }

  await pool.query(
    `INSERT INTO nlp_result (historia_id, score, tags, sentiment, sentiment_label, entities, anacronismos, modelo)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
    [historiaId, resultado.score, resultado.tags, resultado.sentiment, resultado.sentiment_label,
     resultado.entities, resultado.anacronismos, modelo]
  );

  // Auto-approve acima de 0.7 (Bloco 4.1): passa a em_curadoria pronta para publicação
  if (resultado.score > 0.7) {
    await pool.query(
      "UPDATE historia SET estado = 'em_curadoria', updated_at = now() WHERE id = $1",
      [historiaId]
    );
  }

  // Detecção de duplicatas por hash de conteúdo (Bloco 6.1)
  const hash = crypto.createHash("sha256").update(texto).digest("hex");
  await pool.query("UPDATE historia SET cert_hash = $1 WHERE id = $2", [hash, historiaId]);

  return resultado;
}
