// Rota /submit-historia e /api/historias — Bloco 3.1 (crowdsourcing) + 7.1 (cert)
import { Router } from "express";
import multer from "multer";
import path from "node:path";
import fs from "node:fs";
import { v4 as uuidv4 } from "uuid";
import { pool } from "../db.js";
import { gerarCertificado } from "../security/cert.js";
import { analisarHistoria } from "../nlp/pipeline.js";

const router = Router();

const UPLOAD_DIR = process.env.API_UPLOAD_DIR || "/data/uploads";
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
    filename: (_req, file, cb) => {
      const id = uuidv4();
      const ext = path.extname(file.originalname) || "";
      cb(null, `${id}${ext}`);
    },
  }),
  limits: { fileSize: Number(process.env.MAX_UPLOAD_MB || 500) * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (/^(audio\/|video\/)/.test(file.mimetype)) cb(null, true);
    else cb(new Error("tipo de ficheiro não suportado (só áudio/vídeo)"));
  },
});

const TIPOS = new Set(["lenda", "oficio", "memoria", "curiosidade", "transformacao"]);
const ANON = new Set(["completo", "primeiro-nome", "nome-completo", "pseudonimo"]);

// ---- Submissão (POST /submit-historia) ----
router.post("/", upload.single("audio"), async (req, res, next) => {
  try {
    const b = req.body || {};
    const titulo = String(b.titulo || "").trim();
    const resumo = String(b.resumo || "").trim();
    const tipo = String(b.tipo || "").trim();
    const anonimato = String(b.anonimato || "completo").trim();
    const email = String(b.email || "").trim().toLowerCase();
    const freguesiaNome = String(b.freguesia || "").trim();
    const lat = b.lat ? Number(b.lat) : null;
    const lng = b.lng ? Number(b.lng) : null;

    // Validação estrita (Bloco 3.1)
    if (!titulo || titulo.length > 120) return res.status(400).json({ erro: "título inválido (1-120 chars)" });
    if (!resumo || resumo.length > 300) return res.status(400).json({ erro: "resumo inválido (1-300 chars)" });
    if (!TIPOS.has(tipo)) return res.status(400).json({ erro: "tipo inválido" });
    if (!ANON.has(anonimato)) return res.status(400).json({ erro: "anonimato inválido" });
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return res.status(400).json({ erro: "email inválido" });

    // Consentimentos obrigatórios (GDPR + CC-BY-SA + arquivo)
    const cc = b.consent_cc_by_sa === "true" || b.consent_cc_by_sa === "on";
    const priv = b.consent_privacidade === "true" || b.consent_privacidade === "on";
    const arq = b.consent_arquivo === "true" || b.consent_arquivo === "on";
    if (!cc || !priv || !arq) return res.status(400).json({ erro: "consentimentos obrigatórios em falta" });

    // Sanitização XSS simples (Bloco 7.1)
    const sane = (s) => String(s).replace(/[<>]/g, "").slice(0, 4000);

    const nomeSubmissor = anonimato === "completo" ? null : sane(b.nome || "");

    // Resolver freguesia (se fornecida)
    let fregId = null;
    if (freguesiaNome) {
      const fr = await pool.query(
        "SELECT id FROM freguesia WHERE nome ILIKE $1 OR codigo_dgal = $2 LIMIT 1",
        [freguesiaNome, freguesiaNome]
      );
      if (fr.rows.length) fregId = fr.rows[0].id;
    }

    const id = uuidv4();
    const audioPath = req.file ? path.relative(UPLOAD_DIR, req.file.path) : null;
    const audioMime = req.file ? req.file.mimetype : null;

    // Certificado de autenticidade (JWT RS256 + SHA-256) — Bloco 7.1
    const { token, hash } = gerarCertificado({ id, titulo, tipo, email });

    await pool.query(
      `INSERT INTO historia
        (id, titulo, resumo, tipo, freguesia_id, freguesia_nome, lat, lng,
         audio_path, audio_mime, anonimato, nome_submissor, email_submissor,
         consent_cc_by_sa, consent_privacidade, consent_arquivo,
         estado, cert_token, cert_hash)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,'submetida',$17,$18)`,
      [id, titulo, resumo, tipo, fregId, freguesiaNome, lat, lng,
       audioPath, audioMime, anonimato, nomeSubmissor, email,
       cc, priv, arq, token, hash]
    );

    // Audit log append-only (Bloco 7.1)
    await pool.query(
      "INSERT INTO audit_log (actor, acao, entidade, entidade_id, depois, ip) VALUES ($1,$2,$3,$4,$5,$6)",
      [email, "submeter_historia", "historia", id, { titulo, tipo, freguesia: freguesiaNome }, req.ip]
    );

    // NLP assíncrono (não bloqueia a resposta) — Bloco 4.1/6.1
    analisarHistoria(id, resumo).catch((e) => console.error("[nlp]", e));

    res.status(201).json({
      status: "submetida",
      id,
      cert_token: token,
      cert_hash: hash,
      mensagem: "História recebida. Será avaliada por curadoria antes da publicação.",
    });
  } catch (e) {
    next(e);
  }
});

// ---- Listagem pública (GET /api/historias) ----
router.get("/", async (req, res, next) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 50, 200);
    const tipo = req.query.tipo;
    const params = [];
    let where = "visibilidade_publica = TRUE AND removed_at IS NULL";
    if (tipo) { params.push(tipo); where += ` AND tipo = $${params.length}`; }
    const rows = await pool.query(
      `SELECT id, titulo, resumo, tipo, freguesia_nome, lat, lng, anonimato,
              nome_submissor, published_at
       FROM historia WHERE ${where}
       ORDER BY published_at DESC NULLS LAST LIMIT $${params.length + 1}`,
      [...params, limit]
    );
    res.json({ historias: rows.rows });
  } catch (e) { next(e); }
});

// ---- Detalhe público (GET /api/historias/:id) ----
router.get("/:id", async (req, res, next) => {
  try {
    const r = await pool.query(
      `SELECT id, titulo, resumo, tipo, freguesia_nome, lat, lng, anonimato,
              nome_submissor, corpo, cert_hash, published_at
       FROM historia WHERE id = $1 AND visibilidade_publica = TRUE AND removed_at IS NULL`,
      [req.params.id]
    );
    if (!r.rows.length) return res.status(404).json({ erro: "história não encontrada" });
    res.json(r.rows[0]);
  } catch (e) { next(e); }
});

export default router;
