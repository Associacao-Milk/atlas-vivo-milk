// Rota /api/map — dados para o mapa Leaflet (Bloco 2.1)
import { Router } from "express";
import { pool } from "../db.js";

const router = Router();

// GET /api/map/historias — GeoJSON das histórias publicadas
router.get("/historias", async (_req, res, next) => {
  try {
    const r = await pool.query(
      `SELECT id, titulo, resumo, tipo, freguesia_nome, lat, lng, anonimato, nome_submissor
       FROM historia
       WHERE visibilidade_publica = TRUE AND removed_at IS NULL
         AND lat IS NOT NULL AND lng IS NOT NULL`
    );
    const features = r.rows.map((row) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [Number(row.lng), Number(row.lat)] },
      properties: {
        id: row.id, titulo: row.titulo, resumo: row.resumo, tipo: row.tipo,
        freguesia: row.freguesia_nome, anonimato: row.anonimato,
        nome: row.nome_submissor,
      },
    }));
    res.json({ type: "FeatureCollection", features });
  } catch (e) { next(e); }
});

// GET /api/map/freguesias — limites administrativos (centros para clustering)
router.get("/freguesias", async (_req, res, next) => {
  try {
    const r = await pool.query(
      "SELECT codigo_dgal, nome, municipio, distrito, geom_centro FROM freguesia WHERE geom_centro IS NOT NULL"
    );
    const features = r.rows
      .filter((row) => row.geom_centro)
      .map((row) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [row.geom_centro.lng, row.geom_centro.lat] },
        properties: { codigo: row.codigo_dgal, nome: row.nome, municipio: row.municipio, distrito: row.distrito },
      }));
    res.json({ type: "FeatureCollection", features });
  } catch (e) { next(e); }
});

// GET /api/map/stats — contagens para o painel
router.get("/stats", async (_req, res, next) => {
  try {
    const total = await pool.query("SELECT count(*) AS n FROM historia WHERE removed_at IS NULL");
    const publicadas = await pool.query("SELECT count(*) AS n FROM historia WHERE visibilidade_publica = TRUE");
    const porTipo = await pool.query(
      "SELECT tipo, count(*) AS n FROM historia WHERE visibilidade_publica = TRUE GROUP BY tipo"
    );
    res.json({
      total: Number(total.rows[0].n),
      publicadas: Number(publicadas.rows[0].n),
      por_tipo: porTipo.rows,
    });
  } catch (e) { next(e); }
});

export default router;
