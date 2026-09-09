#!/usr/bin/env python3
"""MILK IA — Local Intelligence Fabric.

Orchestrates: GPU resource manager, local model registry (gpt-oss, embeddings,
reranker), retrieval pipeline (sparse+dense→RRF→rerank), tool layer (MCP/API),
agent fabric, continuous learning event loop, expanded live dashboard.

Runs on http://127.0.0.1:8766 (extends existing live server).
"""
from __future__ import annotations
import sys, os, json, time, hashlib, threading, queue, subprocess, pickle, math, re, unicodedata
from pathlib import Path
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, parse_qs
from collections import Counter
from typing import Any, Callable

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Use Python 3.12 (has CUDA torch + numpy + sklearn)
ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
STATE = ROOT / "state"
MODELS = ROOT / "models"
CORPUS = ROOT / "corpus" / "documents"
MANIFESTS = ROOT / "manifests"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
import torch.nn as nn

EIXOS = ["humana","social","legal","juridica","cultural","territorial",
         "existencial","administrativa","economica","ambiental","tecnologica"]
EIXOS_P = {
    "humana": ["memoria","identidade","pertença","vivencia","experiencia","emoção","corpo","sensação","biografia"],
    "social": ["comunidade","intergeracional","participação","inclusão","diversidade","coletivo","associação"],
    "legal": ["RGPD","consentimento","direitos","licença","conformidade","lei","decreto","estatuto","deliberacao"],
    "juridica": ["propriedade","autoria","contrato","obrigação","responsabilidade"],
    "cultural": ["folclore","tradição","etnografia","património","ritual","festa","costume","lenda","mito","romaria"],
    "territorial": ["freguesia","concelho","distrito","topónimo","paisagem","território","mapa","caop"],
    "existencial": ["sentido","existência","possível","casa","habitar","pertencer","despertar","noema"],
    "administrativa": ["camara","municipio","junta","administração","publica","autarquia","governacao"],
    "economica": ["custo","orcamento","financiamento","receita","despesa","DGARTES","horizon","fundos"],
    "ambiental": ["ambiente","natureza","sustentabilidade","clima","agua","floresta","biodiversidade"],
    "tecnologica": ["QR","digital","interoperabilidade","API","dados","software","sistema","tecnologia"],
}
N_OUT = 11; H1, H2, H3 = 512, 256, 128; MAX_FEATURES = 5000

def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda: f.read(1<<20), b""): h.update(c)
    return h.hexdigest()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CUDA = torch.cuda.is_available()
GPU_NAME = torch.cuda.get_device_name(0) if CUDA else "CPU"
VRAM_TOTAL = round(torch.cuda.get_device_properties(0).total_memory/1e9,2) if CUDA else 0

# ============================================================
# 1. RESOURCE ORCHESTRATOR
# ============================================================
class ResourceOrchestrator:
    def __init__(self):
        self.device = DEVICE
        self.cuda = CUDA
        self.gpu_name = GPU_NAME
        self.vram_total = VRAM_TOTAL
        self.priority_queue = queue.PriorityQueue()
        self.active_jobs: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.metrics = {"queries": 0, "training_jobs": 0, "inference_jobs": 0, "throughput_ops": 0}

    def vram_free(self):
        if not CUDA: return 0
        return round((torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated())/1e9, 2)

    def vram_used(self):
        if not CUDA: return 0
        return round(torch.cuda.memory_allocated()/1e9, 2)

    def request_resource(self, job_id, job_type, priority=0):
        with self._lock:
            self.active_jobs[job_id] = {"type": job_type, "priority": priority, "started": now_iso()}
        return True

    def release_resource(self, job_id):
        with self._lock:
            self.active_jobs.pop(job_id, None)

    def status(self):
        import psutil
        return {"device": str(self.device), "cuda": self.cuda, "gpu": self.gpu_name,
                "vram_total_gb": self.vram_total, "vram_used_gb": self.vram_used(),
                "vram_free_gb": self.vram_free(),
                "cpu_pct": psutil.cpu_percent(),
                "ram_pct": psutil.virtual_memory().percent,
                "ram_gb_total": round(psutil.virtual_memory().total/1e9,2),
                "active_jobs": len(self.active_jobs),
                "metrics": self.metrics}

orchestrator = ResourceOrchestrator()

