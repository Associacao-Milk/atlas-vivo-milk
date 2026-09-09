#!/usr/bin/env python3
"""MILK IA — Benchmark DOCUMENT vs CHUNK vs HIERARCHICAL (caches reused, bug fixed).

Root cause: rrf() returns (index, score) tuples from dict.items(), but the
benchmark code unpacked them as (score, index) — di got the float score
instead of the integer index. Fixed by unpacking correctly and adding
assert isinstance(idx, int) validation throughout.
"""
from __future__ import annotations
import sys, os, json, time, hashlib, math, re, unicodedata
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import numpy as np
import torch

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
STATE = ROOT / "state"; CORPUS = ROOT / "corpus" / "documents"
INDEX_DIR = STATE / "chunk_index"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CUDA = torch.cuda.is_available()

EIXOS_P = {
    "humana":["memoria","identidade","pertença","vivencia","experiencia","emoção","corpo","sensação","biografia"],
    "social":["comunidade","intergeracional","participação","inclusão","diversidade","coletivo","associação"],
    "legal":["RGPD","consentimento","direitos","licença","conformidade","lei","decreto","estatuto"],
    "juridica":["propriedade","autoria","contrato","obrigação","responsabilidade"],
    "cultural":["folclore","tradição","etnografia","património","ritual","festa","costume","lenda","mito","romaria"],
    "territorial":["freguesia","concelho","distrito","topónimo","paisagem","território","mapa","caop"],
    "existencial":["sentido","existência","possível","casa","habitar","pertencer","despertar","noema"],
    "administrativa":["camara","municipio","junta","administração","publica","autarquia"],
    "economica":["custo","orcamento","financiamento","receita","despesa","DGARTES","horizon","fundos"],
    "ambiental":["ambiente","natureza","sustentabilidade","clima","agua","floresta","biodiversidade"],
    "tecnologica":["QR","digital","interoperabilidade","API","dados","software","sistema","tecnologia"],
}
def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256_text(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def _features(text):
    norm = "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))
    tokens = re.findall(r"[a-z0-9]+", norm)
    return tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]

def load_all_chunks():
    files = sorted(CORPUS.glob("*.json"))
    chunks, docs = [], {}
    for i, fp in enumerate(files):
        try:
            d = json.load(open(fp, "r", encoding="utf-8"))
            dh = fp.stem; dt = (d.get("text","") or "")[:2000]
            docs[dh] = {"hash": dh, "text": dt[:500], "n_chunks": 0}
            dcs = d.get("chunks", [])
            if not dcs:
                if dt.strip():
                    chunks.append({"chunk_id": dh, "doc_hash": dh, "text": dt[:500], "sha256": sha256_text(dt)})
                    docs[dh]["n_chunks"] = 1
            else:
                for j, c in enumerate(dcs):
                    ct = (c.get("text","") or "")[:500]
                    if ct.strip():
                        chunks.append({"chunk_id": c.get("chunk_id", f"{dh}_{j}"), "doc_hash": dh,
                                      "text": ct, "sha256": c.get("sha256", sha256_text(ct))})
                docs[dh]["n_chunks"] = len(dcs)
            if (i+1) % 2000 == 0: print(f"  loaded {i+1}/{len(files)} docs, {len(chunks)} chunks")
        except: continue
    print(f"  total: {len(files)} docs, {len(chunks)} chunks")
    return chunks, docs

def build_sparse(texts):
    tcs = [Counter(_features(t)) for t in texts]
    df = Counter()
    for tc in tcs: df.update(tc.keys())
    n = len(texts); idf = {t: math.log((1+n)/(1+df_))+1.0 for t, df_ in df.most_common(50000)}
    vecs = []
    for tc in tcs:
        w = {t: (1+math.log(c))*idf.get(t,0) for t,c in tc.items() if t in idf and c>0}
        norm = math.sqrt(sum(v*v for v in w.values()))
        vecs.append({k:v/norm for k,v in w.items()} if norm else {})
    return idf, vecs

