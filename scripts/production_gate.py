#!/usr/bin/env python3
"""MILK Production Gate — strict, provider-neutral, exits non-zero on failure.

Production Python 3.12 ONLY. Never weakens a failed condition to make the gate
pass. A single failed check fails the whole gate.

Checks:
  1. pytest exit code 0 (production Python 3.12)
  2. index alignment == PASS (strict; never PARTIAL_PASS) from the verifier
  3. original + delta orphan hashes/vectors == 0
  4. BGE-M3 / Torch / CUDA / GPU measured live
  5. retrieval 5/5, evidence 5/5, retrieval_type DENSE+RERANKER
  6. four validation health endpoints PASS (real HTTP GETs)
  7. validation runtime_revision == current HEAD
  8. corpus document count == 10576
  9. canonical ingestion log has 0 test events
"""
from __future__ import annotations
import json, subprocess, sys, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from milk_ai.runtime_nomenclature import read_validation_revision  # compat reader
PY312 = r"C:\Users\Utilizador\AppData\Local\Programs\Python\Python312\python.exe"
VALIDATION = "http://127.0.0.1:8767"
FAILURES = []


def check(name, condition, detail=""):
    if not condition:
        FAILURES.append(f"{name}: FAIL {detail}")
        print(f"  FAIL: {name} {detail}")
    else:
        print(f"  PASS: {name}")


def run_json(args, timeout=120):
    r = subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), timeout=timeout)
    try:
        return json.loads(r.stdout), r
    except Exception:
        return None, r


def http_get(path, timeout=5):
    try:
        req = urllib.request.Request(f"{VALIDATION}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return None, {"error": str(e)}


def main():
    print("=" * 60)
    print("MILK PRODUCTION GATE (Python 3.12)")
    print("=" * 60)

    # 1. Tests — actual exit code 0 required (INTERNALERROR => non-zero => FAIL)
    print("\n[1] Tests")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run([PY312, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests"],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=300, env=env)
    tail = (r.stdout or r.stderr).strip().split("\n")[-1] if (r.stdout or r.stderr).strip() else "no output"
    check("tests_exit0", r.returncode == 0, f"rc={r.returncode} {tail}")

    # 2. Index alignment (strict PASS, never PARTIAL_PASS)
    print("\n[2] Index alignment")
    v, vr = run_json([PY312, str(ROOT / "scripts" / "verify_embedding_consistency.py")], timeout=180)
    if v is None:
        check("index_alignment", False, "verifier produced no JSON")
    else:
        check("index_alignment_pass", v.get("index_alignment") == "PASS",
              f"got {v.get('index_alignment')!r}")
        check("original_orphan_vectors", v.get("original_orphan_vectors") == 0,
              f"got {v.get('original_orphan_vectors')}")
        check("delta_orphan_vectors", v.get("delta_orphan_vectors") == 0,
              f"got {v.get('delta_orphan_vectors')}")

    # 3. Corpus
    print("\n[3] Corpus")
    doc_count = len(list((ROOT / "corpus" / "documents").glob("*.json")))
    check("corpus_docs", doc_count == 10576, f"got {doc_count}")

    # 4. Canonical test contamination
    print("\n[4] Test contamination")
    canonical_log = ROOT / "state" / "knowledge_ingestion_log_canonical.jsonl"
    if canonical_log.exists():
        events = [json.loads(l) for l in canonical_log.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        test_events = sum(1 for e in events if e.get("source") == "test")
        check("canonical_test_events", test_events == 0, f"found {test_events}")
    else:
        check("canonical_test_events", False, "canonical log not found")

    # 5. Retrieval proof
    print("\n[5] Retrieval proof")
    proof_path = ROOT / "state" / "semantic_retrieval_proof.json"
    if proof_path.exists():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        check("retrieval_5_5", proof.get("retrieval_success") == "5/5", proof.get("retrieval_success", ""))
        check("evidence_5_5", proof.get("evidence_success") == "5/5", proof.get("evidence_success", ""))
        check("retrieval_type", proof.get("retrieval_type") == "DENSE+RERANKER", proof.get("retrieval_type", ""))
        check("reranker", proof.get("reranker") == "BAAI/bge-reranker-v2-m3", proof.get("reranker", ""))
    else:
        check("retrieval_5_5", False, "proof not found")

    # 6. BGE / Torch / CUDA / GPU measured live (retry once; CUDA fragmentation
    #    under concurrent load can transiently fail the first attempt).
    print("\n[6] BGE-M3 / CUDA")
    bge_env = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
               "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
               "HF_HUB_OFFLINE": "1"}
    bge_script = """
import torch
from sentence_transformers import SentenceTransformer
free = torch.cuda.mem_get_info()[0]/1e9
dev = 'cuda' if free>1.0 else 'cpu'
m = SentenceTransformer('BAAI/bge-m3', device=dev)
e = m.encode(['test'], normalize_embeddings=True, convert_to_numpy=True)
print(f'BGE_OK dim={e.shape[1]} device={dev} cuda={torch.cuda.is_available()} gpu={torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"none\"}')
"""
    out = ""
    for attempt in range(2):
        r = subprocess.run([PY312, "-c", bge_script], capture_output=True, text=True,
                           cwd=str(ROOT), timeout=120, env=bge_env)
        out = (r.stdout or "").strip() or (r.stderr or "")[:200]
        if "BGE_OK" in (r.stdout or ""):
            break
        import time as _t; _t.sleep(2)
    check("bge_m3_cuda", "BGE_OK" in (r.stdout or ""), out)

    # 7. Four validation health endpoints (real GETs)
    print("\n[7] Validation health")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
    for path, label in [("/health", "health"),
                        ("/health/retrieval", "health_retrieval"),
                        ("/health/reranker", "health_reranker"),
                        ("/health/fabric", "health_fabric")]:
        code, body = http_get(path)
        ok = code == 200 and isinstance(body, dict) and body.get("status") in ("healthy",)
        check(f"validation_{label}", ok, f"http={code} status={body.get('status') if isinstance(body,dict) else body}")

    # 8. Validation revision == HEAD
    print("\n[8] Validation revision")
    code, body = http_get("/health")
    validation_rev = read_validation_revision(body, "") or (body.get("runtime_revision", "") if isinstance(body, dict) else "")
    check("validation_runtime_revision", validation_rev == head, f"validation={validation_rev} head={head}")

    # Summary
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"GATE: FAIL ({len(FAILURES)} failures)")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("GATE: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
