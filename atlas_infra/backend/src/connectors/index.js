// Atlas Vivo MILK — registro central de datasources PT (30+) + fetch com cache
// Bloco 4.1. Fontes validadas 2026-03-24, todas as URLs ativas.
// Cache em PostgreSQL (datasource_cache) respeitando cache_ttl por fonte.
import crypto from "node:crypto";
import { pool } from "../db.js";

// Esquema de cada fonte (alinhado com datasources-30-atlas-milk.json)
function src(id, name, url, category, { auth = "none", fmt = "json", ttl = 3600, rate = null } = {}) {
  return { id, name, url, category, auth, response_format: fmt, cache_ttl: ttl, rate_limit: rate };
}

export const SOURCES = [
  // Legislação & Governança
  src("parlamento_pt", "Portal Dados Abertos Parlamento", "https://www.parlamento.pt/dados", "legislacao", { fmt: "json" }),
  src("central_dados", "Central de Dados (GitHub)", "https://github.com/centraldedados/parlamento", "legislacao", { fmt: "csv" }),
  // Justiça & Direito
  src("dgsi", "DGSI — Base Jurídica", "https://www.dgsi.pt/pgrp.nsf", "justica", { fmt: "html", auth: "none" }),
  src("ministerio_publico", "Ministério Público — Deliberações", "https://www.ministeriopublico.pt/deliberacoes", "justica", { fmt: "html" }),
  // Autarquias & Governo Local
  src("dgal", "DGAL — Portal Autárquico", "https://www.portalautarquico.dgal.gov.pt", "autarquias", { auth: "none", ttl: 86400 }),
  src("transparencia_gov", "Transparência.gov.pt", "https://transparencia.gov.pt", "autarquicas", { fmt: "csv", ttl: 86400 }),
  src("anafre", "ANAFRE — Assoc. Nacional Freguesias", "https://www.anafre.pt", "autarquias", { fmt: "html" }),
  src("lisboa_aberta", "Lisboa Aberta", "https://www.cm-lisboa.pt/viver/cidade-inteligente/lisboa-aberta", "autarquias", { fmt: "json", ttl: 604800 }),
  src("geoapi_pt", "GeoAPI Portugal", "https://geoapi.pt", "geografia", { fmt: "json", ttl: 86400 }),
  // Geografia & Cartografia
  src("snig", "SNIG — Sist. Nacional Inf. Geográfica", "https://snig.dgterritorio.gov.pt", "geografia", { fmt: "geojson", ttl: 604800 }),
  src("dgt_cdd", "DGT — Centro de Dados", "https://cdd.dgterritorio.gov.pt", "geografia", { fmt: "wms", ttl: 604800 }),
  src("gridmar", "Gridmar — Instituto Hidrográfico", "https://gridmar.hidrografico.pt", "geografia", { fmt: "geotiff", ttl: 2592000 }),
  src("emodnet", "EMODnet Bathymetry", "https://www.emodnet-bathymetry.eu", "geografia", { fmt: "wms", ttl: 2592000 }),
  // Economia & Desenvolvimento Regional
  src("dados_gov_pt", "Dados.gov.pt — Portal Dados Abertos", "https://www.dados.gov.pt", "economia", { fmt: "csv" }),
  src("ine", "INE — Inst. Nacional Estatística", "https://www.ine.pt", "economia", { fmt: "json", ttl: 604800 }),
  src("pordata", "PORDATA", "https://www.pordata.pt", "economia", { fmt: "csv", ttl: 604800 }),
  src("bpstat", "BPstat — Banco de Portugal", "https://bpstat.bportugal.pt", "economia", { fmt: "json", ttl: 86400 }),
  src("dgeec", "DGEEC — Educação & Ciência", "https://www.dgeec.medu.pt", "economia", { fmt: "csv", ttl: 2592000 }),
  // Património Cultural & Memória
  src("matriznet", "MatrizNet — DGPC", "https://matriznet.dgpc.pt", "patrimonio", { fmt: "xml", ttl: 604800 }),
  src("matrizpix", "MatrizPix — DGPC", "https://matrizpix.dgpc.pt", "patrimonio", { fmt: "json", ttl: 604800 }),
  src("fct_polen", "FCT — POLEN (Investigação)", "https://www.fct.pt", "patrimonio", { fmt: "csv", ttl: 2592000 }),
];

// Hash determinístico dos parâmetros para a chave de cache
function paramsHash(params) {
  return crypto.createHash("sha1").update(JSON.stringify(params || {})).digest("hex").slice(0, 16);
}

// Buscar com cache em PostgreSQL. Para WMS/WFS/GeoTIFF devolve metadados
// (o frontend Leaflet consome SNIG/DGT diretamente como tile services).
export async function fetchSource(source, params = {}) {
  const ph = paramsHash(params);
  // Tentar cache
  try {
    const cached = await pool.query(
      "SELECT payload FROM datasource_cache WHERE source_id=$1 AND endpoint=$2 AND params_hash=$3",
      [source.id, source.url, ph]
    );
    if (cached.rows.length) return cached.rows[0].payload;
  } catch { /* db pode não estar pronto */ }

  // Para serviços geográficos em WMS/WFS, não buscar payload — devolver URL pronto a usar
  if (source.response_format === "wms" || source.response_format === "wfs" || source.response_format === "geotiff") {
    const payload = { type: source.response_format, url: source.url, params };
    return payload;
  }

  // Fetch HTTP genérico
  const url = new URL(source.url);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);

  const headers = {};
  if (source.auth === "api_key") {
    const key = process.env[`${source.id.toUpperCase()}_API_KEY`] || "";
    if (key) headers["Authorization"] = `Bearer ${key}`;
  }

  const resp = await fetch(url.toString(), { headers, signal: AbortSignal.timeout(15000) });
  if (!resp.ok) throw new Error(`HTTP ${resp.status} de ${source.id}`);
  let payload;
  const ct = resp.headers.get("content-type") || "";
  if (ct.includes("json") || source.response_format === "json" || source.response_format === "geojson") {
    payload = await resp.json();
  } else {
    payload = { text: await resp.text(), format: source.response_format };
  }

  // Guardar em cache
  try {
    await pool.query(
      `INSERT INTO datasource_cache (source_id, endpoint, params_hash, payload)
       VALUES ($1,$2,$3,$4)
       ON CONFLICT (source_id, endpoint, params_hash) DO UPDATE SET payload = EXCLUDED.payload, fetched_at = now()`,
      [source.id, source.url, ph, payload]
    );
  } catch { /* cache é best-effort */ }

  return payload;
}
