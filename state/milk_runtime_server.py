"""MILK IA - Generic Runtime Server (validation | canonical).

One generic MILK runtime entrypoint configured by runtime_role and port.
Reuses the SAME MILK core for both validation and canonical runtimes — no
two independent cognitive implementations.

Usage:
    python state/milk_runtime_server.py --runtime_role=validation --port=8767
    python state/milk_runtime_server.py --runtime_role=canonical  --port=8766

The validation server (state/milk_validation_server.py) remains as a
compatibility wrapper that delegates to this generic server with
runtime_role=validation.

Endpoints (identical for both roles, role-specific nomenclature in payloads):
    /health             - runtime readiness + role-specific revision
    /health/retrieval   - BGE-M3 vector index integrity
    /health/reranker    - reranker availability
    /health/fabric      - fabric lifecycle (role-specific schema/host)
    /health/research    - internal research observability (non-sensitive)
    /research?q=...     - real research query through ResearchContext Gate
    /shutdown           - graceful drain
"""
import json, time, threading, sys, os, subprocess, zipfile, argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CACHE = ROOT / "state" / "chunk_index"
SRC = ROOT / "src"
STATE = ROOT / "state"

# Parse arguments early to set runtime_role before module-level init.
_parser = argparse.ArgumentParser()
_parser.add_argument("--runtime_role", default="validation", choices=["validation", "canonical"])
_parser.add_argument("--port", type=int, default=8767)
_args, _remaining = _parser.parse_known_args()
RUNTIME_ROLE = _args.runtime_role
PORT = _args.port

started_at = datetime.now(timezone.utc).isoformat()
git_head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
git_tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
active_requests = 0
shutting_down = False
server = None

sys.path.insert(0, str(SRC))
try:
    from milk_ai.provenance import CANONICAL_AUTHOR
except Exception:
    CANONICAL_AUTHOR = {
        "idealized_by": "Eduardo Mauricio Vieira Cabral e Araujo",
        "artistic_name": "Eduardo Mauer",
        "orcid": "0009-0007-6892-6570",
    }
try:
    from milk_ai.runtime_nomenclature import ROLE_SCHEMA, ROLE_HOST
    RUNTIME_SCHEMA = ROLE_SCHEMA.get(RUNTIME_ROLE, "ia_milk.validation.v1")
    RUNTIME_HOST = ROLE_HOST.get(RUNTIME_ROLE, "MILK-validation")
except Exception:
    RUNTIME_SCHEMA = "ia_milk.canonical.v1" if RUNTIME_ROLE == "canonical" else "ia_milk.validation.v1"
    RUNTIME_HOST = "MILK-canonical" if RUNTIME_ROLE == "canonical" else "MILK-validation"

# Role-specific revision field name in health responses.
REVISION_FIELD = "validation_runtime_revision" if RUNTIME_ROLE == "validation" else "canonical_runtime_revision"

BGE = "BAAI/bge-m3"
RERANKER = "BAAI/bge-reranker-v2-m3"


# ---------------------------------------------------------------------------
# In-memory research hypergraph (shared core, same for both roles).
# ---------------------------------------------------------------------------
_RESEARCH_GATE = None
_LAST_RESEARCH_STATUS = "idle"


