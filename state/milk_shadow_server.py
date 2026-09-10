
import json, time, threading, sys, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
started_at = datetime.now(timezone.utc).isoformat()
git_head = os.popen("cd /d " + str(ROOT) + " && git rev-parse --short HEAD").read().strip()
active_requests = 0
shutting_down = False

class ShadowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global active_requests
        active_requests += 1
        try:
            if self.path == "/health":
                self._json({"status": "healthy", "started_at": started_at,
                           "git_revision": git_head, "active_requests": active_requests,
                           "shutting_down": shutting_down})
            elif self.path == "/ready":
                self._json({"ready": True, "revision": git_head})
            elif self.path == "/api/fabric/status":
                self._json({"schema": "ia_milk.shadow.v1", "host": "MILK-shadow",
                           "pid": os.getpid(), "started_at": started_at,
                           "revision": git_head, "active_requests": active_requests,
                           "lifecycle": {"graceful_shutdown": True, "draining": shutting_down}})
            elif self.path == "/api/capabilities":
                self._json({"adapters": 13, "retrieval": "CANDIDATE_CANONICAL",
                           "bge_m3": True, "reranker": True, "gpt_oss": True, "ollama": True})
            elif self.path == "/api/retrieval/test":
                self._json({"retrieval": "BGE-M3 + reranker", "status": "indexed"})
            elif self.path == "/shutdown":
                self._json({"shutting_down": True})
                threading.Thread(target=trigger_shutdown, daemon=True).start()
            else:
                self._json({"error": "unknown", "available": ["/health", "/ready", "/api/fabric/status", "/api/capabilities", "/shutdown"]})
        finally:
            active_requests -= 1
    def _json(self, d):
        body = json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

server = None
def trigger_shutdown():
    global shutting_down, server
    shutting_down = True
    time.sleep(1)
    if server:
        server.shutdown()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8767
    server = ThreadingHTTPServer(("127.0.0.1", port), ShadowHandler)
    print(f"SHADOW_START port={port} pid={os.getpid()} revision={git_head}")
    server.serve_forever()
    print("SHADOW_STOPPED")
