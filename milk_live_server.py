#!/usr/bin/env python3
"""MILK IA — Live monitoring server (stdlib http.server + SSE).

Serve /milk-live, /api/milk/status, /api/milk/training/status,
/api/milk/training/events (SSE). Reads state/training_live.json.
"""
from __future__ import annotations
import sys, os, json, time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
STATE = ROOT / "state"
LIVE_FILE = STATE / "training_live.json"
PORT = 8766

def read_live():
    if LIVE_FILE.exists():
        try:
            return json.loads(LIVE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

LIVE_HTML = """<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<title>MILK IA — Live</title>
<style>
body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:20px}
h1{color:#58a6ff;font-size:1.4em;margin:0 0 16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:900px}
.card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px}
.label{color:#8b949e;font-size:0.75em;text-transform:uppercase;letter-spacing:0.5px}
.value{color:#58a6ff;font-size:1.1em;font-weight:bold;margin-top:2px}
.pclass{display:inline-block;margin:2px 6px;padding:2px 8px;border-radius:4px;background:#21262d;font-size:0.8em}
.on{color:#3fb950}.off{color:#f85149}.warn{color:#d29922}
.bar{height:6px;background:#30363d;border-radius:3px;margin-top:4px;overflow:hidden}
.bar>div{height:100%;background:#58a6ff;border-radius:3px}
table{width:100%;border-collapse:collapse;font-size:0.85em}
td,th{padding:4px 8px;text-align:left;border-bottom:1px solid #21262d}
th{color:#8b949e;font-size:0.75em}
</style></head>
<body>
<h1>MILK IA — Monitorizacao Ao Vivo</h1>
<div id="content">A carregar...</div>
<script>
async function poll(){
  try{
    const r=await fetch('/api/milk/training/status');
    const d=await r.json();
    let h='<div class="grid">';
    const row=(l,v,c)=>`<div class="card"><div class="label">${l}</div><div class="value ${c||''}">${v}</div></div>`;
    h+=row('HOST',d.host||'—');
    h+=row('PID',d.pid||'—');
    h+=row('DEVICE',d.device||'—');
    h+=row('GPU',d.gpu||'CPU',d.cuda?'on':'');
    h+=row('CUDA',d.cuda?'SIM':'NAO',d.cuda?'on':'off');
    h+=row('STATUS',d.status||'—',d.status==='TRAINING'?'on':d.status?.startsWith('DONE')?'warn':'');
    h+=row('EPOCH',`${d.epoch||0}/${d.total_epochs||20}`);
    const ep_pct=d.total_epochs?((d.epoch||0)/d.total_epochs*100):0;
    h+=`<div class="card" style="grid-column:span 2"><div class="label">EPOCH PROGRESS</div><div class="bar"><div style="width:${ep_pct}%"></div></div></div>`;
    h+=row('TRAIN LOSS',d.train_loss??'—');
    h+=row('VAL LOSS',d.val_loss??'—');
    h+=row('VAL F1 MACRO',d.val_f1_macro??'—');
    h+=row('VAL F1 MICRO',d.val_f1_micro??'—');
    h+=row('CLASSES ATIVAS',`${d.val_classes_detected||0}/11`);
    h+=row('HAMMING',d.val_hamming??'—');
    h+=row('DOCS PROCESSADOS',d.docs_processed?.toLocaleString()||0);
    h+=row('BATCHES',d.batches_processed||0);
    h+=row('BASE MODEL SHA',(d.base_model_sha||'—').slice(0,16));
    h+=row('TRAIN MODEL SHA',(d.training_model_sha||'—').slice(0,16));
    h+=row('CHECKPOINT SHA',(d.checkpoint_sha||'—').slice(0,16));
    h+=row('GPU/VRAM',d.vram_used_gb!=null?`${d.vram_used_gb} GB`:'—');
    h+=row('CPU',d.cpu_pct!=null?`${d.cpu_pct}%`:'—');
    h+=row('RAM',d.ram_pct!=null?`${d.ram_pct}%`:'—');
    h+=row('TEMPO',d.elapsed_s!=null?`${d.elapsed_s}s`:'—');
    h+=row('HEARTBEAT',(d.heartbeat||'—').slice(11,19));
    h+='</div>';
    if(d.per_class&&d.per_class.length){
      h+='<h3 style="color:#8b949e;margin-top:16px;font-size:0.9em">F1 POR CLASSE</h3><table>';
      h+='<tr><th>Classe</th><th>Precision</th><th>Recall</th><th>F1</th><th>TP</th><th>FP</th><th>FN</th></tr>';
      for(const c of d.per_class){
        const cls=c.f1>0?'on':'off';
        h+=`<tr><td class="${cls}">${c.class}</td><td>${c.precision}</td><td>${c.recall}</td><td class="${cls}">${c.f1}</td><td>${c.tp}</td><td>${c.fp}</td><td>${c.fn}</td></tr>`;
      }
      h+='</table>';
    }
    document.getElementById('content').innerHTML=h;
  }catch(e){document.getElementById('content').innerHTML='<p class="off">Erro: '+e+'</p>'}
}
poll();setInterval(poll,3000);
</script></body></html>"""


class LiveHandler(BaseHTTPRequestHandler):
    server_version = "MilkLive/1.0"

    def log_message(self, *a): pass

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body, status=HTTPStatus.OK):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = unquote(self.path.split("?")[0])
        if route == "/milk-live":
            self._send_html(LIVE_HTML); return
        if route == "/api/milk/status":
            d = read_live()
            self._send_json({"status": d.get("status", "IDLE"), "pid": d.get("pid"),
                             "device": d.get("device"), "gpu": d.get("gpu"),
                             "heartbeat": d.get("heartbeat")}); return
        if route == "/api/milk/training/status":
            self._send_json(read_live()); return
        if route == "/api/milk/training/events":
            self._send_sse(); return
        self._send_json({"error": "unknown endpoint"}, HTTPStatus.NOT_FOUND)

    def _send_sse(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last_hb = None
        for _ in range(600):
            d = read_live()
            hb = d.get("heartbeat")
            if hb != last_hb:
                last_hb = hb
                self.wfile.write(f"data: {json.dumps(d, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
            time.sleep(2)
        self.wfile.write(b"event: close\ndata: timeout\n\n")


def serve(port=PORT):
    server = ThreadingHTTPServer(("127.0.0.1", port), LiveHandler)
    print(f"MILK LIVE SERVER on http://127.0.0.1:{port}")
    print(f"  /milk-live               — dashboard HTML")
    print(f"  /api/milk/status         — status JSON")
    print(f"  /api/milk/training/status — training status JSON")
    print(f"  /api/milk/training/events — SSE stream")
    server.serve_forever()

if __name__ == "__main__":
    serve()
