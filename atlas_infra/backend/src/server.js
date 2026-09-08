// Atlas Vivo MILK — servidor Express (Bloco 4.1)
// Roteamento de todos os endpoints da API. Proxy via nginx no domínio PT.
import express from "express";
import helmet from "helmet";
import cors from "cors";
import rateLimit from "express-rate-limit";
import { ensureVectorType, pool } from "./db.js";
import historiasRouter from "./routes/historias.js";
import freguesiasRouter from "./routes/freguesias.js";
import mapRouter from "./routes/map.js";
import gamificacaoRouter from "./routes/gamificacao.js";
import connectorsRouter from "./routes/connectors.js";

const app = express();
const PORT = Number(process.env.PORT) || 3000;

// Segurança (Bloco 7.1)
app.use(helmet({ contentSecurityPolicy: false, crossOriginEmbedderPolicy: false }));
const origins = (process.env.CORS_ORIGINS || "https://atlas.milk.pt").split(",").map((s) => s.trim());
app.use(cors({ origin: origins, methods: ["GET", "POST"] }));

// Rate limit global na API
const limiter = rateLimit({
  windowMs: Number(process.env.RATE_LIMIT_WINDOW_MS) || 60000,
  max: Number(process.env.RATE_LIMIT_MAX) || 100,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use("/api/", limiter);

// Body + uploads
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true, limit: "2mb" }));

// Rota raiz de diagnóstico
app.get("/", (_req, res) => res.json({ service: "atlas-vivo-milk-api", status: "ok" }));

// Health check (nginx /healthz)
app.get("/api/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", db: "up" });
  } catch {
    res.status(503).json({ status: "degraded", db: "down" });
  }
});

// Rotas da aplicação (mapeadas nos 7 blocos)
app.use("/submit-historia", historiasRouter);   // 3.1 crowdsourcing + 7.1 cert
app.use("/api/historias", historiasRouter);      // 4.1 leitura/publicação
app.use("/api/freguesias", freguesiasRouter);    // 3.1 autocomplete DGAL
app.use("/api/map", mapRouter);                  // 2.1 dados do mapa
app.use("/api/gamificacao", gamificacaoRouter);  // 5.1 pontos/badges/leaderboard
app.use("/api/connectors", connectorsRouter);    // 4.1 30+ datasources

// Erro genérico
app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ erro: "erro_interno" });
});

async function start() {
  await ensureVectorType();
  app.listen(PORT, () => console.log(`[atlas-api] a ouvir em :${PORT}`));
}

start().catch((e) => { console.error(e); process.exit(1); });
