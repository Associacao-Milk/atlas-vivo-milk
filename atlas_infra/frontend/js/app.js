// Atlas Vivo MILK — app principal (orquestra tabs + módulos)
import { initMap, renderMapTab } from "./map.js";
import { renderForm } from "./form.js";
import { renderExplorar } from "./explorar.js";
import { renderJogar } from "./gamification.js";

const pane = document.getElementById("pane");
const statusEl = document.getElementById("status");
const announceEl = document.getElementById("announce");
let map;

function announce(msg) {
  announceEl.textContent = msg;
  setTimeout(() => (announceEl.textContent = ""), 1200);
}

async function loadStats() {
  try {
    const r = await fetch("/api/map/stats");
    if (!r.ok) return;
    const s = await r.json();
    statusEl.textContent = `${s.publicadas} histórias publicadas • ${s.total} submetidas`;
  } catch { /* silencioso */ }
}

document.querySelectorAll(".tabs button").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((x) => {
      x.classList.remove("active");
      x.setAttribute("aria-selected", "false");
    });
    b.classList.add("active");
    b.setAttribute("aria-selected", "true");
    const t = b.dataset.tab;
    if (t === "map") renderMapTab(pane, map);
    if (t === "partilhar") renderForm(pane, map, announce);
    if (t === "explorar") renderExplorar(pane, map);
    if (t === "jogar") renderJogar(pane, announce);
  });
});

(async function init() {
  map = await initMap("map");
  await loadStats();
  renderMapTab(pane, map);
})();