def load_dense_cache(cache_path):
    """Load dense embeddings from cache (no recalculation)."""
    cd = np.load(cache_path, allow_pickle=True)
    hashes = cd["hashes"].tolist()
    embs = cd["embs"]
    print(f"  cache loaded: {cache_path.name} -> {embs.shape}")
    return torch.from_numpy(embs.astype(np.float32)), hashes

def sparse_search(q, vecs, idf, limit=10):
    """Returns list of (score: float, index: int) — index is always Python int."""
    qv = Counter(_features(q))
    qw = {t:(1+math.log(c))*idf.get(t,0) for t,c in qv.items() if t in idf and c>0}
    qn = math.sqrt(sum(v*v for v in qw.values()))
    if qn: qw = {k:v/qn for k,v in qw.items()}
    scores = np.array([sum(w*lv.get(t,0.0) for t,w in qw.items()) for lv in vecs])
    order = np.argsort(-scores)[:limit]
    results = []
    for i in order:
        if scores[i] > 0:
            idx = int(i)  # explicit cast to Python int
            results.append((float(scores[i]), idx))
    return results

def dense_search(q, dm, model, limit=10):
    """Returns list of (score: float, index: int) — index is always Python int."""
    qe = model.encode([q], convert_to_tensor=True, show_progress_bar=False).cpu()
    sims = torch.cosine_similarity(qe, dm, dim=1).numpy()
    order = np.argsort(-sims)[:limit]
    results = []
    for i in order:
        idx = int(i)  # explicit cast to Python int
        results.append((float(sims[i]), idx))
    return results

def rrf_fusion(sparse_results, dense_results, k=60, limit=10):
    """RRF fusion. Returns list of (index: int, rrf_score: float).

    Key invariant: the FIRST element of each tuple is the integer index,
    the SECOND is the float RRF score. This is the fixed version — the bug
    was that callers unpacked as (score, index) instead of (index, score).
    """
    r = {}
    for rank, (_, idx) in enumerate(sparse_results[:limit*5]):
        assert isinstance(idx, int), f"sparse idx must be int, got {type(idx)}: {idx}"
        r[idx] = r.get(idx, 0.0) + 1.0/(k+rank+1)
    for rank, (_, idx) in enumerate(dense_results[:limit*5]):
        assert isinstance(idx, int), f"dense idx must be int, got {type(idx)}: {idx}"
        r[idx] = r.get(idx, 0.0) + 1.0/(k+rank+1)
    # Return (index, score) pairs sorted by descending score
    result = sorted(r.items(), key=lambda x: -x[1])[:limit]
    # Validate all indices are integers
    for idx, score in result:
        assert isinstance(idx, int), f"rrf idx must be int, got {type(idx)}: {idx}"
        assert isinstance(score, float), f"rrf score must be float, got {type(score)}: {score}"
    return result

BENCH_QUERIES = [
    {"q":"folclore romaria tradicao Moura","relevant":["cultural","territorial"]},
    {"q":"tecnologia digital QR interoperabilidade API","relevant":["tecnologica"]},
    {"q":"orcamento financiamento DGARTES fundos","relevant":["economica"]},
    {"q":"RGPD consentimento direitos protecao dados","relevant":["legal"]},
    {"q":"camara municipio junta administracao publica","relevant":["administrativa"]},
    {"q":"ambiente natureza sustentabilidade floresta clima","relevant":["ambiental"]},
    {"q":"memoria identidade vivencia experiencia biografia","relevant":["humana"]},
    {"q":"comunidade intergeracional participacao inclusao","relevant":["social"]},
    {"q":"patrimonio etnografia costume lenda mito","relevant":["cultural"]},
    {"q":"freguesia concelho distrito territorio paisagem","relevant":["territorial"]},
]

def get_relevant(qi, chunks):
    rc = qi["relevant"]; rh = set()
    for c in chunks:
        tl = c["text"].lower()
        if any(any(p.lower() in tl for p in EIXOS_P.get(e,[])) for e in rc): rh.add(c["chunk_id"])
    return rh

