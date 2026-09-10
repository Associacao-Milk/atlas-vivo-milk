#!/usr/bin/env python3
"""MILK Embedding Consistency Verifier v2."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "state" / "chunk_index"
CORPUS = ROOT / "corpus" / "documents"

def verify():
    results = {"schema": "ia_milk.embedding_consistency.v2", "checks": {}}
    try:
        import numpy as np
    except ImportError:
        results["index_alignment"] = "UNKNOWN"
        return results

    # Original
    try:
        orig = np.load(CACHE / "original_embeddings.npz", allow_pickle=True)
        orig_embs = orig["embs"]
        results["checks"]["original_embedding_rows"] = int(orig_embs.shape[0])
        results["checks"]["embedding_dimension"] = int(orig_embs.shape[1])
        results["checks"]["original_hash_entries"] = "LOST"
        results["checks"]["original_orphan_hash_entries"] = "UNKNOWN"
        results["checks"]["original_orphan_vectors"] = "UNKNOWN"
    except Exception as e:
        results["index_alignment"] = "UNKNOWN"
        return results

    # Delta
    try:
        incr = np.load(CACHE / "incremental_embeddings.npz", allow_pickle=True)
        incr_hashes = [str(h) for h in incr["hashes"]]
        incr_embs = incr["embs"]
        results["checks"]["delta_embedding_rows"] = int(incr_embs.shape[0])
        results["checks"]["delta_hash_entries"] = len(incr_hashes)
        results["checks"]["delta_unique_hashes"] = len(set(incr_hashes))
        results["checks"]["delta_duplicate_hashes"] = len(incr_hashes) - len(set(incr_hashes))
        delta_aligned = len(incr_hashes) == incr_embs.shape[0]
        results["checks"]["delta_alignment"] = "PASS" if delta_aligned else "FAIL"
    except Exception as e:
        results["index_alignment"] = "FAIL"
        return results

    # Corpus hashes for orphan check
    corpus_hashes = set()
    chunks_discovered = 0; chunks_empty = 0; chunks_eligible = 0
    for f in CORPUS.glob("*.json"):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
            if doc.get("pipeline_version") != "ingest-v1": continue
            for chunk in doc.get("chunks", []):
                chunks_discovered += 1
                ch = chunk.get("sha256", "")
                if not chunk.get("text", "").strip(): chunks_empty += 1
                else: chunks_eligible += 1
                if ch: corpus_hashes.add(ch)
        except: pass

    delta_orphan_hashes = sum(1 for h in incr_hashes if h not in corpus_hashes)
    results["checks"]["delta_orphan_hash_entries"] = delta_orphan_hashes
    results["checks"]["delta_orphan_vectors"] = delta_orphan_hashes
    results["checks"]["chunks_discovered"] = chunks_discovered
    results["checks"]["chunks_empty"] = chunks_empty
    results["checks"]["chunks_eligible"] = chunks_eligible
    results["checks"]["chunks_embedded"] = int(incr_embs.shape[0])
    results["checks"]["embedding_failures"] = chunks_eligible - int(incr_embs.shape[0])

    # Combined
    results["checks"]["combined_embedding_rows"] = int(orig_embs.shape[0]) + int(incr_embs.shape[0])
    try:
        combined = np.load(CACHE / "chunk_dense_cache.npz", allow_pickle=True)
        results["checks"]["combined_hash_entries"] = len(combined["hashes"])
    except: results["checks"]["combined_hash_entries"] = "ERROR"

    # Verdict
    delta_ok = (results["checks"]["delta_alignment"] == "PASS" and
                results["checks"]["delta_orphan_hash_entries"] == 0)
    if delta_ok:
        results["index_alignment"] = "PARTIAL_PASS"
    else:
        results["index_alignment"] = "FAIL"

    results["original_orphan_hash_entries"] = "UNKNOWN"
    results["original_orphan_vectors"] = "UNKNOWN"
    results["delta_orphan_hash_entries"] = delta_orphan_hashes
    results["delta_orphan_vectors"] = delta_orphan_hashes
    return results

if __name__ == "__main__":
    r = verify()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r.get("index_alignment") in ("PASS", "PARTIAL_PASS") else 1)
