// Rota /api/gamificacao — pontos, badges, leaderboard (Bloco 5.1)
import { Router } from "express";
import { pool } from "../db.js";

const router = Router();

const BADGES = {
  historiador: { pontos: 5, cond: "historias_submetidas >= 5" },
  guardiao: { pontos: 1000, cond: "pontos >= 1000" },
  curador: { pontos: 10, cond: "historias_validadas >= 10" },
  padrinho_milk: { pontos: 3, cond: "historias_validadas >= 3" },
};

// Recalcular badges de um utilizador
async function recalcBadges(email) {
  const r = await pool.query("SELECT * FROM usuario WHERE email = $1", [email]);
  if (!r.rows.length) return;
  const u = r.rows[0];
  const novos = [];
  for (const [nome, def] of Object.entries(BADGES)) {
    const condRes = await pool.query(`SELECT ${def.cond} AS ok FROM usuario WHERE email=$1`, [email]);
    if (condRes.rows[0].ok && !(u.badges || []).includes(nome)) novos.push(nome);
  }
  if (novos.length) {
    await pool.query(
      "UPDATE usuario SET badges = array_cat(badges, $1) WHERE email = $2",
      [novos, email]
    );
  }
}

// POST /api/gamificacao/registar — regista/cria utilizador (email + nome + ccdr)
router.post("/registar", async (req, res, next) => {
  try {
    const email = String(req.body.email || "").trim().toLowerCase();
    const nome = String(req.body.nome || "").trim();
    const ccdr = String(req.body.ccdr || "").trim() || null;
    if (!email) return res.status(400).json({ erro: "email obrigatório" });
    await pool.query(
      `INSERT INTO usuario (email, nome, ccdr) VALUES ($1,$2,$3)
       ON CONFLICT (email) DO NOTHING`,
      [email, nome, ccdr]
    );
    res.json({ status: "ok" });
  } catch (e) { next(e); }
});

// GET /api/gamificacao/perfil?email=
router.get("/perfil", async (req, res, next) => {
  try {
    const email = String(req.query.email || "").trim().toLowerCase();
    if (!email) return res.status(400).json({ erro: "email obrigatório" });
    const r = await pool.query(
      "SELECT email, nome, pontos, nivel, badges, historias_submetidas, historias_validadas, ccdr FROM usuario WHERE email=$1",
      [email]
    );
    if (!r.rows.length) return res.status(404).json({ erro: "utilizador não encontrado" });
    res.json(r.rows[0]);
  } catch (e) { next(e); }
});

// GET /api/gamificacao/leaderboard?ccdr=&limit=20
router.get("/leaderboard", async (req, res, next) => {
  try {
    const ccdr = req.query.ccdr ? String(req.query.ccdr) : null;
    const limit = Math.min(Number(req.query.limit) || 20, 100);
    const params = [];
    let where = "";
    if (ccdr) { params.push(ccdr); where = `WHERE ccdr = $1`; }
    const r = await pool.query(
      `SELECT nome, pontos, nivel, badges, historias_submetidas
       FROM usuario ${where}
       ORDER BY pontos DESC LIMIT $${params.length + 1}`,
      [...params, limit]
    );
    res.json({ leaderboard: r.rows });
  } catch (e) { next(e); }
});

export default router;
