// Gamificação — perfil + leaderboard (Bloco 5.1)
export function renderJogar(pane, announce) {
  pane.innerHTML = `
    <h2 style="margin:0 0 8px">Jogar</h2>
    <p class="m">Ganha pontos e badges a partilhar histórias e a curar as dos outros.</p>

    <label for="g-email">Email</label>
    <input id="g-email" type="email" placeholder="o-seu-email@exemplo.pt">
    <button class="btn" id="g-ver">Ver o meu perfil</button>

    <div id="gPerfil" style="margin-top:14px"></div>

    <h3 style="margin-top:18px">Leaderboard</h3>
    <label for="g-ccdr">Região (CCDR)</label>
    <select id="g-ccdr">
      <option value="">Todas</option>
      <option value="CCDR-N">Norte</option>
      <option value="CCDR-C">Centro</option>
      <option value="CCDR-A">Alentejo</option>
      <option value="CCDR-ALG">Algarve</option>
      <option value="CCDR-AÇ">Açores</option>
      <option value="CCDR-M">Madeira</option>
    </select>
    <div id="gBoard" class="m" style="margin-top:10px">A carregar…</div>
  `;

  document.getElementById("g-ver").addEventListener("click", async () => {
    const email = document.getElementById("g-email").value.trim().toLowerCase();
    if (!email) return;
    try {
      const r = await fetch(`/api/gamificacao/perfil?email=${encodeURIComponent(email)}`);
      if (!r.ok) {
        // registar e tentar de novo
        await fetch("/api/gamificacao/registar", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        announce("Perfil criado");
      }
      const r2 = await fetch(`/api/gamificacao/perfil?email=${encodeURIComponent(email)}`);
      const p = await r2.json();
      document.getElementById("gPerfil").innerHTML = `
        <div class="row">
          <div class="t">${esc(p.nome || "Anónimo")}</div>
          <div class="m">${p.pontos} pontos • nível ${p.nivel}</div>
          <div class="m">Histórias: ${p.historias_submetidas} • validadas: ${p.historias_validadas}</div>
          <div class="m">Badges: ${(p.badges || []).map((b) => `<span class="badge">${esc(b)}</span>`).join("") || "—"}</div>
        </div>`;
    } catch { announce("Erro ao carregar perfil"); }
  });

  async function carregarBoard() {
    const ccdr = document.getElementById("g-ccdr").value;
    try {
      const r = await fetch(`/api/gamificacao/leaderboard?limit=20${ccdr ? `&ccdr=${ccdr}` : ""}`);
      const d = await r.json();
      const board = document.getElementById("gBoard");
      board.innerHTML = (d.leaderboard || []).map((u, i) => `
        <div class="row" style="cursor:default">
          <div class="t">${i + 1}. ${esc(u.nome || "Anónimo")}</div>
          <div class="m">${u.pontos} pontos • nível ${u.nivel}</div>
        </div>`).join("") || "Sem dados ainda";
    } catch { document.getElementById("gBoard").innerHTML = "Erro"; }
  }

  document.getElementById("g-ccdr").addEventListener("change", carregarBoard);
  carregarBoard();
}

function esc(s) {
  return String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}
