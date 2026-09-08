// Watermark canvas overlay — Bloco 7.1
// Gera metadados de marca de água para o frontend aplicar sobre áudio/imagem.
// No frontend, o áudio público é servido com marca de água MILK + hash.

export function watermarkMetadata(historiaId, hash) {
  return {
    texto: `MILK • ${historiaId.slice(0, 8)} • ${hash.slice(0, 12)}`,
    hash,
    timestamp: new Date().toISOString(),
    licenca: "CC-BY-SA-4.0",
  };
}
