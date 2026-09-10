#!/usr/bin/env python3
"""MILK canonical retrieval smoke test.

Pipeline: ControlPlane task -> BGE-M3 dense retrieval over the real combined
index -> bge-reranker-v2-m3 -> EvidenceBundle -> worker response.

Run with PRODUCTION Python 3.12 (torch+CUDA+sentence_transformers).
Writes state/semantic_retrieval_proof.json with retrieval_type DENSE+RERANKER.
"""
from __future__ import annotations
import json, hashlib, sys, os
from pathlib import Path
import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CORPUS = ROOT / "corpus" / "documents"
CACHE = ROOT / "state" / "chunk_index"
PROOF = ROOT / "state" / "semantic_retrieval_proof.json"

BGE = "BAAI/bge-m3"
RERANKER = "BAAI/bge-reranker-v2-m3"

# 5 natural Portuguese queries (no hash/filename/doc_id).
QUERIES = [
    "nucleo estavel consolidacao curatorial atlas vivo",
    "resumo consolidacao total versao publica operacional",
    "governacao migracao atlas vivo milk",
    "protocolo genealogico autoavaliacao curatorial",
    "regra consolidacao total nucleo estavel",
]


def build_hash_map():
    """content_hash -> (chunk_id, document_id) for every corpus chunk."""
    h2 = {}
    for f in CORPUS.glob("*.json"):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc_id = doc.get("id") or doc.get("document_id") or f.stem
        for chunk in doc.get("chunks", []):
            sha = chunk.get("sha256", "")
            cid = chunk.get("chunk_id", "")
            if sha and cid:
                h2.setdefault(sha, []).append((cid, doc_id, chunk.get("text", "")[:200]))
    return h2


def main():
    import torch
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from milk_ai.cognitive_control_plane import EvidenceBundle

    cache = np.load(CACHE / "chunk_dense_cache.npz", allow_pickle=True)
    all_hashes = [str(h) for h in cache["hashes"].tolist()]
    all_embs = cache["embs"]
    dim = int(all_embs.shape[1])

    h2 = build_hash_map()

    # Retrieval smoke runs on CPU for robustness under GPU contention (the
    # production gate verifies CUDA/BGE-M3 capability separately). CPU dense
    # retrieval over ~251k vectors is fast and keeps GPU free for inference
    # services. Falls back is handled by always using CPU here.
    device = "cpu"
    model = SentenceTransformer(BGE, device=device)
    reranker = CrossEncoder(RERANKER, device="cpu")

    queries_out = []
    retrieval_ok = 0
    evidence_ok = 0

    for qi, q in enumerate(QUERIES):
        q_emb = model.encode([q], normalize_embeddings=True, convert_to_numpy=True)
        scores = (all_embs @ q_emb.T).flatten()
        top_idx = np.argsort(scores)[::-1][:20]

        # Map top dense hits to real chunk_ids via the corpus hash map.
        hits = []
        for idx in top_idx:
            h = all_hashes[idx]
            if h in h2:
                cid, doc_id, preview = h2[h][0]
                hits.append({
                    "idx": int(idx),
                    "hash": h,
                    "chunk_id": cid,
                    "document_id": doc_id,
                    "dense_score": round(float(scores[idx]), 6),
                    "text_preview": preview,
                })
            if len(hits) >= 10:
                break

        # Rerank the retrieved candidates with the cross-encoder.
        reranked = []
        if hits:
            pairs = [(q, ht["text_preview"]) for ht in hits]
            raw = reranker.predict(pairs)
            lo, hi = float(min(raw)), float(max(raw))
            for ht, r in zip(hits, raw):
                norm = (float(r) - lo) / (hi - lo) if hi > lo else 1.0
                ht["rerank_raw_score"] = round(float(r), 6)
                ht["rerank_normalized_score"] = round(norm, 6)
            reranked = sorted(hits, key=lambda x: -x["rerank_raw_score"])

        top = reranked[0] if reranked else (hits[0] if hits else None)

        # Build the EvidenceBundle (ControlPlane -> evidence fabric).
        bundle = EvidenceBundle(task_id=f"smoke-{qi+1}", trace_id=hashlib.sha256(q.encode()).hexdigest()[:16])
        if top:
            bundle.add_evidence(
                source=f"chunk:{top['chunk_id']}",
                source_uri=f"document:{top['document_id']}",
                content=top["text_preview"],
                content_hash=top["hash"],
                retrieval_method="dense_bge_m3",
                reranking=RERANKER,
                metadata={"dense_score": top["dense_score"],
                          "rerank_raw_score": top.get("rerank_raw_score", 0)},
            )
        bundle.add_inference(model=BGE, model_version="bge-m3", output=top["text_preview"] if top else "")
        bundle.add_decision(
            decision="respond" if top else "no_evidence",
            rationale="dense+reranker evidence selected" if top else "no chunk matched",
        )
        hc = bundle.hash_chain()

        retrieval_success = bool(top and top.get("chunk_id"))
        evidence_success = bool(bundle.items and hc)
        if retrieval_success:
            retrieval_ok += 1
        if evidence_success:
            evidence_ok += 1

        if top:
            queries_out.append({
                "query": q,
                "rank": 1,
                "chunk_id": top["chunk_id"],
                "document_id": top["document_id"],
                "retrieval_score": top["dense_score"],
                "rerank_raw_score": top.get("rerank_raw_score", 0.0),
                "rerank_normalized_score": top.get("rerank_normalized_score", 0.0),
                "evidence_hash_chain": hc,
                "evidence_items": len(bundle.items),
            })
        else:
            queries_out.append({"query": q, "rank": 0, "chunk_id": "", "document_id": ""})

    proof = {
        "queries": queries_out,
        "retrieval_success": f"{retrieval_ok}/5",
        "evidence_success": f"{evidence_ok}/5",
        "retrieval_type": "DENSE+RERANKER",
        "bge": BGE,
        "bge_dim": dim,
        "bge_device": device,
        "reranker": RERANKER,
        "reranker_device": "cpu",
        "index_vectors": int(all_embs.shape[0]),
    }
    PROOF.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=False, indent=2))
    ok = retrieval_ok == 5 and evidence_ok == 5
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
