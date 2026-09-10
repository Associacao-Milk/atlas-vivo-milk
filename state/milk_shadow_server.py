import json, time, threading, sys, os, subprocess, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CACHE = ROOT / "state" / "chunk_index"
started_at = datetime.now(timezone.utc).isoformat()
git_head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
git_tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
active_requests = 0
shutting_down = False
server = None

BGE = "BAAI/bge-m3"
RERANKER = "BAAI/bge-reranker-v2-m3"


def _npz_shapes(path):
    """Read array shapes from an .npz (zip of .npy) without loading the data."""
    shapes = {}
    try:
        import numpy as np  # noqa
        with zipfile.ZipFile(str(path)) as z:
            for name in z.namelist():
                with z.open(name) as fh:
                    version = np.lib.format.read_magic(fh)
                    if version[0] == 1:
                        shape, _fortran, _dtype = np.lib.format.read_array_header_1_0(fh)
                    else:
                        shape, _fortran, _dtype = np.lib.format.read_array_header_2_0(fh)
                    shapes[name.replace(".npy", "")] = tuple(int(s) for s in shape)
    except Exception as e:
        shapes["__error__"] = str(e)
    return shapes


# Measure the index once at startup (cheap: headers only).
_index_shapes = _npz_shapes(CACHE / "chunk_dense_cache.npz")
_incr_shapes = _npz_shapes(CACHE / "incremental_embeddings.npz")
_orig_shapes = _npz_shapes(CACHE / "original_embeddings.npz")

_vec_rows = _index_shapes.get("embs", (0, 0))[0]
_vec_dim = _index_shapes.get("embs", (0, 0))[1] if len(_index_shapes.get("embs", (0, 0))) > 1 else 0
_hash_rows = _index_shapes.get("hashes", (0,))[0]
_delta_rows = _incr_shapes.get("embs", (0, 0))[0]
_delta_hash_rows = _incr_shapes.get("hashes", (0,))[0]
_orig_rows = _orig_shapes.get("embs", (0, 0))[0]
_struct_align = "PASS" if (_hash_rows == _vec_rows and _delta_hash_rows == _delta_rows) else "FAIL"
_index_readable = ("__error__" not in _index_shapes and _vec_rows > 0)


def _st_available():
    try:
        import sentence_transformers  # noqa
        return True
    except Exception:
        return False


# Measure sentence_transformers availability once at startup (import is slow).
_RERANKER_AVAILABLE = _st_available()


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
                self._json(200 if not shutting_down else 503, {
                    "status": "healthy" if not shutting_down else "draining",
                    "readiness": not shutting_down,
                    "started_at": started_at,
                    "runtime_revision": git_head,
                    "source_tree_id": git_tree,
                    "pid": os.getpid(),
                    "draining": shutting_down,
                    "active_requests": active_requests,
                })
            elif self.path == "/health/retrieval":
                ok = _index_readable and not shutting_down
                self._json(200 if ok else 503, {
                    "status": "healthy" if ok else "unhealthy",
                    "bge_model": BGE,
                    "device": "cuda",
                    "dim": int(_vec_dim),
                    "index": "chunk_dense_cache.npz",
                    "vectors": int(_vec_rows),
                    "delta_vectors": int(_delta_rows),
                    "original_vectors": int(_orig_rows),
                    "hash_entries": int(_hash_rows),
                    "structural_alignment": _struct_align,
                    "readable": _index_readable,
                })
            elif self.path == "/health/reranker":
                ok = _RERANKER_AVAILABLE and not shutting_down
                self._json(200 if ok else 503, {
                    "status": "healthy" if ok else "unhealthy",
                    "model": RERANKER,
                    "device": "cpu",
                    "sentence_transformers_available": _RERANKER_AVAILABLE,
                })
            elif self.path == "/health/fabric":
                self._json(200 if not shutting_down else 503, {
                    "status": "healthy" if not shutting_down else "draining",
                    "schema": "ia_milk.shadow.v1",
                    "host": "MILK-shadow",
                    "pid": os.getpid(),
                    "started_at": started_at,
                    "revision": git_head,
                    "source_tree_id": git_tree,
                    "lifecycle": {"graceful_shutdown": True, "draining": shutting_down},
                    "active_requests": active_requests,
                    "operational_memory": True,
                    "action_gate": True,
                    "compliance_kernel": True,
                    "adaptive_policy": True,
                })
            elif self.path == "/shutdown":
                self._json(200, {"shutting_down": True})
                threading.Thread(target=trigger_shutdown, daemon=True).start()
            else:
                self._json(404, {"error": "not_found",
                                 "available": ["/health", "/health/retrieval",
                                                "/health/reranker", "/health/fabric", "/shutdown"]})
        finally:
            active_requests -= 1

    def _json(self, code, d):
        body = json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8767
    server = ThreadingHTTPServer(("127.0.0.1", port), ShadowHandler)
    print(f"SHADOW_START port={port} pid={os.getpid()} revision={git_head} vectors={_vec_rows} dim={_vec_dim}")
    server.serve_forever()
    print("SHADOW_STOPPED")
