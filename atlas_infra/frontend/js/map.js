// Mapa Leaflet + SNIG + clustering (Bloco 2.1)
// Tiles OSM + camada SNIG opcional + marcadores das histórias publicadas.

export async function initMap(elementId) {
  const map = L.map(elementId, {
    center: [39.5, -8.0],
    zoom: 7,
    zoomControl: true,
    preferCanvas: true,
  });

  // Base OSM
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap",
  }).addTo(map);

  // Camada SNIG ortofoto (DGTerritório) — toggle
  const snig = L.tileLayer.wms(
    "https://snig.dgterritorio.gov.pt/wms-inspire/wms",
    {
      layers: "Ortoimagens_2023_RGB_50cm",
      format: "image/png",
      transparent: true,
      attribution: "© SNIG/DGTerritório",
      maxZoom: 19,
    }
  );

  // Controlo de camadas
  L.control.layers({ "OpenStreetMap": map._layers[Object.keys(map._layers)[0]], "SNIG Ortofoto": snig }, null, { collapsed: true }).addTo(map);

  return map;
}

export function renderMapTab(pane, map) {
  pane.innerHTML = `
    <h2 style="margin:0 0 8px">Atlas Vivo MILK</h2>
    <p class="m">Cartografia afetiva do folclore português. Toque num ponto para ouvir a história.</p>
    <div id="mapLegend">
      <span class="badge lenda">lenda</span>
      <span class="badge oficio">ofício</span>
      <span class="badge memoria">memória</span>
      <span class="badge curiosidade">curiosidade</span>
      <span class="badge transformacao">transformação</span>
    </div>
    <div id="mapStats" class="m" style="margin-top:12px">A carregar histórias…</div>
  `;
  carregarMarcadores(map);
}

async function carregarMarcadores(map) {
  try {
    const r = await fetch("/api/map/historias");
    if (!r.ok) return;
    const geo = await r.json();
    const cluster = L.markerClusterGroup();
    const icon = L.divIcon({ className: "marker-milk", iconSize: [18, 18] });
    for (const f of geo.features) {
      const p = f.properties;
      const m = L.marker([f.geometry.coordinates[1], f.geometry.coordinates[0]], { icon });
      m.bindPopup(`
        <strong>${esc(p.titulo)}</strong><br>
        <span class="badge ${esc(p.tipo)}">${esc(p.tipo)}</span><br>
        ${esc(p.resumo)}<br>
        <em>${esc(p.freguesia || "")}</em>
      `);
      cluster.addLayer(m);
    }
    map.addLayer(cluster);
    const statsEl = document.getElementById("mapStats");
    if (statsEl) statsEl.textContent = `${geo.features.length} histórias no mapa`;
  } catch (e) {
    console.error(e);
  }
}

function esc(s) {
  return String(s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}