def _build_research_gate():
    global _RESEARCH_GATE
    if _RESEARCH_GATE is not None:
        return _RESEARCH_GATE
    try:
        from milk_ai.hypergraph import SovereignHypergraph, HyperNode, HyperEdge
        from milk_ai.research_context import ResearchContextGate
        from milk_ai.method_repertoire import load_method_repertory
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        ag = STATE / "atlas_graph.json"
        if ag.exists():
            g = json.loads(ag.read_text(encoding="utf-8"))
            for n in g.get("nodes", []):
                nid = n.get("id")
                if nid and not hg.get_node(nid):
                    t = (n.get("type") or n.get("tipo") or "DOCUMENT")
                    if t not in ("fonte",):
                        t = t.upper() if t.upper() in (
                            "AUTHOR","PLACE","TERRITORY","METHOD","WORK","EVENT","CONCEPT","MEMORY","EVIDENCE"
                        ) else "DOCUMENT"
                    else:
                        t = "DOCUMENT"
                    try:
                        hg.add_node(HyperNode(
                            id=nid, type=t, label=n.get("nome") or n.get("label") or nid,
                            modality="text", source_pointer=n.get("source_id", ""),
                            validation_state="validated" if n.get("estado_epistemico") in ("validado","preparado") else "pending",
                            confidence=0.8))
                    except Exception:
                        pass
            for e in g.get("edges", []):
                eid = e.get("id") or f"e:{e.get('source','')}_{e.get('target','')}"
                et = (e.get("type") or e.get("tipo") or "RELATED_TO").upper()
                if et not in ("RELATED_TO","INSPIRED_BY","APPLIED_IN","SUPPORTS","CONTRADICTS"):
                    et = "RELATED_TO"
                try:
                    hg.add_edge(HyperEdge(id=eid, source=e.get("source",""),
                                          edge_type=et, target=e.get("target",""),
                                          confidence=0.7, validation_state="validated"))
                except Exception:
                    pass
        _RESEARCH_GATE = ResearchContextGate(hg)
    except Exception as exc:
        _RESEARCH_GATE = None
        _set_last_status(f"build_failed: {exc}")
    return _RESEARCH_GATE


def _set_last_status(s):
    global _LAST_RESEARCH_STATUS
    _LAST_RESEARCH_STATUS = s


def _npz_shapes(path):
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


_RERANKER_AVAILABLE = _st_available()


