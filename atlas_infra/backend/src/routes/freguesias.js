// Rota /api/freguesias — autocomplete DGAL (Bloco 3.1)
import { Router } from "express";
import { pool } from "../db.js";

const router = Router();

// GET /api/freguesias?q=barcelos&limit=20
router.get("/", async (req, res, next) => {
  try {
    const q = String(req.query.q || "").trim();
    const limit = Math.min(Number(req.query.limit) || 20, 100);
    if (q.length < 2) return res.json({ freguesias: [] });

    const r = await pool.query(
      `SELECT codigo_dgal, nome, municipio, distrito, regiao, ccdr, geom_centro
       FROM freguesia
       WHERE nome ILIKE $1 OR municipio ILIKE $1
       ORDER BY nome LIMIT $2`,
      [`%${q}%`, limit]
    );
    res.json({ freguesias: r.rows });
  } catch (e) { next(e); }
});

// GET /api/freguesias/municipios
router.get("/municipios", async (_req, res, next) => {
  try {
    const r = await pool.query(
      "SELECT DISTINCT municipio, distrito FROM freguesia ORDER BY municipio"
    );
    res.json({ municipios: r.rows });
  } catch (e) { next(e); }
});

export default router;
