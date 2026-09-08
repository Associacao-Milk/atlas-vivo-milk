// Explorar — listagem de histórias publicadas com filtros (Bloco 4.1)
export function renderExplorar(pane, map) {
  pane.innerHTML = `
    <h2 style="margin:0 0 8px">Explorar histórias</h2>
    <input id="exQ" type="text" placeholder="Pesquisar por título, freguesia…">
    <select id="exTipo" style="margin:8px 0">
      <option value="">Todos os tipos</option>
      <option value="lenda">lenda</option>
      <option value="oficio">ofício</option>
      <option value="memoria">memória</option>
      <option value="curiosidade">curiosidade</option>
      <option value="transformacao">transformação</option>
    </select>
    <div id="exResults" class="m">A carregar…</div>
  `;

  let dados = [];
  const q = document.getElementById("exQ");
  const tipo = document.getElementById("exTipo");
  const out = document.getElementById("exResults");

  async function carregar() {
    try {
      const r = await fetch("/api/historias?limit=200");
      const d = await r.json();
      dados = d.historias || [];
      render();
    } catch { out.innerHTML = "Erro ao carregar"; }
  }

  function render() {
    const term = q.value.trim().toLowerCase();
    const t = tipo.value;
    let arr = dados;
    if (t) arr = arr.filter((h) => h.tipo === t);
    if (term) arr = arr.filter((h) => (h.titulo + " " + (h.freguesia_nome || "") + " " + h.resumo).toLowerCase().includes(term));
    out.innerHTML = arr.length
      ? arr.map((h) => `
        <div class="row" data-id="${h.id}">
          <div class="t">${esc(h.titulo)} <span class="badge ${esc(h.tipo)}">${esc(h.tipo)}</span></div>
          <div class="m">${esc(h.freguesia_nome || "")} • ${esc(h.anonimato)}</div>
          <div class="m">${esc(h.resumo).slice(0,120)}</div>
        </div>`).join("")
      : '<div class="m">Sem resultados</div>';
    out.querySelectorAll(".row").forEach((r) => {
      r.addEventListener("click", () => abrirHistoria(r.dataset.id, map));
    });
  }

  async function abrirHistoria(id, map) {
    try {
      const r = await fetch(`/api/historias/${id}`);
      const h = await r.json();
      if (h.lat && h.lng) map.panTo([h.lat, h.lng]);
      out.innerHTML = `
        <button class="btn secondary" id="exVoltar">Voltar</button>
        <h3 style="margin-top:12px">${esc(h.titulo)}</h3>
        <span class="badge ${esc(h.tipo)}">${esc(h.tipo)}</span>
        <p>${esc(h.resumo)}</p>
        ${h.corpo ? `<p>${esc(h.corpo)}</p>` : ""}
        <p class="m">Cert hash: ${esc(h.cert_hash?.slice(0,24))}…</p>
        <p class="m">Freguesia: ${esc(h.freguesia_nome || "—")}</p>
      `;
      document.getElementById("exVoltar").addEventListener("click", () => { carregar(); });
    } catch {}
  }

  q.addEventListener("input", render);
  tipo.addEventListener("change", render);
  carregar();
}

function esc(s) {
  return String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}