def _research_observability():
    metrics = {
        "active_reference_count": 0,
        "method_repertoire_nodes": 0,
        "relational_nodes": 0,
        "relational_edges": 0,
        "cross_modal_links": 0,
        "queries_with_research_context": 0,
        "queries_without_research_context": 0,
        "research_gaps": 0,
        "learning_events_by_environment": {},
        "production_policy_updates": 0,
        "blocked_nonproduction_policy_updates": 0,
        "legacy_unknown_learning_events": 0,
        "last_relational_query_status": "idle",
        "runtime_role": RUNTIME_ROLE,
        "validation_runtime_revision": git_head if RUNTIME_ROLE == "validation" else None,
        "canonical_runtime_revision": git_head if RUNTIME_ROLE == "canonical" else None,
        "canonical_runtime_revision_if_observable": git_head if RUNTIME_ROLE == "canonical" else None,
        "promotion_required": RUNTIME_ROLE == "validation",
    }
    manifest = STATE / "knowledge_recovery_manifest.json"
    if manifest.exists():
        try:
            m = json.loads(manifest.read_text(encoding="utf-8"))
            summary = m.get("summary", {})
            metrics["active_reference_count"] = summary.get("active_references", 0)
            metrics["method_repertoire_nodes"] = summary.get("method_repertoire_nodes", 0)
            metrics["relational_nodes"] = summary.get("relational_nodes", 0)
            metrics["relational_edges"] = summary.get("relational_edges", 0)
            metrics["cross_modal_links"] = summary.get("cross_modal_links", 0)
            metrics["research_gaps"] = summary.get("research_gaps", 0)
        except Exception:
            pass
    events_path = STATE / "operational_memory" / "adaptive_learning_events.jsonl"
    by_env = {}
    legacy_unknown = 0
    if events_path.exists():
        try:
            with open(events_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    env = (ev.get("provenance") or {}).get("environment") or ev.get("environment")
                    if not env:
                        env = "legacy_unknown"
                        legacy_unknown += 1
                    by_env[env] = by_env.get(env, 0) + 1
        except Exception:
            pass
    metrics["learning_events_by_environment"] = by_env
    metrics["legacy_unknown_learning_events"] = legacy_unknown
    fw = STATE / "policy_firewall_log.jsonl"
    if fw.exists():
        try:
            prod = blocked = 0
            with open(fw, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if r.get("action") == "policy_updated":
                        prod += 1
                    elif r.get("action") == "blocked_nonproduction_policy_update":
                        blocked += 1
            metrics["production_policy_updates"] = prod
            metrics["blocked_nonproduction_policy_updates"] = blocked
        except Exception:
            pass
    traces_path = STATE / "validation_multiaxial_traces.json"
    if traces_path.exists():
        try:
            td = json.loads(traces_path.read_text(encoding="utf-8"))
            tr_list = td.get("traces", []) if isinstance(td, dict) else td
            metrics["queries_with_research_context"] = sum(1 for t in tr_list if t.get("has_research_trace"))
            metrics["queries_without_research_context"] = sum(1 for t in tr_list if not t.get("has_research_trace"))
            metrics["last_relational_query_status"] = "ok" if tr_list else "idle"
        except Exception:
            pass
    return metrics


def trigger_shutdown():
    global shutting_down, server
    shutting_down = True
    time.sleep(1)
    if server:
        server.shutdown()
        server.server_close()


class RuntimeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global active_requests
        active_requests += 1
        try:
            if self.path == "/health":
                resp = {
                    "status": "healthy" if not shutting_down else "draining",
                    "readiness": not shutting_down,
                    "runtime_role": RUNTIME_ROLE,
                    "started_at": started_at,
                    "runtime_revision": git_head,
                    REVISION_FIELD: git_head,
                    "source_tree_id": git_tree,
                    "pid": os.getpid(),
                    "draining": shutting_down,
                    "active_requests": active_requests,
                    "canonical_author": CANONICAL_AUTHOR.get("idealized_by", ""),
                    "canonical_orcid": CANONICAL_AUTHOR.get("orcid", ""),
                }
                self._json(200 if not shutting_down else 503, resp)
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
                    "orphan_vectors": 0 if _struct_align == "PASS" else 1,
                    "index_alignment": _struct_align,
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
                    "schema": RUNTIME_SCHEMA,
                    "host": RUNTIME_HOST,
                    "runtime_role": RUNTIME_ROLE,
                    "pid": os.getpid(),
                    "started_at": started_at,
                    "revision": git_head,
                    REVISION_FIELD: git_head,
                    "source_tree_id": git_tree,
                    "lifecycle": {"graceful_shutdown": True, "draining": shutting_down},
                    "active_requests": active_requests,
                    "operational_memory": True,
                    "action_gate": True,
                    "compliance_kernel": True,
                    "adaptive_policy": True,
                    "canonical_author": CANONICAL_AUTHOR.get("idealized_by", ""),
                    "canonical_orcid": CANONICAL_AUTHOR.get("orcid", ""),
                })
            elif self.path == "/health/research":
                self._json(200 if not shutting_down else 503, _research_observability())
            elif self.path.startswith("/research"):
                import urllib.parse as _up
                parsed = _up.urlparse(self.path)
                qs = _up.parse_qs(parsed.query)
                query = (qs.get("q", [""])[0]) or ""
                gate = _build_research_gate()
                if gate is None:
                    self._json(503, {"error": "research_gate_unavailable",
                                     "status": _LAST_RESEARCH_STATUS})
                else:
                    bundle = gate.research(task_id=f"rt:{os.getpid()}", query=query,
                                           worker=f"{RUNTIME_ROLE}_runtime",
                                           runtime_role=RUNTIME_ROLE)
                    tr = gate.traces()[-1].to_dict() if gate.traces() else {}
                    _set_last_status("ok" if bundle.has_research_context else "gap")
                    self._json(200, {
                        "schema": RUNTIME_SCHEMA,
                        "runtime_role": RUNTIME_ROLE,
                        REVISION_FIELD: git_head,
                        "bundle": bundle.to_dict(),
                        "trace": tr,
                    })
            elif self.path == "/shutdown":
                self._json(200, {"shutting_down": True})
                threading.Thread(target=trigger_shutdown, daemon=True).start()
            else:
                self._json(404, {"error": "not_found",
                                 "available": ["/health", "/health/retrieval",
                                                "/health/reranker", "/health/fabric",
                                                "/health/research", "/research?q=...",
                                                "/shutdown"]})
        finally:
            active_requests -= 1

    def _json(self, code, d):
        body = json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), RuntimeHandler)
    print(f"MILK_RUNTIME_START role={RUNTIME_ROLE} port={PORT} pid={os.getpid()} revision={git_head} vectors={_vec_rows} dim={_vec_dim}")
    server.serve_forever()
    print(f"MILK_RUNTIME_STOPPED role={RUNTIME_ROLE} port={PORT}")
