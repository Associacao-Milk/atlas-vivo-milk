// Atlas Vivo MILK — pool PostgreSQL + migrations + seed
// Bloco 4.1: backend / base de dados
import fs from "node:fs";
import path from "node:path";
import pg from "pg";
import { registerType } from "pgvector/pg";

const {
  POSTGRES_USER = "milk",
  POSTGRES_DB = "atlas_vivo",
  POSTGRES_PASSWORD = "",
  POSTGRES_HOST = "db",
  POSTGRES_PORT = "5432",
} = process.env;

export const pool = new pg.Pool({
  user: POSTGRES_USER,
  password: POSTGRES_PASSWORD,
  host: POSTGRES_HOST,
  port: Number(POSTGRES_PORT),
  database: POSTGRES_DB,
  max: 10,
  idleTimeoutMillis: 30000,
});

// Regista o tipo vector no parser do node-postgres
let typeReady = false;
export async function ensureVectorType() {
  if (typeReady) return;
  const client = await pool.connect();
  try {
    await client.query("CREATE EXTENSION IF NOT EXISTS vector");
    registerType(client);
    typeReady = true;
  } finally {
    client.release();
  }
}

// ---- Migration ----
export async function migrate() {
  await ensureVectorType();
  const schema = fs.readFileSync(
    path.join(import.meta.dirname, "schema.sql"),
    "utf-8"
  );
  await pool.query(schema);
  console.log("[db] schema aplicado (migrations ok)");
}

// ---- Seed mínimo: distritos/municípios representativos (DGAL subset) ----
// O carregamento completo das 3091 freguesias deve ser feito via connector DGAL
// (backend/src/connectors/dgal.js) após deploy.
const SEED_FREGUESIAS = [
  // Barcelos (piloto)
  { codigo: "030219", nome: "Barcelos", municipio: "Barcelos", distrito: "Braga", regiao: "Continente", ccdr: "CCDR-N", lat: 41.5287, lng: -8.6145 },
  // Évora (piloto)
  { codigo: "070505", nome: "Évora (Sé e São Pedro)", municipio: "Évora", distrito: "Évora", regiao: "Continente", ccdr: "CCDR-A", lat: 38.5667, lng: -7.9000 },
  // Matosinhos (piloto)
  { codigo: "130806", nome: "Matosinhos", municipio: "Matosinhos", distrito: "Porto", regiao: "Continente", ccdr: "CCDR-N", lat: 41.1797, lng: -8.6896 },
];

export async function seed() {
  await migrate();
  for (const f of SEED_FREGUESIAS) {
    await pool.query(
      `INSERT INTO freguesia (codigo_dgal, nome, municipio, distrito, regiao, ccdr, geom_centro)
       VALUES ($1,$2,$3,$4,$5,$6,$7)
       ON CONFLICT (codigo_dgal) DO NOTHING`,
      [f.codigo, f.nome, f.municipio, f.distrito, f.regiao, f.ccdr, JSON.stringify({ lat: f.lat, lng: f.lng })]
    );
  }
  console.log("[db] seed aplicado (freguesias piloto: Barcelos, Évora, Matosinhos)");
}

// Permite correr: node src/db.js --migrate | --seed
const arg = process.argv[2];
if (arg === "--migrate") {
  migrate().then(() => pool.end()).catch((e) => { console.error(e); process.exit(1); });
} else if (arg === "--seed") {
  seed().then(() => pool.end()).catch((e) => { console.error(e); process.exit(1); });
}