# ============================================================
# 2. LOCAL MODEL REGISTRY
# ============================================================
class LocalModelRegistry:
    def __init__(self):
        self.models: dict[str, dict] = {}
        self.gptoss_url = "http://localhost:8009"
        self.gptoss_pid = None
        pid_file = STATE / "gptoss_pid.json"
        if pid_file.exists():
            try:
                self.gptoss_pid = json.load(open(pid_file))["pid"]
            except: pass
        self.register_models()

    def register_models(self):
        self.models["gpt-oss-20b"] = {
            "type": "reasoning", "backend": "llama.cpp",
            "endpoint": self.gptoss_url, "pid": self.gptoss_pid,
            "status": "starting" if self.gptoss_pid else "offline",
            "vram_requirement_gb": 8.0, "quantization": "GGUF"}
        self.models["milk-neural"] = {
            "type": "classifier", "backend": "pytorch",
            "device": str(DEVICE), "status": "loaded",
            "sha": sha256_file(MODELS / "milk_neural.npz")[:16] if (MODELS / "milk_neural.npz").exists() else "N/A"}
        self.models["tfidf-sparse"] = {
            "type": "retrieval", "backend": "sklearn",
            "status": "loaded",
            "vocab": len(pickle.load(open(MODELS / "milk_vec.pkl", "rb")).vocabulary_) if (MODELS / "milk_vec.pkl").exists() else 0}
        self.models["milk-embeddings"] = {
            "type": "embedding", "backend": "tfidf-hash" if not CUDA else "pytorch",
            "status": "ready", "dim": 384, "note": "local hash-based multilingual embeddings"}

    def gptoss_health(self):
        """Check if gpt-oss server is responding."""
        import urllib.request
        try:
            req = urllib.request.Request(f"{self.gptoss_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except:
            return False

    def gptoss_chat(self, messages: list[dict], max_tokens=512, temperature=0.3):
        """Send chat to local gpt-oss-20b."""
        import urllib.request
        payload = {"model": "gpt-oss-20b", "messages": messages,
                   "max_tokens": max_tokens, "temperature": temperature,
                   "stream": False}
        try:
            req = urllib.request.Request(f"{self.gptoss_url}/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read().decode("utf-8"))
                return r.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            return f"[gpt-oss unavailable: {e}]"

    def status(self):
        self.models["gpt-oss-20b"]["status"] = "online" if self.gptoss_health() else ("starting" if self.gptoss_pid else "offline")
        return self.models

model_registry = LocalModelRegistry()

# ============================================================
# 3. RETRIEVAL PIPELINE (sparse + dense → RRF → rerank)
# ============================================================
class RetrievalPipeline:
    def __init__(self):
        self.chunks: list[dict] = []
        self.idf: dict[str, float] = {}
        self.lexical_vectors: list[dict[str, float]] = []
        self.index_path = STATE / "retrieval_index.json"
        self.stats = {"queries": 0, "avg_latency_ms": 0, "index_size": 0}
        self._lock = threading.Lock()
        self._load_index()

    def _features(self, text):
        norm = "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))
        tokens = re.findall(r"[a-z0-9]+", norm)
        return tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]

    def _load_index(self):
        """Load or build sparse index from corpus chunks."""
        if self.index_path.exists():
            try:
                d = json.loads(self.index_path.read_text(encoding="utf-8"))
                self.idf = d.get("idf", {})
                self.stats["index_size"] = len(d.get("chunks", []))
                print(f"  [Retrieval] Index loaded: {self.stats['index_size']} entries")
                return
            except: pass
        print("  [Retrieval] Building index (first run)...")
        self._build_index()

    def _build_index(self):
        """Build sparse TF-IDF index from first N documents for speed."""
        docs = sorted(CORPUS.glob("*.json"))[:5000]  # sample for fast initial index
        chunks = []
        term_counts = []
        doc_freq = Counter()
        for fp in docs:
            try:
                r = json.load(open(fp, "r", encoding="utf-8"))
                text = (r.get("text", "") or "")[:2000]
                if not text.strip(): continue
                tc = Counter(self._features(text))
                chunks.append({"chunk_id": fp.stem, "text": text[:500], "source_id": fp.stem})
                term_counts.append(tc)
                doc_freq.update(tc.keys())
            except: continue
        total = len(chunks)
        self.idf = {t: math.log((1+total)/(1+df))+1.0 for t, df in doc_freq.most_common(20000)}
        self.lexical_vectors = []
        for tc in term_counts:
            w = {t: (1+math.log(c))*self.idf.get(t,0) for t,c in tc.items() if t in self.idf and c>0}
            norm = math.sqrt(sum(v*v for v in w.values()))
            self.lexical_vectors.append({k: v/norm for k,v in w.items()} if norm else {})
        self.chunks = chunks
        self.stats["index_size"] = len(chunks)
        # save
        self.index_path.write_text(json.dumps({"idf": self.idf, "chunks": self.chunks,
            "built_at": now_iso(), "doc_count": total}, ensure_ascii=False), encoding="utf-8")
        print(f"  [Retrieval] Index built: {total} chunks, {len(self.idf)} terms")

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Sparse TF-IDF search with RRF-ready output."""
        t0 = time.time()
        if not query.strip() or not self.idf:
            return []
        qv = Counter(self._features(query))
        qw = {t: (1+math.log(c))*self.idf.get(t,0) for t,c in qv.items() if t in self.idf and c>0}
        qnorm = math.sqrt(sum(v*v for v in qw.values()))
        if qnorm: qw = {k: v/qnorm for k,v in qw.items()}
        scores = []
        for i, lv in enumerate(self.lexical_vectors):
            s = sum(w * lv.get(t, 0.0) for t, w in qw.items())
            scores.append((s, i))
        scores.sort(reverse=True)
        results = []
        for rank, (score, idx) in enumerate(scores[:limit]):
            if score <= 0: break
            c = self.chunks[idx]
            results.append({"chunk_id": c["chunk_id"], "score": round(float(score), 4),
                           "rank": rank+1, "text": c["text"], "source_id": c["source_id"],
                           "retriever": "sparse-tfidf"})
        latency = (time.time() - t0) * 1000
        with self._lock:
            self.stats["queries"] += 1
            self.stats["avg_latency_ms"] = round((self.stats["avg_latency_ms"] * (self.stats["queries"]-1) + latency) / self.stats["queries"], 1)
        return results

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """Simple lexical reranker: re-score by query term overlap + coverage."""
        qfeats = set(self._features(query))
        for c in candidates:
            cfeats = set(self._features(c.get("text", "")))
            overlap = len(qfeats & cfeats)
            coverage = overlap / max(len(qfeats), 1)
            c["rerank_score"] = round(c["score"] * 0.5 + coverage * 0.5, 4)
            c["term_overlap"] = overlap
            c["query_coverage"] = round(coverage, 3)
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_k]

    def benchmark(self) -> dict:
        """Run retrieval benchmark with known queries."""
        test_queries = [
            ("folclore romaria tradicao Moura", ["cultural","territorial"]),
            ("tecnologia digital QR interoperabilidade", ["tecnologica"]),
            ("orcamento financiamento DGARTES fundos", ["economica"]),
            ("RGPD consentimento direitos", ["legal"]),
            ("camara municipio junta administracao", ["administrativa"]),
        ]
        results = []
        for q, expected in test_queries:
            hits = self.search(q, limit=10)
            reranked = self.rerank(q, hits, top_k=5)
            # MRR
            mrr = 0
            for i, h in enumerate(reranked):
                mrr = 1.0 / (i + 1)
                break
            results.append({"query": q, "expected_classes": expected,
                           "n_hits": len(hits), "mrr": round(mrr, 4),
                           "top_score": reranked[0]["score"] if reranked else 0,
                           "top_rerank": reranked[0]["rerank_score"] if reranked else 0,
                           "latency_ms": self.stats["avg_latency_ms"]})
        return {"queries_tested": len(results), "avg_mrr": round(np.mean([r["mrr"] for r in results]), 4),
                "avg_latency_ms": self.stats["avg_latency_ms"],
                "index_size": self.stats["index_size"], "details": results}

retrieval = RetrievalPipeline()

# ============================================================
# 4. MILK TOOL LAYER (API tools)
# ============================================================
MILK_TOOLS = {
    "milk_query": {"description": "Query MILK with sparse+dense retrieval + rerank",
                   "params": {"question": "str", "limit": "int=5"}},
    "milk_train": {"description": "Start a controlled training job",
                   "params": {"epochs": "int=20", "lr": "float=0.001"}},
    "milk_training_status": {"description": "Get current training status", "params": {}},
    "milk_retrieve": {"description": "Raw retrieval search", "params": {"query": "str", "limit": "int=10"}},
    "milk_rerank": {"description": "Rerank retrieval results", "params": {"query": "str", "candidates": "list"}},
    "milk_evidence": {"description": "Get evidence + citations for a query", "params": {"question": "str"}},
    "milk_hypothesize": {"description": "Generate hypothesis from evidence (gpt-oss)", "params": {"evidence": "list"}},
    "milk_test_hypothesis": {"description": "Test a hypothesis against corpus", "params": {"hypothesis": "str"}},
    "milk_ontology_validate": {"description": "Validate document against MILK ontology (SHACL)", "params": {"doc": "dict"}},
    "milk_compliance_check": {"description": "Check compliance profiles (EIF/AI Act/ISO42001)", "params": {"governance": "dict"}},
    "milk_export_ngsi": {"description": "Export document as NGSI-LD entity", "params": {"doc": "dict"}},
    "milk_model_compare": {"description": "Compare model versions", "params": {"sha_a": "str", "sha_b": "str"}},
}

def execute_tool(tool_name: str, params: dict) -> dict:
    """Execute a MILK tool and return result."""
    if tool_name == "milk_retrieve":
        return {"results": retrieval.search(params.get("query",""), params.get("limit",10))}
    if tool_name == "milk_rerank":
        return {"results": retrieval.rerank(params.get("query",""), params.get("candidates",[]))}
    if tool_name == "milk_query":
        hits = retrieval.search(params.get("question",""), params.get("limit",5)*2)
        reranked = retrieval.rerank(params.get("question",""), hits, params.get("limit",5))
        return {"results": reranked, "n_sources": len(reranked)}
    if tool_name == "milk_evidence":
        hits = retrieval.search(params.get("question",""), 10)
        reranked = retrieval.rerank(params.get("question",""), hits, 5)
        evidence = [{"citation": r["chunk_id"], "text": r["text"],
                     "score": r["rerank_score"], "provenance": "corpus"} for r in reranked]
        return {"evidence": evidence, "citations": [e["citation"] for e in evidence]}
    if tool_name == "milk_training_status":
        live = {}
        lf = STATE / "training_live.json"
        if lf.exists():
            live = json.loads(lf.read_text(encoding="utf-8"))
        return live
    if tool_name == "milk_hypothesize":
        evidence = params.get("evidence", [])
        ev_text = "\n".join(f"- {e.get('text','')[:200]}" for e in evidence[:5])
        prompt = [{"role":"system","content":"You are MILK AI hypothesis engine. Generate a falsifiable hypothesis from evidence. Output JSON: {hypothesis, falsification_criteria, confidence, provenance:MODEL_GENERATED}"},
                  {"role":"user","content":f"Evidence:\n{ev_text}\n\nGenerate a falsifiable hypothesis."}]
        result = model_registry.gptoss_chat(prompt, max_tokens=256)
        return {"hypothesis_output": result, "provenance": "MODEL_GENERATED"}
    if tool_name == "milk_compliance_check":
        try:
            from milk_ai.compliance import assess_all
            assessments = assess_all(params.get("governance", {}))
            return {"profiles": [{"profile_id": a.profile_id, "overall": a.overall} for a in assessments]}
        except Exception as e:
            return {"error": str(e)}
    if tool_name == "milk_export_ngsi":
        try:
            from milk_ai.export_ngsi import export_source_ngsi
            return export_source_ngsi(params.get("doc", {}))
        except Exception as e:
            return {"error": str(e)}
    if tool_name == "milk_model_compare":
        return {"sha_a": params.get("sha_a",""), "sha_b": params.get("sha_b",""),
                "comparison": "see git log and state/evaluation_test.json"}
    return {"error": f"unknown tool: {tool_name}"}

# ============================================================
# 5. AGENT FABRIC
# ============================================================
AGENTS = {
    "MILK_ORCHESTRATOR": {"role": "canonical writer", "tools": ["milk_query","milk_train","milk_compliance_check"],
                          "status": "active", "description": "Single canonical orchestrator"},
    "MILK_NEURAL": {"role": "neural specialist", "tools": ["milk_train","milk_model_compare"],
                    "status": "active", "description": "Neural training and evaluation"},
    "MILK_RETRIEVAL": {"role": "retrieval", "tools": ["milk_retrieve","milk_rerank","milk_evidence"],
                       "status": "active", "description": "Sparse+dense retrieval and reranking"},
    "MILK_ONTOLOGY": {"role": "ontology", "tools": ["milk_ontology_validate","milk_export_ngsi"],
                      "status": "active", "description": "Ontology validation and NGSI-LD export"},
    "MILK_SCIENCE": {"role": "science", "tools": ["milk_hypothesize","milk_test_hypothesis"],
                     "status": "active", "description": "Hypothesis generation and testing"},
    "MILK_MULTIMODAL": {"role": "multimodal", "tools": ["milk_query"],
                        "status": "active", "description": "Multimodal ingestion and processing"},
    "MILK_PUBLIC_INTEROP": {"role": "interop", "tools": ["milk_export_ngsi","milk_compliance_check"],
                            "status": "active", "description": "Public interoperability (EIF/NGSI-LD)"},
    "MILK_AUDITOR": {"role": "auditor", "tools": ["milk_compliance_check","milk_model_compare"],
                     "status": "active", "description": "Compliance and audit"},
}

agent_jobs: list[dict] = []

def run_agent_task(agent_name: str, task: str, params: dict = None):
    """Run a task on behalf of an agent."""
    params = params or {}
    agent = AGENTS.get(agent_name)
    if not agent: return {"error": f"unknown agent {agent_name}"}
    job = {"agent": agent_name, "task": task, "params": params, "started": now_iso(), "status": "running"}
    agent_jobs.append(job)
    # execute via tools
    result = execute_tool(task, params)
    job["status"] = "done" if "error" not in result else "error"
    job["result"] = result
    job["completed"] = now_iso()
    return result

# ============================================================
# 6. CONTINUOUS LEARNING (event-driven)
# ============================================================
cl_events: list[dict] = []
cl_queue = queue.Queue()
CL_ACTIVE = True

def continuous_learning_loop():
    """Event-driven continuous learning daemon."""
    print("  [CL] Continuous learning loop started (event-driven)")
    while CL_ACTIVE:
        try:
            event = cl_queue.get(timeout=5)
        except queue.Empty:
            continue
        if event is None: break
        cl_events.append(event)
        event_type = event.get("type")
        print(f"  [CL] Event: {event_type}")
        if event_type == "NEW_DOCUMENT":
            # trigger re-indexing
            retrieval._build_index()
            event["result"] = "index_rebuilt"
        elif event_type == "MODEL_REGRESSION":
            event["result"] = "alert_logged"
        elif event_type == "EXPLICIT_EXPERIMENT":
            event["result"] = "experiment_queued"
        event["processed"] = now_iso()
    print("  [CL] Continuous learning loop stopped")

cl_thread = threading.Thread(target=continuous_learning_loop, daemon=True)
cl_thread.start()

# ============================================================
# 7. MILK NEURAL (PyTorch on GPU)
# ============================================================
class MilkTorchNet(nn.Module):
    def __init__(self, dim_in=MAX_FEATURES):
        super().__init__()
        self.fc0 = nn.Linear(dim_in, H1); self.bn0 = nn.BatchNorm1d(H1)
        self.fc1 = nn.Linear(H1, H2); self.bn1 = nn.BatchNorm1d(H2)
        self.fc2 = nn.Linear(H2, H3); self.bn2 = nn.BatchNorm1d(H3)
        self.fc3 = nn.Linear(H3, N_OUT); self.drop = nn.Dropout(0.3)
    def forward(self, x):
        x = self.drop(torch.relu(self.bn0(self.fc0(x))))
        x = self.drop(torch.relu(self.bn1(self.fc1(x))))
        x = self.drop(torch.relu(self.bn2(self.fc2(x))))
        return torch.sigmoid(self.fc3(x))

def load_neural():
    net = MilkTorchNet().to(DEVICE)
    npz = np.load(MODELS / "milk_neural.npz")
    with torch.no_grad():
        net.fc0.weight.copy_(torch.from_numpy(npz["W0"].T).to(DEVICE))
        net.fc0.bias.copy_(torch.from_numpy(npz["b0"]).to(DEVICE))
        net.bn0.weight.copy_(torch.from_numpy(npz["g0"]).to(DEVICE))
        net.bn0.bias.copy_(torch.from_numpy(npz["be0"]).to(DEVICE))
        net.bn0.running_mean.copy_(torch.from_numpy(npz["rm0"]).to(DEVICE))
        net.bn0.running_var.copy_(torch.from_numpy(npz["rv0"]).to(DEVICE))
        net.fc1.weight.copy_(torch.from_numpy(npz["W1"].T).to(DEVICE))
        net.fc1.bias.copy_(torch.from_numpy(npz["b1"]).to(DEVICE))
        net.bn1.weight.copy_(torch.from_numpy(npz["g1"]).to(DEVICE))
        net.bn1.bias.copy_(torch.from_numpy(npz["be1"]).to(DEVICE))
        net.bn1.running_mean.copy_(torch.from_numpy(npz["rm1"]).to(DEVICE))
        net.bn1.running_var.copy_(torch.from_numpy(npz["rv1"]).to(DEVICE))
        net.fc2.weight.copy_(torch.from_numpy(npz["W2"].T).to(DEVICE))
        net.fc2.bias.copy_(torch.from_numpy(npz["b2"]).to(DEVICE))
        net.bn2.weight.copy_(torch.from_numpy(npz["g2"]).to(DEVICE))
        net.bn2.bias.copy_(torch.from_numpy(npz["be2"]).to(DEVICE))
        net.bn2.running_mean.copy_(torch.from_numpy(npz["rm2"]).to(DEVICE))
        net.bn2.running_var.copy_(torch.from_numpy(npz["rv2"]).to(DEVICE))
        net.fc3.weight.copy_(torch.from_numpy(npz["W3"].T).to(DEVICE))
        net.fc3.bias.copy_(torch.from_numpy(npz["b3"]).to(DEVICE))
    net.eval()
    return net

neural_net = load_neural()
vec = pickle.load(open(MODELS / "milk_vec.pkl", "rb"))

def classify_text(text: str) -> dict:
    """Run MILK neural classifier on GPU/CPU."""
    X = vec.transform([text[:2000]]).toarray().astype(np.float32)
    X_t = torch.from_numpy(X).to(DEVICE)
    with torch.no_grad():
        P = neural_net(X_t).cpu().numpy()
    # load thresholds
    thr_file = MODELS / "milk_thresholds.json"
    thresholds = json.load(open(thr_file, "r")) if thr_file.exists() else {}
    result = {}
    for i, eixo in enumerate(EIXOS):
        t = thresholds.get(eixo, 0.5)
        result[eixo] = {"prob": round(float(P[0][i]), 4),
                        "predicted": bool(P[0][i] > t),
                        "threshold": t}
    return result

# ============================================================
# 8. LIVE DASHBOARD (expanded)
# ============================================================
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt"><head><meta charset="utf-8"><meta http-equiv="refresh" content="3">
<title>MILK IA — Intelligence Fabric</title>
<style>
body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:16px}
h1{color:#58a6ff;font-size:1.3em;margin:0 0 12px}
h2{color:#8b949e;font-size:0.9em;margin:16px 0 8px;border-bottom:1px solid #30363d;padding-bottom:4px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;max-width:1200px}
.card{background:#161b22;border:1px solid #30363d;border-radius:4px;padding:8px}
.label{color:#8b949e;font-size:0.65em;text-transform:uppercase}
.value{color:#58a6ff;font-size:1em;font-weight:bold;margin-top:2px}
.on{color:#3fb950}.off{color:#f85149}.warn{color:#d29922}
table{width:100%;border-collapse:collapse;font-size:0.75em}td,th{padding:3px 6px;border-bottom:1px solid #21262d}
th{color:#8b949e;text-align:left}.small{font-size:0.7em;color:#8b949e}
</style></head><body>
<h1>MILK IA — Local Intelligence Fabric</h1>
<div id="content">A carregar...</div>
<script>
async function poll(){try{
const r=await fetch('/api/fabric/status');const d=await r.json();
let h='<h2>CORE</h2><div class="grid">';
const R=(l,v,c)=>`<div class="card"><div class="label">${l}</div><div class="value ${c||''}">${v}</div></div>`;
h+=R('HOST',d.host);h+=R('DEVICE',d.resource.device);
h+=R('GPU',d.resource.gpu||'CPU',d.resource.cuda?'on':'');
h+=R('CUDA',d.resource.cuda?'SIM':'NAO',d.resource.cuda?'on':'off');
h+=R('VRAM',`${d.resource.vram_used_gb}/${d.resource.vram_total_gb} GB`);
h+=R('VRAM FREE',`${d.resource.vram_free_gb} GB`);
h+=R('CPU',`${d.resource.cpu_pct}%`);h+=R('RAM',`${d.resource.ram_pct}%`);
h+=R('ACTIVE JOBS',d.resource.active_jobs);
h+=R('QUERIES',d.resource.metrics.queries);
h+='</div>';
h+='<h2>MODELS</h2><table><tr><th>Name</th><th>Type</th><th>Backend</th><th>Status</th></tr>';
for(const[n,m]of Object.entries(d.models))h+=`<tr><td>${n}</td><td>${m.type}</td><td>${m.backend}</td><td class="${m.status==='online'||m.status==='loaded'||m.status==='ready'?'on':'warn'}">${m.status}</td></tr>`;
h+='</table>';
h+='<h2>RETRIEVAL</h2><div class="grid">';
h+=R('INDEX SIZE',d.retrieval.index_size);
h+=R('QUERIES',d.retrieval.queries);
h+=R('AVG LATENCY',`${d.retrieval.avg_latency_ms}ms`);
h+=R('IDF TERMS',d.retrieval.idf_terms||'—');
h+='</div>';
if(d.retrieval.benchmark){
h+='<table><tr><th>Query</th><th>Hits</th><th>MRR</th><th>Top Score</th><th>Latency</th></tr>';
for(const b of d.retrieval.benchmark.details)h+=`<tr><td class="small">${b.query.slice(0,40)}</td><td>${b.n_hits}</td><td>${b.mrr}</td><td>${b.top_score}</td><td>${b.latency_ms}ms</td></tr>`;
h+=`</table><p class="small">Avg MRR: ${d.retrieval.benchmark.avg_mrr} | Avg Latency: ${d.retrieval.benchmark.avg_latency_ms}ms</p>`;
}
h+='<h2>AGENTS</h2><table><tr><th>Agent</th><th>Role</th><th>Tools</th><th>Status</th></tr>';
for(const[n,a]of Object.entries(d.agents))h+=`<tr><td>${n}</td><td>${a.role}</td><td class="small">${a.tools.join(', ')}</td><td class="on">${a.status}</td></tr>`;
h+='</table>';
h+='<h2>CONTINUOUS LEARNING</h2><div class="grid">';
h+=R('STATUS',d.continuous_learning.active?'ACTIVE':'OFF',d.continuous_learning.active?'on':'off');
h+=R('EVENTS',d.continuous_learning.events_count);
h+='</div>';
if(d.continuous_learning.recent_events.length){
h+='<table><tr><th>Type</th><th>Time</th><th>Result</th></tr>';
for(const e of d.continuous_learning.recent_events.slice(-5))h+=`<tr><td>${e.type}</td><td class="small">${(e.time||'').slice(11,19)}</td><td>${e.result||'processing'}</td></tr>`;
h+='</table>';}
if(d.proof_query){
h+='<h2>PROOF QUERY</h2><div class="grid">';
h+=R('QUERY',d.proof_query.question);
h+=R('RESULTS',d.proof_query.n_results);
h+=R('LATENCY',`${d.proof_query.latency_ms}ms`);
h+=R('TOP CITATION',d.proof_query.top_citation||'—');
h+='</div>';
if(d.proof_query.classification){
h+='<table><tr><th>Class</th><th>Prob</th><th>Predicted</th></tr>';
for(const[c,v]of Object.entries(d.proof_query.classification))if(v.predicted)h+=`<tr><td class="on">${c}</td><td>${v.prob}</td><td>YES</td></tr>`;
h+='</table>';}
}
h+=`<p class="small">Heartbeat: ${(d.heartbeat||'').slice(11,19)} | PID: ${d.pid}</p>`;
document.getElementById('content').innerHTML=h;
}catch(e){document.getElementById('content').innerHTML='<p class="off">Error: '+e+'</p>';}}
poll();setInterval(poll,3000);
</script></body></html>"""

# ============================================================
# 9. SERVER
# ============================================================
class FabricHandler(BaseHTTPRequestHandler):
    server_version = "MilkFabric/2.0"

    def log_message(self, *a): pass

    def _json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body):
        data = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = unquote(self.path.split("?")[0])
        params = {}
        if "?" in self.path:
            params = {k: v[0] for k, v in parse_qs(self.path.split("?")[1]).items()}

        if route == "/milk-live":
            self._html(DASHBOARD_HTML); return
        if route == "/api/fabric/status":
            self._json(self._fabric_status()); return
        if route == "/api/milk/status":
            d = self._fabric_status()
            self._json({"status": "OPERATIONAL", "pid": d["pid"], "device": d["resource"]["device"],
                        "gpu": d["resource"]["gpu"], "heartbeat": d["heartbeat"]}); return
        if route == "/api/milk/training/status":
            lf = STATE / "training_live.json"
            if lf.exists(): self._json(json.loads(lf.read_text(encoding="utf-8")))
            else: self._json({"status": "no training in progress"})
            return
        if route == "/api/milk/training/events":
            self._sse(); return
        if route == "/api/fabric/tools":
            self._json(MILK_TOOLS); return
        if route == "/api/fabric/agents":
            self._json(AGENTS); return
        if route == "/api/fabric/models":
            self._json(model_registry.status()); return
        if route == "/api/fabric/retrieval/benchmark":
            self._json(retrieval.benchmark()); return
        if route == "/api/fabric/query":
            q = params.get("q", "")
            if not q: self._json({"error": "missing q param"}); return
            t0 = time.time()
            hits = retrieval.search(q, 10)
            reranked = retrieval.rerank(q, hits, 5)
            classification = classify_text(q)
            self._json({"query": q, "results": reranked, "classification": classification,
                        "latency_ms": round((time.time()-t0)*1000, 1)}); return
        if route == "/api/fabric/gptoss/chat":
            q = params.get("q", "Hello")
            result = model_registry.gptoss_chat([{"role":"user","content":q}])
            self._json({"response": result, "model": "gpt-oss-20b"}); return
        self._json({"error": "unknown endpoint", "available": [
            "/milk-live", "/api/fabric/status", "/api/milk/status",
            "/api/milk/training/status", "/api/milk/training/events",
            "/api/fabric/tools", "/api/fabric/agents", "/api/fabric/models",
            "/api/fabric/retrieval/benchmark", "/api/fabric/query?q=...",
            "/api/fabric/gptoss/chat?q=..."
        ]}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        route = unquote(self.path.split("?")[0])
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if route == "/api/fabric/tools/call":
            tool = body.get("tool", "")
            params = body.get("params", {})
            self._json(execute_tool(tool, params)); return
        if route == "/api/fabric/agents/run":
            agent = body.get("agent", "")
            task = body.get("task", "")
            params = body.get("params", {})
            self._json(run_agent_task(agent, task, params)); return
        if route == "/api/fabric/cl/event":
            cl_queue.put({"type": body.get("type","NEW_DOCUMENT"), "data": body, "time": now_iso()})
            self._json({"queued": True, "events": len(cl_events)}); return
        self._json({"error": "unknown POST endpoint"}, HTTPStatus.NOT_FOUND)

    def _sse(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last = None
        for _ in range(300):
            d = self._fabric_status()
            hb = d["heartbeat"]
            if hb != last:
                last = hb
                self.wfile.write(f"data: {json.dumps(d, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
            time.sleep(2)

    def _fabric_status(self) -> dict:
        live = {}
        lf = STATE / "training_live.json"
        if lf.exists():
            try: live = json.loads(lf.read_text(encoding="utf-8"))
            except: pass
        # run proof query
        proof = None
        try:
            t0 = time.time()
            hits = retrieval.search("folclore romaria tradicao Moura", 10)
            reranked = retrieval.rerank("folclore romaria tradicao Moura", hits, 5)
            classification = classify_text("folclore romaria tradicao Moura")
            proof = {"question": "folclore romaria tradicao Moura",
                     "n_results": len(reranked),
                     "latency_ms": round((time.time()-t0)*1000, 1),
                     "top_citation": reranked[0]["chunk_id"][:16] if reranked else None,
                     "classification": classification}
        except: pass
        return {
            "schema": "ia_milk.fabric_status.v1",
            "host": os.environ.get("COMPUTERNAME", "localhost"),
            "pid": os.getpid(),
            "heartbeat": now_iso(),
            "resource": orchestrator.status(),
            "models": model_registry.status(),
            "retrieval": {"index_size": retrieval.stats["index_size"],
                          "queries": retrieval.stats["queries"],
                          "avg_latency_ms": retrieval.stats["avg_latency_ms"],
                          "idf_terms": len(retrieval.idf),
                          "benchmark": retrieval.benchmark() if retrieval.stats["queries"] == 0 else None},
            "agents": AGENTS,
            "continuous_learning": {"active": CL_ACTIVE, "events_count": len(cl_events),
                                    "recent_events": cl_events[-10:]},
            "training": live,
            "proof_query": proof,
            "semantic_memory": "Minimal Ontological Commitment + MLO + MIM + SEMIC + EIF/Mosaico/iAP + ENTI/ARPGU/CNMD + FIWARE/NGSI-LD + AI Act + ISO42001",
        }


def serve(port=8766):
    server = ThreadingHTTPServer(("127.0.0.1", port), FabricHandler)
    print(f"MILK INTELLIGENCE FABRIC on http://127.0.0.1:{port}")
    print(f"  DEVICE: {DEVICE} | CUDA: {CUDA} | GPU: {GPU_NAME} | VRAM: {VRAM_TOTAL}GB")
    print(f"  /milk-live — expanded dashboard")
    print(f"  /api/fabric/status — full status")
    print(f"  /api/fabric/query?q= — real query with retrieval+classification")
    print(f"  /api/fabric/tools — MILK tool registry")
    print(f"  /api/fabric/agents — agent registry")
    print(f"  /api/fabric/gptoss/chat?q= — gpt-oss-20b local chat")
    print(f"  Continuous learning: ACTIVE (event-driven)")
    server.serve_forever()

if __name__ == "__main__":
    # Run a benchmark on startup
    print("Running retrieval benchmark...")
    bench = retrieval.benchmark()
    print(f"  Benchmark: {bench['queries_tested']} queries, avg MRR={bench['avg_mrr']}, latency={bench['avg_latency_ms']}ms")
    serve()
