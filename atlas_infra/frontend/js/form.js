// Formulário multi-step de submissão (Bloco 1.1 + 3.1)
// 5 passos: identidade → território → história → áudio → consentimentos
import { gravarAudio } from "./audio.js";

export function renderForm(pane, map, announce) {
  pane.innerHTML = `
    <h2 style="margin:0 0 8px">Partilhar uma história</h2>
    <div class="progress" role="progressbar" aria-valuemin="1" aria-valuemax="5" aria-valuenow="1">
      <div class="progress-bar" id="progBar"></div>
    </div>
    <form id="formHistoria" enctype="multipart/form-data">

      <!-- Passo 1: identidade -->
      <div class="step active" data-step="1">
        <label for="f-nome">Nome (opcional)</label>
        <input id="f-nome" name="nome" type="text" autocomplete="name">
        <label for="f-email">Email</label>
        <input id="f-email" name="email" type="email" required autocomplete="email">
        <label for="f-anon">Anonimato</label>
        <select id="f-anon" name="anonimato">
          <option value="completo">Anónimo completo</option>
          <option value="primeiro-nome">Primeiro nome</option>
          <option value="nome-completo">Nome completo</option>
          <option value="pseudonimo">Pseudónimo</option>
        </select>
        <button type="button" class="btn" data-next>Seguinte</button>
      </div>

      <!-- Passo 2: território -->
      <div class="step" data-step="2">
        <label for="f-freg">Freguesia (autocomplete DGAL)</label>
        <input id="f-freg" name="freguesia" type="text" list="freguesias" autocomplete="off">
        <datalist id="freguesias"></datalist>
        <p class="m" style="margin:6px 0">Ou escolha no mapa:</p>
        <button type="button" class="btn secondary" id="f-pickmap">Escolher no mapa</button>
        <button type="button" class="btn secondary" data-prev>Voltar</button>
        <button type="button" class="btn" data-next>Seguinte</button>
      </div>

      <!-- Passo 3: história -->
      <div class="step" data-step="3">
        <label for="f-tipo">Tipo</label>
        <select id="f-tipo" name="tipo" required>
          <option value="lenda">Lenda</option>
          <option value="oficio">Ofício</option>
          <option value="memoria">Memória</option>
          <option value="curiosidade">Curiosidade</option>
          <option value="transformacao">Transformação</option>
        </select>
        <label for="f-titulo">Título (máx. 120)</label>
        <input id="f-titulo" name="titulo" type="text" maxlength="120" required>
        <label for="f-resumo">Resumo (máx. 300)</label>
        <textarea id="f-resumo" name="resumo" maxlength="300" rows="4" required></textarea>
        <button type="button" class="btn secondary" data-prev>Voltar</button>
        <button type="button" class="btn" data-next>Seguinte</button>
      </div>

      <!-- Passo 4: áudio -->
      <div class="step" data-step="4">
        <label>Gravar áudio (opcional)</label>
        <div id="audioCtrl"></div>
        <p class="m" style="margin:8px 0">Ou anexe um ficheiro (áudio/vídeo, máx. 500MB):</p>
        <input type="file" name="audio" accept="audio/*,video/*">
        <button type="button" class="btn secondary" data-prev>Voltar</button>
        <button type="button" class="btn" data-next>Seguinte</button>
      </div>

      <!-- Passo 5: consentimentos -->
      <div class="step" data-step="5">
        <div class="checkbox-row">
          <input type="checkbox" id="c-cc" name="consent_cc_by_sa" value="true" required>
          <label for="c-cc" style="margin:0">Aceito licença CC-BY-SA 4.0</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="c-priv" name="consent_privacidade" value="true" required>
          <label for="c-priv" style="margin:0">Aceito a política de privacidade (RGPD)</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="c-arq" name="consent_arquivo" value="true" required>
          <label for="c-arq" style="margin:0">Aceito arquivamento de longo prazo</label>
        </div>
        <button type="button" class="btn secondary" data-prev>Voltar</button>
        <button type="submit" class="btn">Submeter</button>
      </div>

      <div id="formResult"></div>
    </form>
  `;

  const form = document.getElementById("formHistoria");
  let passo = 1;
  const total = 5;

  function ir(n) {
    document.querySelectorAll(".step").forEach((s) => s.classList.remove("active"));
    const target = form.querySelector(`.step[data-step="${n}"]`);
    if (target) target.classList.add("active");
    passo = n;
    const bar = document.getElementById("progBar");
    bar.style.width = `${(n / total) * 100}%`;
    form.parentElement.querySelector("[role=progressbar]").setAttribute("aria-valuenow", n);
    target.querySelector("input,select,textarea,button")?.focus?.();
  }

  form.querySelectorAll("[data-next]").forEach((b) => b.addEventListener("click", () => {
    if (passo < total) ir(passo + 1);
  }));
  form.querySelectorAll("[data-prev]").forEach((b) => b.addEventListener("click", () => {
    if (passo > 1) ir(passo - 1);
  }));

  // Ctrl+Enter avança
  form.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter" && passo < total) ir(passo + 1);
  });

  // Autocomplete DGAL
  const fregInput = document.getElementById("f-freg");
  fregInput.addEventListener("input", async () => {
    const q = fregInput.value.trim();
    if (q.length < 2) return;
    try {
      const r = await fetch(`/api/freguesias?q=${encodeURIComponent(q)}&limit=10`);
      const d = await r.json();
      const dl = document.getElementById("freguesias");
      dl.innerHTML = d.freguesias.map((f) => `<option value="${f.nome} — ${f.municipio}">`).join("");
    } catch {}
  });

  // Picker no mapa
  let pickerMarker = null;
  document.getElementById("f-pickmap").addEventListener("click", () => {
    announce("Clique no mapa para escolher a localização");
    map.once("click", (e) => {
      if (pickerMarker) map.removeLayer(pickerMarker);
      pickerMarker = L.marker(e.latlng).addTo(map);
      const hidden = form.querySelector('input[name="lat"]') || document.createElement("input");
      hidden.type = "hidden"; hidden.name = "lat"; hidden.value = e.latlng.lat; form.appendChild(hidden);
      const h2 = form.querySelector('input[name="lng"]') || document.createElement("input");
      h2.type = "hidden"; h2.name = "lng"; h2.value = e.latlng.lng; form.appendChild(h2);
      announce("Localização registada");
    });
  });

  // Gravar áudio
  gravarAudio(document.getElementById("audioCtrl"), form);

  // Submissão
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const result = document.getElementById("formResult");
    result.innerHTML = '<p class="m">A enviar…</p>';
    try {
      const r = await fetch("/submit-historia", { method: "POST", body: fd });
      const d = await r.json();
      if (r.ok) {
        result.innerHTML = `
          <div class="row" style="border-color:var(--milk-green-dark)">
            <div class="t" style="color:var(--milk-green)">História recebida</div>
            <div class="m">Token: ${d.cert_token?.slice(0,20)}…</div>
            <div class="m">Hash: ${d.cert_hash?.slice(0,24)}…</div>
            <div class="m">${d.mensagem || ""}</div>
          </div>`;
        announce("História submetida com sucesso");
      } else {
        result.innerHTML = `<div class="m" style="color:var(--milk-pink)">${d.erro || "Erro na submissão"}</div>`;
      }
    } catch (err) {
      result.innerHTML = `<div class="m" style="color:var(--milk-pink)">Falha de rede</div>`;
    }
  });
}
