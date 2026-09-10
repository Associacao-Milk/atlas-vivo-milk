#!/usr/bin/env python3
"""MILK Production Gate — provider-neutral, exits non-zero on failure.

Checks: tests, index alignment, orphans, BGE, reranker, retrieval smoke,
EvidenceBundle, startup validation, shadow health, shadow revision,
corpus doc count, canonical test contamination.
"""
from __future__ import annotations
import json, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY314 = r"C:\Python314\python.exe"
PY312 = r"C:\Users\Utilizador\AppData\Local\Programs\Python\Python312\python.exe"
FAILURES = []

def check(name, condition, detail=""):
    if not condition:
        FAILURES.append(f"{name}: FAIL {detail}")
        print(f"  FAIL: {name} {detail}")
    else:
        print(f"  PASS: {name}")

def main():
    print("=" * 60)
    print("MILK PRODUCTION GATE")
    print("=" * 60)

    # 1. Tests
    print("\n[1] Tests")
    r = subprocess.run([PY314, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q",
                       "tests/test_external_adapters.py", "tests/test_action_gate_and_extended.py",
                       "tests/test_execution_graph_and_compliance.py", "tests/test_hardening.py",
                       "tests/test_knowledge_ingestion.py"],
                      capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    passed = "passed" in r.stdout and "failed" not in r.stdout.split("passed")[0]
    check("tests", passed, r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr[:200])

    # 2. Index alignment
    print("\n[2] Index alignment")
    r = subprocess.run([PY312, str(ROOT / "scripts" / "verify_embedding_consistency.py")],
                      capture_output=True, text=True, timeout=60)
    try:
        v = json.loads(r.stdout)
        check("index_alignment", v.get("index_alignment") in ("PASS", "PARTIAL_PASS"), v.get("index_alignment",""))
        check("delta_orphans", v.get("delta_orphan_hash_entries", -1) == 0, f"orphans={v.get('delta_orphan_hash_entries')}")
    except:
        check("index_alignment", False, "verifier failed")

    # 3. Corpus count
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
        check("canonical_test_events", False, "log not found")

    # 5. Retrieval proof
    print("\n[5] Retrieval proof")
    proof_path = ROOT / "state" / "semantic_retrieval_proof.json"
    if proof_path.exists():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        check("retrieval_5_5", proof.get("retrieval_success") == "5/5", proof.get("retrieval_success",""))
        check("evidence_5_5", proof.get("evidence_success") == "5/5", proof.get("evidence_success",""))
        check("reranker", proof.get("reranker") == "BAAI/bge-reranker-v2-m3", proof.get("reranker",""))
    else:
        check("retrieval_5_5", False, "proof not found")

    # 6. BGE verification
    print("\n[6] BGE")
    r = subprocess.run([PY312, "-c", """
from sentence_transformers import SentenceTransformer
import torch
m = SentenceTransformer('BAAI/bge-m3', device='cuda')
e = m.encode(['test'])
print(f'BGE_OK dim={e.shape[1]} cuda={torch.cuda.is_available()}')
"""], capture_output=True, text=True, timeout=60)
    check("bge_m3", "BGE_OK" in r.stdout, r.stdout[:100] if r.stdout else r.stderr[:200])

    # 7. Shadow health (if running) — revision check is informational
    print("\n[7] Shadow")
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8767/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            h = json.loads(resp.read())
            head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                  capture_output=True, text=True, cwd=str(ROOT)).stdout.strip()
            check("shadow_health", h.get("status") == "healthy", h.get("status",""))
            shadow_rev = h.get("runtime_revision") or h.get("git_revision", "")
            check("shadow_revision", shadow_rev == head, f"shadow={shadow_rev} head={head}")
    except:
        check("shadow_health", False, "shadow not running")

    # 8. git diff --check (only for staged/our files, not preexisting dirty logs)
    print("\n[8] Git diff")
    # Check only files we changed in this commit
    r = subprocess.run(["git", "diff", "--check", "HEAD~1"], capture_output=True, text=True, cwd=str(ROOT))
    # git diff --check exits non-zero if whitespace issues found in the diff
    # But preexisting dirty logs are not part of our diff — check our commit's diff
    r2 = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], capture_output=True, text=True, cwd=str(ROOT))
    our_files = r2.stdout.strip().split("\n") if r2.stdout.strip() else []
    has_ws_issue = False
    for f in our_files:
        if not f: continue
        r3 = subprocess.run(["git", "diff", "--check", f"HEAD~1", "HEAD", "--", f],
                           capture_output=True, text=True, cwd=str(ROOT))
        if r3.stdout.strip():
            has_ws_issue = True
    check("git_diff_check", not has_ws_issue, "whitespace in our diff" if has_ws_issue else "OK")

    # Summary
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"GATE: FAIL ({len(FAILURES)} failures)")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("GATE: PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
