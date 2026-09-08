"""Webapp só de leitura do Atlas — grafo factual do corpus.

Servidor HTTP em stdlib puro (sem Flask/FastAPI), consistente com o núcleo
soberano: bind a 127.0.0.1, sem escritas, sem envio remoto ao Mistral. A
recuperação é léxica local; a síntese remota permanece bloqueada por defeito,
como no CLI.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

from .atlas_graph import build_graph
from .ingest import CorpusStore
from .retrieval import HybridRetriever


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Copia apenas campos de apresentação; segredos já são quarentenados no ingest."""
    keys = (
        "source_id", "original_name", "original_path", "sha256", "size_bytes",
        "ingested_at", "visibility", "epistemic_state", "author",
        "responsible_entity", "territory", "district", "municipality", "parish",
        "document_type", "curatorial_device", "rights_status", "consent_status",
        "rgpd_status", "human_validated", "validated_by", "validation_date",
        "notes",
    )
    return {key: metadata.get(key) for key in keys if key in metadata}


class AtlasHandler(BaseHTTPRequestHandler):
    server_version = "MilkAtlas/1.0"

    # Silenciar o log ruidoso padrão; manter um traço mínimo.
    def log_message(self, format: str, *args: Any) -> None:
        pass

    @property
    def store(self) -> CorpusStore:
        return self.server.store  # type: ignore[attr-defined]

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: str, status: int = HTTPStatus.OK) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _not_found(self) -> None:
        self._send_json({"erro": "endpoint desconhecido"}, HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:  # noqa: N802 - interface stdlib
        path = self.path.split("?", 1)
        route = unquote(path[0])
        params: dict[str, str] = {}
        if len(path) == 2:
            parsed = parse_qs(path[1], keep_blank_values=True)
            params = {key: value[0] for key, value in parsed.items()}

        if route == "/":
            self._send_html(ATLAS_HTML)
            return
        if route == "/api/graph":
            self._send_json(build_graph(self.store.documents()))
            return
        if route == "/api/status":
            documents = self.store.documents()
            self._send_json({
                "documentos": len(documents),
                "chunks": sum(len(doc.get("chunks", [])) for doc in documents),
                "quarentena": len(list((self.store.root / "quarantine").glob("*.json"))),
            })
            return
        if route == "/api/documents":
            self._send_json([
                _safe_metadata(doc.get("metadata", {}))
                for doc in self.store.documents()
            ])
            return
        if route == "/api/document":
            source_id = params.get("id", "")
            doc = self._find_document(source_id)
            if doc is None:
                self._send_json({"erro": "fonte não encontrada"}, HTTPStatus.NOT_FOUND)
                return
            chunks = [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "ordinal": chunk.get("ordinal"),
                    "heading": chunk.get("heading"),
                    "sha256": chunk.get("sha256"),
                    "text": chunk.get("text", ""),
                }
                for chunk in doc.get("chunks", [])
            ]
            self._send_json({
                "metadata": _safe_metadata(doc.get("metadata", {})),
                "provenance_paths": doc.get("provenance_paths", []),
                "governance_log": doc.get("governance_log", []),
                "chunks": chunks,
            })
            return
        if route == "/api/query":
            question = params.get("q", "").strip()
            try:
                limit = max(1, min(int(params.get("limit", "5")), 50))
            except ValueError:
                limit = 5
            if not question:
                self._send_json({"hits": [], "aviso": "pergunta vazia"})
                return
            retriever = HybridRetriever(self.store.chunks())
            hits = retriever.search(question, limit=limit)
            self._send_json({
                "pergunta": question,
                "hits": [
                    {
                        "chunk_id": hit.chunk_id,
                        "source_id": hit.source_id,
                        "score": round(hit.score, 4),
                        "lexical_score": round(hit.lexical_score, 4),
                        "heading": hit.metadata.get("heading"),
                        "text": hit.text,
                        "visibility": hit.metadata.get("visibility"),
                    }
                    for hit in hits
                ],
            })
            return
        self._not_found()

    def _find_document(self, source_id: str) -> dict[str, Any] | None:
        if not source_id:
            return None
        for doc in self.store.documents():
            if doc.get("metadata", {}).get("source_id") == source_id:
                return doc
        return None


