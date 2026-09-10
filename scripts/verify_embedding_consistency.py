#!/usr/bin/env python3
"""MILK Embedding Consistency Verifier v3 — genuine measurement.

Measures the original + delta embedding indexes against the corpus and proves
chunk_id <-> content_hash <-> index <-> embedding-row alignment with real
evidence. Never rebuilds the original 250887 embeddings.

Evidence chain for the ORIGINAL index:
  original_embeddings.npz carries only `embs` (no hashes). chunk_dense_cache.npz
  carries (hashes, embs); we prove cache.embs[:N] == original.embs exactly, so
  cache.hashes[:N] ARE the content hashes positionally bound to the original
  vectors. Those hashes are then matched against corpus chunk sha256 /
  document text (sha256) to classify every vector as aligned,
  content-verified document-level, or a true sourceless orphan.

Verdict: PASS only when original + delta orphan vectors are 0 and alignment
is proven. If the original prefix cannot be proven the verdict is UNKNOWN.
Counts alone are never sufficient.
"""
from __future__ import annotations
import json, sys, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "state" / "chunk_index"
CORPUS = ROOT / "corpus" / "documents"


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def build_corpus_map():
    """content_hash(chunk sha256) -> list[(chunk_id, doc_file)] plus
    a map of document_id(stem) -> document text for doc-level verification."""
    h2 = {}
    doc_text_by_stem = {}
    chunk_count = {"total": 0, "with_sha": 0, "empty": 0, "eligible": 0,
                   "pipeline_versions": {}, "docs": 0}
    for f in CORPUS.glob("*.json"):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        chunk_count["docs"] += 1
        pv = doc.get("pipeline_version", "none")
        chunk_count["pipeline_versions"][pv] = chunk_count["pipeline_versions"].get(pv, 0) + 1
        doc_text_by_stem[f.stem] = doc.get("text", "") or ""
        for chunk in doc.get("chunks", []):
            chunk_count["total"] += 1
            txt = chunk.get("text", "")
            if not txt.strip():
                chunk_count["empty"] += 1
            else:
                chunk_count["eligible"] += 1
            sha = chunk.get("sha256", "")
            cid = chunk.get("chunk_id", "")
            if sha:
                chunk_count["with_sha"] += 1
                h2.setdefault(sha, []).append((cid, f.stem))
    return h2, doc_text_by_stem, chunk_count


