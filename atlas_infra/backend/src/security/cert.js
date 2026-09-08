// Certificado de autenticidade — JWT RS256 + SHA-256 (Bloco 7.1)
import fs from "node:fs";
import crypto from "node:crypto";
import jwt from "jsonwebtoken";

const PRIV_PATH = process.env.JWT_PRIVATE_KEY_PATH || "";
const PUB_PATH = process.env.JWT_PUBLIC_KEY_PATH || "";
const ISSUER = process.env.JWT_ISSUER || "atlas.milk.pt";
const EXPIRES_DAYS = Number(process.env.JWT_EXPIRES_DAYS || 3650);

let privKey = "";
try { privKey = fs.readFileSync(PRIV_PATH, "utf-8"); } catch { /* fallback HS256 simbólico */ }

// Gera cert-token (JWT) + cert-hash (SHA-256 do payload) para uma história.
// O certificado prova a autenticidade e imutabilidade da submissão.
export function gerarCertificado({ id, titulo, tipo, email }) {
  const payload = {
    sub: id,
    titulo,
    tipo,
    iss: ISSUER,
    iat: Math.floor(Date.now() / 1000),
    licenca: "CC-BY-SA-4.0",
  };
  const hash = crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex");

  let token;
  if (privKey && privKey.includes("PRIVATE KEY")) {
    token = jwt.sign(payload, privKey, { algorithm: "RS256", expiresIn: `${EXPIRES_DAYS}d` });
  } else {
    // Fallback simétrico se não houver chave RS256 configurada (não usar em produção final)
    token = jwt.sign(payload, ISSUER, { algorithm: "HS256", expiresIn: `${EXPIRES_DAYS}d` });
  }
  return { token, hash };
}

// Verifica um cert-token (usado por curadoria / auditoria)
export function verificarCertificado(token) {
  try {
    if (privKey && privKey.includes("PRIVATE KEY")) {
      const pubKey = fs.readFileSync(PUB_PATH, "utf-8");
      return jwt.verify(token, pubKey, { algorithms: ["RS256"], issuer: ISSUER });
    }
    return jwt.verify(token, ISSUER, { algorithms: ["HS256"], issuer: ISSUER });
  } catch {
    return null;
  }
}