def serve(state_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> int:
    store = CorpusStore(state_dir / "corpus")
    server = ThreadingHTTPServer((host, port), AtlasHandler)
    server.store = store  # type: ignore[attr-defined]
    print(f"Atlas: http://{host}:{port}  (state_dir={state_dir})  — só leitura, Ctrl+C para parar")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAtlas: a parar...")
    finally:
        server.server_close()
    return 0


# Página única auto-contida: grafo factual interactivo em Canvas + painel de
# detalhe/consulta. Sem bibliotecas externas, coerente com o núcleo soberano.
ATLAS_HTML = r"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MILK AI — Atlas</title>
<style>
  :root{
    --bg:#0f1115; --panel:#161a21; --ink:#e6e8ee; --muted:#8a93a3;
    --line:#262b36; --accent:#6aa0ff; --green:#5fcf80; --amber:#e0b341; --red:#e06a6a;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
    font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
  #app{display:grid;grid-template-columns:1fr 420px;height:100vh}
  #stage{position:relative;overflow:hidden}
  canvas{display:block;width:100%;height:100%}
  #side{background:var(--panel);border-left:1px solid var(--line);display:flex;
    flex-direction:column;min-width:0}
  header{padding:14px 16px;border-bottom:1px solid var(--line)}
  header h1{margin:0;font-size:15px;font-weight:600}
  header .sub{color:var(--muted);font-size:12px;margin-top:2px}
  .tabs{display:flex;border-bottom:1px solid var(--line)}
  .tabs button{flex:1;background:none;border:0;color:var(--muted);padding:10px;
    cursor:pointer;font-size:13px;border-bottom:2px solid transparent}
  .tabs button.active{color:var(--ink);border-bottom-color:var(--accent)}
  .pane{flex:1;overflow:auto;padding:12px 14px}
  .row{padding:9px 0;border-bottom:1px solid var(--line);cursor:pointer}
  .row:hover{background:#1c212b}
  .row .t{font-weight:600}
  .row .m{color:var(--muted);font-size:12px}
  .badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;
    background:#222732;color:var(--muted);margin-left:6px}
  .badge.v-publica{color:var(--green)}
  .badge.v-licenciavel{color:var(--accent)}
  .badge.v-restrita{color:var(--amber)}
  .badge.v-invisivel{color:var(--red)}
  input,button{font:inherit;color:var(--ink)}
  input[type=text]{width:100%;background:#0f1217;border:1px solid var(--line);
    border-radius:5px;padding:8px 10px;outline:none}
  input[type=text]:focus{border-color:var(--accent)}
  .btn{background:var(--accent);color:#0b1220;border:0;border-radius:5px;
    padding:8px 14px;cursor:pointer;font-weight:600}
  .hit{padding:10px 0;border-bottom:1px solid var(--line)}
  .hit .h{display:flex;justify-content:space-between;font-size:12px;color:var(--muted)}
  .hit .txt{margin-top:4px;white-space:pre-wrap}
  .chunk{padding:8px 0;border-bottom:1px solid var(--line)}
  .chunk .oh{font-size:12px;color:var(--muted)}
  .chunk .ot{margin-top:4px;white-space:pre-wrap;max-height:160px;overflow:auto}
  .empty{color:var(--muted);padding:20px 0;text-align:center}
  #legend{position:absolute;left:12px;bottom:12px;background:rgba(15,17,21,.82);
    border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:12px}
  #legend .li{display:flex;align-items:center;gap:7px;margin:3px 0}
  .dot{width:10px;height:10px;border-radius:50%}
</style>
</head>
<body>
<div id="app">
  <div id="stage">
    <canvas id="graph"></canvas>
    <div id="legend">
      <div class="li"><span class="dot" style="background:var(--accent)"></span>fonte</div>
      <div class="li"><span class="dot" style="background:var(--green)"></span>chunk</div>
      <div class="li"><span class="dot" style="background:var(--amber)"></span>metadado</div>
      <div class="li"><span class="dot" style="background:var(--muted)"></span>proveniência</div>
    </div>
  </div>
  <div id="side">
    <header>
      <h1>Atlas factual</h1>
      <div class="sub" id="status">a carregar…</div>
    </header>
    <div class="tabs">
      <button data-tab="graph" class="active">Grafo</button>
      <button data-tab="docs">Fontes</button>
      <button data-tab="query">Consulta</button>
    </div>
    <div class="pane" id="pane"></pane>
  </div>
</div>
<script>
const $ = s => document.querySelector(s);
const pane = $('#pane');
const statusEl = $('#status');
let graphData = null;
let selNode = null;
const COLORS = {fonte:'#6aa0ff', chunk:'#5fcf80', metadado:'#e0b341', proveniencia:'#8a93a3'};

async function jget(url){
  const r = await fetch(url);
  if(!r.ok) throw new Error(r.status);
  return r.json();
}

function badge(v){
  const cls = (v||'').toString().replace(/\s/g,'-');
  return `<span class="badge v-${cls}">${v||'—'}</span>`;
}

/* ---------- status ---------- */
async function loadStatus(){
  try{
    const s = await jget('/api/status');
    statusEl.textContent = `${s.documentos} fontes · ${s.chunks} chunks · ${s.quarentena} em quarentena`;
  }catch(e){ statusEl.textContent = 'indisponível'; }
}

/* ---------- tabs ---------- */
document.querySelectorAll('.tabs button').forEach(b=>{
  b.onclick = ()=>{
    document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    const t = b.dataset.tab;
    if(t==='graph') renderGraphInfo();
    if(t==='docs') renderDocs();
    if(t==='query') renderQuery();
  };
});

/* ---------- fontes ---------- */
async function renderDocs(){
  pane.innerHTML = '<div class="empty">a carregar fontes…</div>';
  try{
    const docs = await jget('/api/documents');
    if(!docs.length){ pane.innerHTML = '<div class="empty">corpus vazio</div>'; return; }
    pane.innerHTML = docs.map(d=>`
      <div class="row" data-id="${d.source_id}">
        <div class="t">${d.original_name||d.source_id.slice(0,18)} ${badge(d.visibility)}</div>
        <div class="m">${d.source_id.slice(0,24)}… · ${d.epistemic_state||'—'}</div>
      </div>`).join('');
    pane.querySelectorAll('.row').forEach(r=>{
      r.onclick = ()=>openDoc(r.dataset.id);
    });
  }catch(e){ pane.innerHTML = '<div class="empty">erro ao carregar</div>'; }
}

async function openDoc(id){
  pane.innerHTML = '<div class="empty">a carregar detalhe…</div>';
  try{
    const d = await jget('/api/document?id='+encodeURIComponent(id));
    const m = d.metadata||{};
    let html = `<div style="margin-bottom:10px">
      <div class="t" style="font-size:15px">${m.original_name||id}</div>
      <div class="m">${id}</div>
      <div style="margin-top:6px">${badge(m.visibility)} ${badge(m.epistemic_state)}
        ${badge('RGPD:'+(m.rgpd_status||'—'))}</div>
      <div class="m" style="margin-top:4px">sha256: ${m.sha256||'—'}</div>
    </div>`;
    if(d.provenance_paths?.length){
      html += '<div class="m">proveniência</div>';
      d.provenance_paths.forEach(p=> html += `<div class="m" style="word-break:break-all">${p}</div>`);
    }
    if(d.governance_log?.length){
      html += '<div class="m" style="margin-top:8px">registo de governança</div>';
      d.governance_log.forEach(g=> html += `<div class="m">${g.timestamp} — ${g.actor}</div>`);
    }
    html += `<div class="m" style="margin-top:10px">chunks (${d.chunks.length})</div>`;
    d.chunks.forEach(c=>{
      html += `<div class="chunk">
        <div class="oh">#${c.ordinal} · ${c.heading||'—'}</div>
        <div class="ot">${c.text||''}</div></div>`;
    });
    pane.innerHTML = html;
  }catch(e){ pane.innerHTML = '<div class="empty">fonte não encontrada</div>'; }
}

/* ---------- consulta ---------- */
function renderQuery(){
  pane.innerHTML = `
    <input type="text" id="q" placeholder="pergunta ao corpus (léxico local)…">
    <div style="margin:8px 0"><button class="btn" id="qgo">Consultar</button></div>
    <div id="qout"></div>`;
  const run = async ()=>{
    const q = $('#q').value.trim();
    if(!q) return;
    $('#qout').innerHTML = '<div class="empty">a procurar…</div>';
    try{
      const r = await jget('/api/query?q='+encodeURIComponent(q)+'&limit=8');
      if(!r.hits.length){ $('#qout').innerHTML = '<div class="empty">sem evidência suficiente</div>'; return; }
      $('#qout').innerHTML = r.hits.map(h=>`
        <div class="hit">
          <div class="h"><span>${h.heading||'—'}</span><span>score ${h.score}</span></div>
          <div class="txt">${(h.text||'').slice(0,500)}</div>
        </div>`).join('');
    }catch(e){ $('#qout').innerHTML = '<div class="empty">erro na consulta</div>'; }
  };
  $('#qgo').onclick = run;
  $('#q').onkeydown = e=>{ if(e.key==='Enter') run(); };
  $('#q').focus();
}

/* ---------- grafo ---------- */
async function loadGraph(){
  graphData = await jget('/api/graph');
}

function renderGraphInfo(){
  if(!graphData){ pane.innerHTML = '<div class="empty">a carregar grafo…</div>'; return; }
  const s = graphData.summary||{};
  let html = `<div class="t">Resumo do grafo</div>
    <div class="m">${s.documents} fontes · ${s.chunks} chunks</div>
    <div class="m">${s.nodes} nós · ${s.edges} arestas</div>
    <div class="m">${graphData.generated_at}</div>`;
  if(selNode){
    const n = selNode;
    html += `<div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--line)">
      <div class="t">${n.tipo}</div>`;
    Object.entries(n).forEach(([k,v])=>{
      if(k==='id'||k==='tipo') return;
      html += `<div class="m">${k}: ${String(v).slice(0,80)}</div>`;
    });
    const neighbours = (graphData.edges||[]).filter(e=>e.origem===n.id||e.destino===n.id);
    html += `<div class="m" style="margin-top:6px">${neighbours.length} relações</div>`;
    html += '</div>';
  }
  pane.innerHTML = html;
}

/* canvas force-directed */
let canvas, ctx, W, H, nodes, edges, drag=null;
function initCanvas(){
  canvas = $('#graph');
  ctx = canvas.getContext('2d');
  resize();
  window.addEventListener('resize', resize);
  canvas.addEventListener('mousedown', e=>{
    const p = ptr(e);
    for(let i=nodes.length-1;i>=0;i--){
      const n=nodes[i];
      if(Math.hypot(n.x-p.x,n.y-p.y)<n.r+3){ drag=n; return; }
    }
  });
  canvas.addEventListener('mousemove', e=>{
    if(drag){ drag.x=ptr(e).x; drag.y=ptr(e).y; drag.vx=0; drag.vy=0; }
  });
  window.addEventListener('mouseup', ()=>{ drag=null; });
  canvas.addEventListener('click', e=>{
    const p = ptr(e);
    for(let i=nodes.length-1;i>=0;i--){
      const n=nodes[i];
      if(Math.hypot(n.x-p.x,n.y-p.y)<n.r+3){ selNode=n; renderGraphInfo(); return; }
    }
  });
}
function ptr(e){
  const r = canvas.getBoundingClientRect();
  return {x:(e.clientX-r.left), y:(e.clientY-r.top)};
}
function resize(){
  const s = $('#stage');
  W = s.clientWidth; H = s.clientHeight;
  const dpr = window.devicePixelRatio||1;
  canvas.width = W*dpr; canvas.height = H*dpr;
  canvas.style.width = W+'px'; canvas.style.height = H+'px';
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
function buildNodes(){
  const raw = graphData.nodes||[];
  nodes = raw.map(n=>{
    const r = n.tipo==='fonte'?7: n.tipo==='chunk'?4: n.tipo==='metadado'?3:5;
    return Object.assign(n, {
      x: W/2 + (Math.random()-0.5)*W*0.6,
      y: H/2 + (Math.random()-0.5)*H*0.6,
      vx:0, vy:0, r
    });
  });
  const byId = {}; nodes.forEach(n=>byId[n.id]=n);
  edges = (graphData.edges||[]).map(e=>({s:byId[e.origem], t:byId[e.destino], r:e.relacao}))
    .filter(e=>e.s&&e.t);
}
function tick(){
  if(!nodes) return;
  const REPEL = 600, SPRING = 0.012, LEN = 70, DAMP = 0.85, GRAV = 0.02;
  for(const n of nodes){
    if(n===drag) continue;
    n.vx += (W/2 - n.x)*GRAV; n.vy += (H/2 - n.y)*GRAV;
  }
  for(let i=0;i<nodes.length;i++){
    for(let j=i+1;j<nodes.length;j++){
      const a=nodes[i], b=nodes[j];
      let dx=a.x-b.x, dy=a.y-b.y; let d2=dx*dx+dy*dy+0.01;
      let f=REPEL/d2; let d=Math.sqrt(d2);
      let fx=f*dx/d, fy=f*dy/d;
      if(a!==drag){a.vx-=fx;a.vy-=fy;}
      if(b!==drag){b.vx+=fx;b.vy+=fy;}
    }
  }
  for(const e of edges){
    const a=e.s,b=e.t;
    let dx=b.x-a.x, dy=b.y-a.y; let d=Math.sqrt(dx*dx+dy*dy)+0.01;
    let f=(d-LEN)*SPRING;
    let fx=f*dx/d, fy=f*dy/d;
    if(a!==drag){a.vx+=fx;a.vy+=fy;}
    if(b!==drag){b.vx-=fx;b.vy-=fy;}
  }
  for(const n of nodes){
    if(n===drag) continue;
    n.vx*=DAMP; n.vy*=DAMP;
    n.x+=n.vx; n.y+=n.vy;
    n.x=Math.max(n.r,Math.min(W-n.r,n.x));
    n.y=Math.max(n.r,Math.min(H-n.r,n.y));
  }
}
function draw(){
  ctx.clearRect(0,0,W,H);
  ctx.strokeStyle='rgba(106,160,255,0.18)'; ctx.lineWidth=1;
  for(const e of edges){
    ctx.beginPath(); ctx.moveTo(e.s.x,e.s.y); ctx.lineTo(e.t.x,e.t.y); ctx.stroke();
  }
  for(const n of nodes){
    ctx.beginPath(); ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
    ctx.fillStyle = COLORS[n.tipo]||'#888';
    if(n===selNode){ ctx.lineWidth=2; ctx.strokeStyle='#fff'; ctx.stroke(); }
    ctx.fill();
  }
}
function loop(){ if(nodes){ tick(); draw(); } requestAnimationFrame(loop); }

(async function init(){
  initCanvas();
  await loadStatus();
  await loadGraph();
  if((graphData.nodes||[]).length>1200){
    /* limita densidade para não saturar o canvas em corpora grandes */
    graphData.nodes = graphData.nodes.slice(0,1200);
    const keep = new Set(graphData.nodes.map(n=>n.id));
    graphData.edges = graphData.edges.filter(e=>keep.has(e.origem)&&keep.has(e.destino));
  }
  buildNodes();
  renderGraphInfo();
  loop();
})();
</script>
</body>
</html>
"""