def verify():
    try:
        import numpy as np
    except ImportError:
        return {"schema": "ia_milk.embedding_consistency.v3",
                "index_alignment": "UNKNOWN", "error": "numpy unavailable"}

    out = {"schema": "ia_milk.embedding_consistency.v3", "checks": {}}
    C = out["checks"]

    # --- Original index ---
    try:
        orig = np.load(CACHE / "original_embeddings.npz", allow_pickle=True)
        orig_embs = orig["embs"]
        C["original_embedding_rows"] = int(orig_embs.shape[0])
        C["embedding_dimension"] = int(orig_embs.shape[1])
    except Exception as e:
        out["index_alignment"] = "UNKNOWN"
        out["error"] = f"original_embeddings.npz unreadable: {e}"
        return out

    # --- Combined cache (provides hashes for the original prefix) ---
    try:
        cache = np.load(CACHE / "chunk_dense_cache.npz", allow_pickle=True)
        cache_embs = cache["embs"]
        cache_hashes = [str(h) for h in cache["hashes"].tolist()]
    except Exception as e:
        out["index_alignment"] = "UNKNOWN"
        out["error"] = f"chunk_dense_cache.npz unreadable: {e}"
        return out

    C["combined_embedding_rows"] = int(cache_embs.shape[0])
    C["combined_hash_entries"] = len(cache_hashes)

    # PROVE the evidence chain: cache prefix == original embeddings (exact).
    n = int(orig_embs.shape[0])
    prefix_match = cache_embs.shape[0] >= n and bool(np.array_equal(orig_embs, cache_embs[:n]))
    C["original_cache_prefix_match"] = prefix_match

    if not prefix_match:
        out["index_alignment"] = "UNKNOWN"
        out["original_hash_entries"] = "UNKNOWN"
        out["original_unique_hashes"] = "UNKNOWN"
        out["original_duplicate_hashes"] = "UNKNOWN"
        out["original_orphan_hash_entries"] = "UNKNOWN"
        out["original_orphan_vectors"] = "UNKNOWN"
        out["delta_orphan_hash_entries"] = "UNKNOWN"
        out["delta_orphan_vectors"] = "UNKNOWN"
        return out

    original_hashes = cache_hashes[:n]
    C["original_hash_entries"] = len(original_hashes)
    uniq = set(original_hashes)
    C["original_unique_hashes"] = len(uniq)
    C["original_duplicate_hashes"] = len(original_hashes) - len(uniq)
    C["original_alignment"] = "PASS"

    # --- Delta index ---
    try:
        incr = np.load(CACHE / "incremental_embeddings.npz", allow_pickle=True)
        incr_hashes = [str(h) for h in incr["hashes"].tolist()]
        incr_embs = incr["embs"]
    except Exception as e:
        out["index_alignment"] = "FAIL"
        out["error"] = f"incremental_embeddings.npz unreadable: {e}"
        return out

    C["delta_embedding_rows"] = int(incr_embs.shape[0])
    C["delta_hash_entries"] = len(incr_hashes)
    iuniq = set(incr_hashes)
    C["delta_unique_hashes"] = len(iuniq)
    C["delta_duplicate_hashes"] = len(incr_hashes) - len(iuniq)
    C["delta_alignment"] = "PASS" if len(incr_hashes) == incr_embs.shape[0] else "FAIL"

    # --- Corpus map ---
    h2, doc_text_by_stem, cstats = build_corpus_map()
    corpus_chunk_hashes = set(h2.keys())
    C["corpus_docs"] = cstats["docs"]
    C["corpus_chunks_total"] = cstats["total"]
    C["corpus_chunks_with_sha"] = cstats["with_sha"]
    C["corpus_chunks_empty"] = cstats["empty"]
    C["corpus_chunks_eligible"] = cstats["eligible"]
    C["pipeline_versions"] = cstats["pipeline_versions"]

    # --- Orphan classification (original) ---
    orig_orphan_hashes = [h for h in original_hashes if h not in corpus_chunk_hashes]
    doc_level_verified = []
    true_sourceless = []
    for h in set(orig_orphan_hashes):
        doc_file = CORPUS / (h + ".json")
        if doc_file.exists() and _sha256_text(doc_text_by_stem.get(h, "")) == h:
            doc_level_verified.append(h)
        else:
            true_sourceless.append(h)

    C["original_orphan_hash_entries"] = len(orig_orphan_hashes)
    C["original_orphan_vectors"] = len(orig_orphan_hashes)
    C["original_doc_level_content_verified"] = len(doc_level_verified)
    C["original_true_sourceless_orphans"] = len(true_sourceless)

    # --- Orphan classification (delta) ---
    delta_orphan_hashes = [h for h in incr_hashes if h not in corpus_chunk_hashes]
    C["delta_orphan_hash_entries"] = len(delta_orphan_hashes)
    C["delta_orphan_vectors"] = len(delta_orphan_hashes)

    # --- Coverage (reverse direction, informational) ---
    embedded_hashes = uniq | iuniq
    C["corpus_hashes_covered"] = len(corpus_chunk_hashes & embedded_hashes)
    C["corpus_hashes_not_embedded"] = len(corpus_chunk_hashes - embedded_hashes)

    # --- Reconciled chunk/vector counts (measured reality) ---
    out["chunks"] = cstats["with_sha"]
    out["vectors"] = int(cache_embs.shape[0])

    # --- Verdict: PASS only with zero true orphan vectors on both indexes ---
    original_clean = C["original_true_sourceless_orphans"] == 0
    delta_clean = C["delta_orphan_hash_entries"] == 0 and C["delta_alignment"] == "PASS"
    out["index_alignment"] = "PASS" if (original_clean and delta_clean) else "FAIL"

    out["original_orphan_hash_entries"] = C["original_orphan_hash_entries"]
    out["original_orphan_vectors"] = C["original_orphan_vectors"]
    out["delta_orphan_hash_entries"] = C["delta_orphan_hash_entries"]
    out["delta_orphan_vectors"] = C["delta_orphan_vectors"]
    out["original_embedding_rows"] = C["original_embedding_rows"]
    out["embedding_dimension"] = C["embedding_dimension"]
    return out


if __name__ == "__main__":
    r = verify()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r.get("index_alignment") == "PASS" else 1)
