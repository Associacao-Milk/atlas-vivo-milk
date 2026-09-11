#!/usr/bin/env python3
"""Build state/milk_production_readiness.json from measured facts.

Gathers live measurements: embedding consistency verifier output, the
retrieval proof, the four validation health endpoints, corpus count, BGE/CUDA,
canonical test-event contamination, and git tree id. Stores source_tree_id
(the git tree object id), NOT a self-referential commit hash.
"""
from __future__ import annotations
import json, subprocess, sys, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from milk_ai.runtime_nomenclature import read_validation_revision  # compat reader
PY312 = r"C:\Users\Utilizador\AppData\Local\Programs\Python\Python312\python.exe"
VALIDATION = "http://127.0.0.1:8767"
OUT = ROOT / "state" / "milk_production_readiness.json"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()


def http_get(path, timeout=5):
    try:
        with urllib.request.urlopen(f"{VALIDATION}{path}", timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return None, {"error": str(e)}


def run_json(args, timeout=300):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), timeout=timeout, env=env)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"error": "no json", "stderr": r.stderr[:200]}


def main():
    head = git("rev-parse", "--short", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")

    # Embedding consistency (measured by the verifier)
    v = run_json([PY312, str(ROOT / "scripts" / "verify_embedding_consistency.py")], timeout=300)
    C = v.get("checks", {})

    # Retrieval proof (measured by the smoke test)
    proof_path = ROOT / "state" / "semantic_retrieval_proof.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8")) if proof_path.exists() else {}

    # BGE / CUDA (measured live)
    bge = {}
    try:
        r = subprocess.run([PY312, "-c", """
import torch
from sentence_transformers import SentenceTransformer
free=torch.cuda.mem_get_info()[0]/1e9; dev='cuda' if free>1.0 else 'cpu'
m=SentenceTransformer('BAAI/bge-m3',device=dev)
e=m.encode(['t'],normalize_embeddings=True,convert_to_numpy=True)
print(f'BGE_OK dim={e.shape[1]} device={dev} cuda={torch.cuda.is_available()} gpu={torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"none\"}')
"""], capture_output=True, text=True, cwd=str(ROOT), timeout=120,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src"),
                                 "HF_HUB_OFFLINE": "1",
                                 "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
        line = [l for l in (r.stdout or "").splitlines() if l.startswith("BGE_OK")]
        if line:
            parts = dict(p.split("=", 1) for p in line[0][7:].split() if "=" in p)
            bge = {"model": "BAAI/bge-m3", "dim": int(parts.get("dim", 0)),
                   "device": parts.get("device", "?"), "cuda": parts.get("cuda", "False") == "True",
                   "gpu": parts.get("gpu", "none")}
    except Exception as e:
        bge = {"error": str(e)}

    # Tests (measured)
    tr = subprocess.run([PY312, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests", "-q"],
                        capture_output=True, text=True, cwd=str(ROOT), timeout=300,
                        env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    tests_ok = tr.returncode == 0
    last = (tr.stdout or "").strip().splitlines()[-1] if (tr.stdout or "").strip() else ""

    # Health endpoints (measured)
    health = {}
    for path, key in [("/health", "health"), ("/health/retrieval", "retrieval"),
                      ("/health/reranker", "reranker"), ("/health/fabric", "fabric")]:
        code, body = http_get(path)
        health[key] = {"http": code,
                       "status": body.get("status") if isinstance(body, dict) else None}

    validation_rev = ""
    code, body = http_get("/health")
    if isinstance(body, dict):
        validation_rev = read_validation_revision(body, "") or body.get("runtime_revision", "")

    # Corpus + canonical test contamination (measured)
    doc_count = len(list((ROOT / "corpus" / "documents").glob("*.json")))
    canonical_log = ROOT / "state" / "knowledge_ingestion_log_canonical.jsonl"
    test_events = -1
    if canonical_log.exists():
        evs = [json.loads(l) for l in canonical_log.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        test_events = sum(1 for e in evs if e.get("source") == "test")

    # Conditions (mirrors the production gate)
    retrieval_5 = proof.get("retrieval_success") == "5/5"
    evidence_5 = proof.get("evidence_success") == "5/5"
    health_ok = all(h["http"] == 200 and h["status"] == "healthy" for h in health.values())
    idx_pass = v.get("index_alignment") == "PASS"
    orig_orphan = v.get("original_orphan_vectors") == 0
    delta_orphan = v.get("delta_orphan_vectors") == 0
    corpus_ok = doc_count == 10576
    tests_ok_cond = tests_ok
    test_events_ok = test_events == 0
    validation_head_match = validation_rev == head

    all_pass = (idx_pass and orig_orphan and delta_orphan and retrieval_5 and evidence_5
                and health_ok and corpus_ok and tests_ok_cond and test_events_ok
                and validation_head_match and bool(bge.get("cuda")))

    readiness = {
        "schema": "ia_milk.production_readiness.v2",
        "source_tree_id": tree,
        "head_short": head,
        "baseline_commit": "6b68fb9",
        "measured_at": git("show", "-s", "--format=%cI", "HEAD") or "",
        "tests": ("PASS" if tests_ok else "FAIL") + f" ({last})",
        "python": "3.12.10",
        "torch": "2.6.0+cu124",
        "cuda": bge.get("cuda", False),
        "gpu": bge.get("gpu", "none"),
        "bge_m3": {"model": bge.get("model"), "dim": bge.get("dim"), "device": bge.get("device")},
        "original_embedding_rows": C.get("original_embedding_rows"),
        "original_hash_entries": C.get("original_hash_entries"),
        "original_unique_hashes": C.get("original_unique_hashes"),
        "original_duplicate_hashes": C.get("original_duplicate_hashes"),
        "original_orphan_hash_entries": C.get("original_orphan_hash_entries"),
        "original_orphan_vectors": C.get("original_orphan_vectors"),
        "original_doc_level_content_verified": C.get("original_doc_level_content_verified"),
        "original_true_sourceless_orphans": C.get("original_true_sourceless_orphans"),
        "delta_embedding_rows": C.get("delta_embedding_rows"),
        "delta_hash_entries": C.get("delta_hash_entries"),
        "delta_unique_hashes": C.get("delta_unique_hashes"),
        "delta_duplicate_hashes": C.get("delta_duplicate_hashes"),
        "delta_orphan_hash_entries": C.get("delta_orphan_hash_entries"),
        "delta_orphan_vectors": C.get("delta_orphan_vectors"),
        "combined_embedding_rows": C.get("combined_embedding_rows"),
        "embedding_dimension": C.get("embedding_dimension"),
        "index_alignment": v.get("index_alignment"),
        "chunks": C.get("corpus_chunks_with_sha") if "corpus_chunks_with_sha" in C else v.get("chunks"),
        "vectors": v.get("vectors"),
        "retrieval_type": proof.get("retrieval_type"),
        "retrieval_success": proof.get("retrieval_success"),
        "evidence_success": proof.get("evidence_success"),
        "reranker": proof.get("reranker"),
        "health_endpoints": health,
        "validation_runtime_revision": validation_rev,
        "validation_runtime_head_match": validation_head_match,
        "corpus_docs": doc_count,
        "canonical_test_events": test_events,
        "production_gate": "PASS" if all_pass else "FAIL",
        "core_production_ready": bool(all_pass),
        "promotion_required": not all_pass,
        "fabric_8766": "legacy (PID 5744, pre-closeout, do-not-touch)",
    }
    OUT.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(readiness, ensure_ascii=False, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
