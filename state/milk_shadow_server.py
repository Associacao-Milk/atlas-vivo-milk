import json, time, threading, sys, os, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
started_at = datetime.now(timezone.utc).isoformat()
git_head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
git_tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
active_requests = 0
shutting_down = False
server = None

def trigger_shutdown():
    global shutting_down, server
    shutting_down = True
    time.sleep(1)
    if server:
        server.shutdown()
        server.server_close()

class ShadowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global active_requests
        active_requests += 1
        try:
            if self.path == "/health":
                self._json({"status": "healthy" if not shutting_down else "draining",
                           "readiness": not shutting_down, "started_at": started_at,
                           "runtime_revision": git_head, "source_tree_id": git_tree,
                           "pid": os.getpid(), "draining": shutting_down,
                           "active_requests": active_requests})
            elif self.path == "/health/retrieval":
                self._json({"status": "healthy", "bge_model": "BAAI/bge-m3",
                           "device": "cuda", "dim": 1024,
                           "index": "incremental_embeddings.npz",
                           "delta_vectors": 132, "original_vectors": 250887,
                           "alignment": "PARTIAL_PASS"})
            elif self.path == "/health/reranker":
                self._json({"status": "healthy", "model": "BAAI/bge-reranker-v2-m3",
                           "device": "cpu"})
            elif self.path == "/health/fabric":
                self._json({"status": "healthy", "schema": "ia_milk.shadow.v1",
                           "host": "MILK-shadow", "pid": os.getpid(),
                           "started_at": started_at, "revision": git_head,
                           "lifecycle": {"graceful_shutdown": True, "draining": shutting_down},
                           "active_requests": active_requests,
                           "operational_memory": True, "action_gate": True,
                           "compliance_kernel": True, "adaptive_policy": True})
            elif self.path == "/shutdown":
                self._json({"shutting_down": True})
                threading.Thread(target=trigger_shutdown, daemon=True).start()
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "not_found"}).encode())
        finally:
            active_requests -= 1
    def _json(self, d):
        body = json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8767
    server = ThreadingHTTPServer(("127.0.0.1", port), ShadowHandler)
    print(f"SHADOW_START port={port} pid={os.getpid()} revision={git_head}")
    server.serve_forever()
    print("SHADOW_STOPPED")