def compute_metrics(result_ids, relevant_hashes, limit=10):
    rr = sum(1 for r in result_ids[:limit] if r in relevant_hashes)
    recall = rr/max(len(relevant_hashes),1)
    mrr = 0
    for i, r in enumerate(result_ids[:limit]):
        if r in relevant_hashes: mrr = 1.0/(i+1); break
    dcg = sum(1.0/math.log2(i+2) for i, r in enumerate(result_ids[:limit]) if r in relevant_hashes)
    idcg = sum(1.0/math.log2(i+2) for i in range(min(len(relevant_hashes), limit)))
    ndcg = dcg/max(idcg,1e-8)
    # citation precision: fraction of top-k results that are relevant
    cit_prec = rr / max(min(limit, len(result_ids)), 1)
    return {"recall@10": round(recall,4), "mrr": round(mrr,4), "ndcg@10": round(ndcg,4),
            "citation_precision": round(cit_prec,4)}

def main():
    t0 = time.time()
    print(f"=== MILK BENCHMARK (caches reused) | CUDA={CUDA} ===")

    # Load chunks + docs (no embeddings recalculation)
    chunks, docs = load_all_chunks()
    doc_list = list(docs.values())
    print(f"  {len(chunks)} chunks, {len(doc_list)} docs")

    # Build sparse indices (fast, needed for search)
    print("building chunk sparse...")
    chunk_idf, chunk_vecs = build_sparse([c["text"] for c in chunks])
    print("building doc sparse...")
    doc_idf, doc_vecs = build_sparse([d["text"] for d in doc_list])
    print(f"  chunk sparse: {len(chunk_idf)} terms, doc sparse: {len(doc_idf)} terms")

    # REUSE cached dense embeddings (no recalculation)
    print("loading dense caches...")
    chunk_dense, chunk_cache_hashes = load_dense_cache(INDEX_DIR / "chunk_dense_cache.npz")
    doc_dense, doc_cache_hashes = load_dense_cache(INDEX_DIR / "doc_dense_cache.npz")
    print(f"  chunk dense: {chunk_dense.shape}, doc dense: {doc_dense.shape}")

    # Load embedder for query encoding (search-time only)
    from sentence_transformers import SentenceTransformer
    use_gpu = CUDA and (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated())/1e9 > 4.0
    emb_model = SentenceTransformer("BAAI/bge-m3", device="cuda" if use_gpu else "cpu")
    print(f"  bge-m3 query encoder on {'cuda' if use_gpu else 'cpu'}")

    # Benchmark sample (5000 chunks for speed, full doc index)
    sample_size = min(5000, len(chunks))
    sample_idx = np.random.RandomState(42).choice(len(chunks), sample_size, replace=False)
    sample_chunks = [chunks[i] for i in sample_idx]
    sample_vecs = [chunk_vecs[i] for i in sample_idx]
    sample_dense = chunk_dense[torch.tensor(sample_idx, dtype=torch.long)]

    print(f"\n=== BENCHMARK (sample={sample_size} chunks, {len(doc_list)} docs) ===")
    results = {}

    for strat in ["DOCUMENT", "CHUNK", "HIERARCHICAL"]:
        print(f"\n  --- {strat} ---")
        all_m = []; total_lat = 0

        for qi in BENCH_QUERIES:
            q = qi["q"]
            relevant = get_relevant(qi, sample_chunks)
            t1 = time.time()

            if strat == "DOCUMENT":
                sp = sparse_search(q, doc_vecs, doc_idf, 10)
                dp = dense_search(q, doc_dense, emb_model, 10)
                fused = rrf_fusion(sp, dp, limit=10)
                # fused = [(index:int, score:float), ...]
                # Map doc index -> first sample chunk from that doc
                result_ids = []
                for idx, _score in fused:
                    assert isinstance(idx, int), f"doc idx must be int, got {type(idx)}"
                    dh = doc_list[idx]["hash"]
                    for sc in sample_chunks:
                        if sc["doc_hash"] == dh:
                            result_ids.append(sc["chunk_id"])
                            break

            elif strat == "CHUNK":
                sp = sparse_search(q, sample_vecs, chunk_idf, 10)
                dp = dense_search(q, sample_dense, emb_model, 10)
                fused = rrf_fusion(sp, dp, limit=10)
                result_ids = []
                for idx, _score in fused:
                    assert isinstance(idx, int), f"chunk idx must be int, got {type(idx)}"
                    result_ids.append(sample_chunks[idx]["chunk_id"])

            elif strat == "HIERARCHICAL":
                sp = sparse_search(q, sample_vecs, chunk_idf, 20)
                dp = dense_search(q, sample_dense, emb_model, 20)
                fused = rrf_fusion(sp, dp, limit=20)
                # Boost by parent doc frequency
                doc_counts = Counter()
                for idx, _score in fused:
                    assert isinstance(idx, int)
                    doc_counts[sample_chunks[idx]["doc_hash"]] += 1
                boosted = [(score + 0.05 * doc_counts[sample_chunks[idx]["doc_hash"]], idx)
                          for idx, score in fused]
                boosted.sort(key=lambda x: -x[0])
                result_ids = [sample_chunks[idx]["chunk_id"] for _, idx in boosted[:10]]

            lat = (time.time()-t1)*1000; total_lat += lat
            m = compute_metrics(result_ids, relevant)
            m["latency_ms"] = round(lat, 1)
            all_m.append(m)
            print(f"    {q[:35]:35s} R@10={m['recall@10']} MRR={m['mrr']} nDCG={m['ndcg@10']} citP={m['citation_precision']} {lat:.0f}ms")

        avg = {
            "recall@10": round(np.mean([m["recall@10"] for m in all_m]), 4),
            "mrr": round(np.mean([m["mrr"] for m in all_m]), 4),
            "ndcg@10": round(np.mean([m["ndcg@10"] for m in all_m]), 4),
            "citation_precision": round(np.mean([m["citation_precision"] for m in all_m]), 4),
            "avg_latency_ms": round(total_lat/len(all_m), 1),
        }
        results[strat] = {"per_query": all_m, "avg": avg}
        print(f"  AVG: R@10={avg['recall@10']} MRR={avg['mrr']} nDCG={avg['ndcg@10']} citP={avg['citation_precision']} lat={avg['avg_latency_ms']}ms")

    # Select winner by nDCG@10 (primary), then MRR (tiebreaker)
    winner = max(results.keys(),
                key=lambda s: (results[s]["avg"]["ndcg@10"], results[s]["avg"]["mrr"]))
    print(f"\n  WINNER: {winner}")
    print(f"    nDCG@10={results[winner]['avg']['ndcg@10']} MRR={results[winner]['avg']['mrr']}")
    print(f"    Recall@10={results[winner]['avg']['recall@10']} citP={results[winner]['avg']['citation_precision']}")
    print(f"    latency={results[winner]['avg']['avg_latency_ms']}ms")

    # Persist results
    report = {
        "schema": "ia_milk.chunk_benchmark.v1",
        "timestamp": now_iso(),
        "total_chunks": len(chunks), "total_docs": len(doc_list),
        "sample_size": sample_size,
        "device": str(DEVICE), "cuda": CUDA,
        "dense_model": "BAAI/bge-m3", "dense_dim": chunk_dense.shape[1],
        "caches_reused": True,
        "cache_files": ["chunk_dense_cache.npz", "doc_dense_cache.npz"],
        "strategies": results, "winner": winner,
        "winner_metrics": results[winner]["avg"],
        "bug_fix": "rrf_fusion returns (index:int, score:float) tuples; original code unpacked as (score, index) causing TypeError. Fixed with explicit int casts and assertions.",
        "elapsed_s": round(time.time()-t0, 1),
    }
    (INDEX_DIR / "benchmark_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    meta = {
        "total_chunks": len(chunks), "total_docs": len(doc_list),
        "chunk_idf_terms": len(chunk_idf), "doc_idf_terms": len(doc_idf),
        "dense_dim": chunk_dense.shape[1], "winner": winner,
        "built_at": now_iso(), "caches_reused": True,
    }
    (INDEX_DIR / "index_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  report -> {INDEX_DIR / 'benchmark_report.json'}")
    print(f"  meta -> {INDEX_DIR / 'index_meta.json'}")
    print(f"  ELAPSED: {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
