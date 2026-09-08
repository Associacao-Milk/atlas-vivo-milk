// Rota /api/connectors — expõe os 30+ datasources PT validados (Bloco 4.1)
import { Router } from "express";
import { SOURCES, fetchSource } from "../connectors/index.js";

const router = Router();

// GET /api/connectors — lista metadados de todas as fontes
router.get("/", (_req, res) => {
  res.json({
    total: SOURCES.length,
    sources: SOURCES.map((s) => ({
      id: s.id, name: s.name, url: s.url, category: s.category,
      auth: s.auth, response_format: s.response_format, rate_limit: s.rate_limit,
    })),
  });
});

// GET /api/connectors/:id?params=... — chama um connector (com cache)
router.get("/:id", async (req, res, next) => {
  try {
    const id = req.params.id;
    const source = SOURCES.find((s) => s.id === id);
    if (!source) return res.status(404).json({ erro: "fonte desconhecida" });
    const params = {};
    for (const [k, v] of Object.entries(req.query)) {
      if (k !== "id") params[k] = String(v);
    }
    const result = await fetchSource(source, params);
    res.json({ source: source.id, data: result });
  } catch (e) {
    res.status(502).json({ erro: "falha ao obter fonte externa", detalhe: String(e.message || e) });
  }
});

export default router;
