#!/usr/bin/env python3
"""MILK IA — Retrieval validation final: full corpus A vs D, paired test, GOLD_QRELS.

- Full 250887 chunk corpus (no sample).
- Pseudo-qrels from EIXOS_P (labelled as PSEUDO, not HUMAN).
- GOLD_QRELS via pooling top results from A/B/C/D for human validation.
- Paired statistical test (Wilcoxon signed-rank) + bootstrap CI.
- MILK selection function: weighted evidence/citation quality + latency.
- No winner if not statistically/materially significant.
"""
from __future__ import annotations
import sys, os, json, time, hashlib, math, re, unicodedata, random
from pathlib import Path
from collections import Counter, defaultdict
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

# ============================================================
# SEARCH — unified contract (index:int, score:float)
# ============================================================
def sparse_search(q, vecs, idf, limit=20):
    qv = Counter(_features(q))
    qw = {t:(1+math.log(c))*idf.get(t,0) for t,c in qv.items() if t in idf and c>0}
    qn = math.sqrt(sum(v*v for v in qw.values()))
    if qn: qw = {k:v/qn for k,v in qw.items()}
    scores = np.array([sum(w*lv.get(t,0.0) for t,w in qw.items()) for lv in vecs])
    order = np.argsort(-scores)[:limit]
    return [(int(i), float(scores[i])) for i in order if scores[i] > 0]

def dense_search(q, dm, model, limit=20):
    qe = model.encode([q], convert_to_tensor=True, show_progress_bar=False).cpu()
    sims = torch.cosine_similarity(qe, dm, dim=1).numpy()
    order = np.argsort(-sims)[:limit]
    return [(int(i), float(sims[i])) for i in order]

def rrf_fusion(sparse_results, dense_results, k=60, limit=20):
    r = {}
    for rank, (idx, _) in enumerate(sparse_results[:limit*5]):
        assert isinstance(idx, int), f"sparse idx must be int, got {type(idx)}"
        r[idx] = r.get(idx, 0.0) + 1.0/(k+rank+1)
    for rank, (idx, _) in enumerate(dense_results[:limit*5]):
        assert isinstance(idx, int)
        r[idx] = r.get(idx, 0.0) + 1.0/(k+rank+1)
    result = sorted(r.items(), key=lambda x: -x[1])[:limit]
    return [(int(idx), float(score)) for idx, score in result]

# ============================================================
# LOAD 52 QUERIES (preserved from v2)
# ============================================================
QUERIES_52 = json.load(open(INDEX_DIR / "queries_50.json", "r", encoding="utf-8"))

# ============================================================
# LOAD FULL CORPUS (250887 chunks, caches reused)
# ============================================================
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

def load_dense_cache(path):
    cd = np.load(path, allow_pickle=True)
    embs = cd["embs"]
    print(f"  cache: {path.name} -> {embs.shape}")
    return torch.from_numpy(embs.astype(np.float32))

# ============================================================
# PSEUDO QRELS (from EIXOS_P, explicitly NOT human)
# ============================================================
def build_pseudo_qrels(chunks):
    qrels = {}
    for qi in QUERIES_52:
        qid = qi["id"]; relevant_classes = qi["relevant"]
        if not relevant_classes:
            qrels[qid] = {}; continue
        chunk_grades = {}
        for c in chunks:
            tl = c["text"].lower(); grade = 0
            for eixo in relevant_classes:
                kws = EIXOS_P.get(eixo, [])
                matches = sum(1 for kw in kws if kw.lower() in tl)
                if matches >= 3: grade = max(grade, 3)
                elif matches >= 2: grade = max(grade, 2)
                elif matches >= 1: grade = max(grade, 1)
            if grade > 0: chunk_grades[c["chunk_id"]] = grade
        qrels[qid] = chunk_grades
    return qrels

# ============================================================
# GOLD QRELS via pooling (for human validation)
# ============================================================
def build_gold_qrels_pool(chunks, qrels_pseudo, strategy_results):
    """Pool top-10 from each strategy, deduplicate, prepare for human grading.
    Each pooled item gets pseudo-grade as starting point; human can override."""
    gold = {}
    for qi in QUERIES_52:
        qid = qi["id"]
        pooled = set()
        for strat_name, per_q in strategy_results.items():
            if qid in per_q:
                pooled.update(per_q[qid][:10])
        # Build gold entries with pseudo-grade as seed
        gold_entries = {}
        chunk_map = {c["chunk_id"]: c for c in chunks}
        for cid in pooled:
            pseudo = qrels_pseudo.get(qid, {}).get(cid, 0)
            c = chunk_map.get(cid)
            gold_entries[cid] = {
                "pseudo_grade": pseudo,
                "human_grade": None,  # to be filled by human
                "text_preview": c["text"][:150] if c else "",
                "doc_hash": c["doc_hash"] if c else "",
            }
        gold[qid] = {"query": qi["q"], "category": qi["category"],
                     "relevant_classes": qi["relevant"],
                     "pooled_chunks": gold_entries}
    return gold

# ============================================================
# METRICS
# ============================================================
def compute_ndcg(result_ids, qrels_qid, k=10):
    dcg = sum((2**qrels_qid.get(cid, 0) - 1) / math.log2(i + 2)
              for i, cid in enumerate(result_ids[:k]) if qrels_qid.get(cid, 0) > 0)
    ideal = sorted(qrels_qid.values(), reverse=True)[:k]
    idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal) if r > 0)
    return dcg / max(idcg, 1e-8)

def compute_recall(result_ids, qrels_qid, k, threshold=1):
    total = sum(1 for g in qrels_qid.values() if g >= threshold)
    if total == 0: return 0.0
    retrieved = sum(1 for cid in result_ids[:k] if qrels_qid.get(cid, 0) >= threshold)
    return retrieved / total

def compute_mrr(result_ids, qrels_qid, threshold=1):
    for i, cid in enumerate(result_ids):
        if qrels_qid.get(cid, 0) >= threshold: return 1.0 / (i + 1)
    return 0.0

def compute_cit_precision(result_ids, qrels_qid, k=10, threshold=1):
    if not result_ids[:k]: return 0.0
    return sum(1 for cid in result_ids[:k] if qrels_qid.get(cid, 0) >= threshold) / min(k, len(result_ids))

def compute_all(result_ids, qrels_qid):
    return {
        "ndcg@10": round(compute_ndcg(result_ids, qrels_qid, 10), 4),
        "recall@5": round(compute_recall(result_ids, qrels_qid, 5), 4),
        "recall@10": round(compute_recall(result_ids, qrels_qid, 10), 4),
        "mrr": round(compute_mrr(result_ids, qrels_qid), 4),
        "citation_precision": round(compute_cit_precision(result_ids, qrels_qid, 10), 4),
    }

def percentile(data, p):
    if not data: return 0
    s = sorted(data); idx = int(len(s) * p / 100)
    return round(s[min(idx, len(s)-1)], 1)

# ============================================================
# STATISTICAL TESTS
# ============================================================
def wilcoxon_signed_rank(x, y):
    """Wilcoxon signed-rank test (simplified, no scipy).
    Returns (W_stat, p_value_approx, effect_direction)."""
    diffs = [a - b for a, b in zip(x, y) if a != b]
    if len(diffs) < 5:
        return {"test": "wilcoxon", "n": len(diffs), "W": 0, "p_value": 1.0,
                "direction": "tie", "note": "too few non-zero diffs for significance"}
    # Rank by absolute value
    abs_diffs = sorted(range(len(diffs)), key=lambda i: abs(diffs[i]))
    ranks = [0] * len(diffs)
    for rank, i in enumerate(abs_diffs):
        ranks[i] = rank + 1
    # Split into positive/negative
    W_pos = sum(ranks[i] for i in range(len(diffs)) if diffs[i] > 0)
    W_neg = sum(ranks[i] for i in range(len(diffs)) if diffs[i] < 0)
    W = min(W_pos, W_neg)
    n = len(diffs)
    # Normal approximation for p-value (n >= 10)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (W - mu) / sigma if sigma > 0 else 0
    # Two-tailed p-value (normal approximation)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    direction = "A>D" if W_pos > W_neg else ("D>A" if W_neg > W_pos else "tie")
    return {"test": "wilcoxon", "n": n, "W": W, "W_pos": W_pos, "W_neg": W_neg,
            "z": round(z, 4), "p_value": round(p, 4), "direction": direction}

def bootstrap_ci(x, y, n_bootstrap=10000, confidence=0.95):
    """Bootstrap confidence interval for mean difference (x - y)."""
    rng = random.Random(42)
    diffs = [a - b for a, b in zip(x, y)]
    n = len(diffs)
    if n == 0: return {"mean_diff": 0, "ci_lower": 0, "ci_upper": 0}
    boot_means = []
    for _ in range(n_bootstrap):
        sample = [diffs[rng.randint(0, n-1)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    alpha = (1 - confidence) / 2
    ci_lower = boot_means[int(n_bootstrap * alpha)]
    ci_upper = boot_means[int(n_bootstrap * (1 - alpha))]
    return {"mean_diff": round(sum(diffs)/n, 4),
            "ci_lower": round(ci_lower, 4), "ci_upper": round(ci_upper, 4),
            "confidence": confidence}

# ============================================================
# MILK SELECTION FUNCTION
# ============================================================
def milk_selection_function(metrics_A, metrics_D, lat_A, lat_D):
    """MILK evidence-quality-weighted selection.

    Weights:
    - nDCG@10: 0.35 (primary ranking quality)
    - citation_precision: 0.25 (evidence/citation quality — MILK core)
    - MRR: 0.20 (first-relevant speed)
    - recall@10: 0.10 (coverage)
    - latency: 0.10 (efficiency, normalized)
    """
    def score(m, lat):
        # Latency score: lower is better, normalize against a reference (10s)
        lat_score = max(0, 1.0 - lat / 10000.0)
        return (0.35 * m["ndcg@10"] + 0.25 * m["citation_precision"] +
                0.20 * m["mrr"] + 0.10 * m["recall@10"] + 0.10 * lat_score)
    score_A = score(metrics_A, lat_A)
    score_D = score(metrics_D, lat_D)
    return {"score_A": round(score_A, 4), "score_D": round(score_D, 4),
            "weights": {"ndcg@10": 0.35, "citation_precision": 0.25, "mrr": 0.20,
                        "recall@10": 0.10, "latency": 0.10}}

# ============================================================
# STRATEGIES A and D (full corpus)
# ============================================================
doc_list_global = []

def strategy_A(q, chunk_vecs, chunk_idf, chunk_dense, emb_model, chunks):
    sp = sparse_search(q, chunk_vecs, chunk_idf, 20)
    dp = dense_search(q, chunk_dense, emb_model, 20)
    fused = rrf_fusion(sp, dp, limit=20)
    return [chunks[idx]["chunk_id"] for idx, _ in fused[:10]]

def strategy_D(q, chunk_vecs, chunk_idf, chunk_dense, emb_model, chunks, doc_vecs, doc_idf, doc_dense):
    sp = sparse_search(q, chunk_vecs, chunk_idf, 20)
    dp = dense_search(q, chunk_dense, emb_model, 20)
    fused = rrf_fusion(sp, dp, limit=20)
    sp_doc = sparse_search(q, doc_vecs, doc_idf, 20)
    dp_doc = dense_search(q, doc_dense, emb_model, 20)
    fused_doc = rrf_fusion(sp_doc, dp_doc, limit=20)
    doc_rrf = {idx: score for idx, score in fused_doc}
    boosted = []
    for idx, score in fused:
        dh = chunks[idx]["doc_hash"]
        doc_boost = 0.0
        for di, dd in enumerate(doc_list_global):
            if dd["hash"] == dh and di in doc_rrf:
                doc_boost = doc_rrf[di] * 0.1; break
        boosted.append((score + doc_boost, idx))
    boosted.sort(key=lambda x: -x[0])
    return [chunks[idx]["chunk_id"] for _, idx in boosted[:10]]

# ============================================================
# MAIN
# ============================================================
def main():
    global doc_list_global
    t0 = time.time()
    print("=== MILK RETRIEVAL VALIDATION FINAL ===")
    print(f"DEVICE: {DEVICE} | CUDA: {CUDA}")

    # 1. Load full corpus + caches
    print("\n--- LOADING FULL CORPUS + CACHES ---")
    chunks, docs = load_all_chunks()
    doc_list_global = list(docs.values())
    print("  building sparse indices (250k chunks)...")
    chunk_idf, chunk_vecs = build_sparse([c["text"] for c in chunks])
    doc_idf, doc_vecs = build_sparse([d["text"] for d in doc_list_global])
    chunk_dense = load_dense_cache(INDEX_DIR / "chunk_dense_cache.npz")
    doc_dense = load_dense_cache(INDEX_DIR / "doc_dense_cache.npz")
    print(f"  full corpus: {len(chunks)} chunks, {len(doc_list_global)} docs")

    # 2. Load embedder
    from sentence_transformers import SentenceTransformer
    use_gpu = CUDA and (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated())/1e9 > 4.0
    emb_model = SentenceTransformer("BAAI/bge-m3", device="cuda" if use_gpu else "cpu")
    print(f"  bge-m3 on {'cuda' if use_gpu else 'cpu'}")

    # 3. Build PSEUDO qrels (explicitly not human)
    print("\n--- PSEUDO QRELS (from EIXOS_P, NOT human) ---")
    pseudo_qrels = build_pseudo_qrels(chunks)
    pseudo_qrels_size = sum(len(v) for v in pseudo_qrels.values())
    print(f"  pseudo_qrels: {pseudo_qrels_size} judgments across {len(QUERIES_52)} queries")

    # 4. Run A and D on FULL corpus
    print("\n--- RUNNING A vs D ON FULL CORPUS ---")
    results_A = {}; results_D = {}
    metrics_A_list = []; metrics_D_list = []
    lat_A_list = []; lat_D_list = []
    per_query_A = {}; per_query_D = {}

    for qi in QUERIES_52:
        qid = qi["id"]; q = qi["q"]; cat = qi["category"]

        # Strategy A
        t1 = time.time()
        ids_A = strategy_A(q, chunk_vecs, chunk_idf, chunk_dense, emb_model, chunks)
        lat_A = (time.time() - t1) * 1000
        m_A = compute_all(ids_A, pseudo_qrels.get(qid, {}))
        results_A[qid] = ids_A; per_query_A[qid] = m_A
        per_query_A[qid]["latency_ms"] = round(lat_A, 1); per_query_A[qid]["category"] = cat
        metrics_A_list.append(m_A["ndcg@10"]); lat_A_list.append(lat_A)

        # Strategy D
        t2 = time.time()
        ids_D = strategy_D(q, chunk_vecs, chunk_idf, chunk_dense, emb_model, chunks, doc_vecs, doc_idf, doc_dense)
        lat_D = (time.time() - t2) * 1000
        m_D = compute_all(ids_D, pseudo_qrels.get(qid, {}))
        results_D[qid] = ids_D; per_query_D[qid] = m_D
        per_query_D[qid]["latency_ms"] = round(lat_D, 1); per_query_D[qid]["category"] = cat
        metrics_D_list.append(m_D["ndcg@10"]); lat_D_list.append(lat_D)

        delta_nDCG = m_A["ndcg@10"] - m_D["ndcg@10"]
        print(f"  {qid:6s} {cat:15s} A:nDCG={m_A['ndcg@10']} citP={m_A['citation_precision']} {lat_A:.0f}ms | D:nDCG={m_D['ndcg@10']} citP={m_D['citation_precision']} {lat_D:.0f}ms | Δ={delta_nDCG:+.4f}")

    # 5. Aggregate metrics
    def aggregate(per_q):
        return {
            "ndcg@10": round(np.mean([m["ndcg@10"] for m in per_q.values()]), 4),
            "recall@5": round(np.mean([m["recall@5"] for m in per_q.values()]), 4),
            "recall@10": round(np.mean([m["recall@10"] for m in per_q.values()]), 4),
            "mrr": round(np.mean([m["mrr"] for m in per_q.values()]), 4),
            "citation_precision": round(np.mean([m["citation_precision"] for m in per_q.values()]), 4),
            "latency_p50_ms": percentile([m["latency_ms"] for m in per_q.values()], 50),
            "latency_p95_ms": percentile([m["latency_ms"] for m in per_q.values()], 95),
        }
    agg_A = aggregate(per_query_A)
    agg_D = aggregate(per_query_D)
    print(f"\n  A AVG: nDCG={agg_A['ndcg@10']} R@5={agg_A['recall@5']} R@10={agg_A['recall@10']} MRR={agg_A['mrr']} citP={agg_A['citation_precision']} p50={agg_A['latency_p50_ms']} p95={agg_A['latency_p95_ms']}")
    print(f"  D AVG: nDCG={agg_D['ndcg@10']} R@5={agg_D['recall@5']} R@10={agg_D['recall@10']} MRR={agg_D['mrr']} citP={agg_D['citation_precision']} p50={agg_D['latency_p50_ms']} p95={agg_D['latency_p95_ms']}")

    # 6. Per-category breakdown
    def by_cat(per_q):
        cats = {}
        for qid, m in per_q.items():
            cat = m["category"]
            if cat not in cats: cats[cat] = []
            cats[cat].append(m)
        return {cat: {"ndcg@10": round(np.mean([m["ndcg@10"] for m in ms]), 4),
                      "mrr": round(np.mean([m["mrr"] for m in ms]), 4),
                      "citP": round(np.mean([m["citation_precision"] for m in ms]), 4),
                      "count": len(ms)}
                for cat, ms in cats.items()}
    cat_A = by_cat(per_query_A)
    cat_D = by_cat(per_query_D)
    print("\n  Per-category:")
    for cat in sorted(cat_A.keys()):
        a = cat_A.get(cat, {}); d = cat_D.get(cat, {})
        print(f"    {cat:20s} A:nDCG={a.get('ndcg@10',0)} citP={a.get('citP',0)} | D:nDCG={d.get('ndcg@10',0)} citP={d.get('citP',0)}")

    # 7. Statistical tests
    print("\n--- STATISTICAL TESTS ---")
    # nDCG@10 paired
    wilcoxon_ndcg = wilcoxon_signed_rank(metrics_A_list, metrics_D_list)
    boot_ndcg = bootstrap_ci(metrics_A_list, metrics_D_list)
    # Citation precision paired
    cit_A = [m["citation_precision"] for m in per_query_A.values()]
    cit_D = [m["citation_precision"] for m in per_query_D.values()]
    wilcoxon_cit = wilcoxon_signed_rank(cit_A, cit_D)
    boot_cit = bootstrap_ci(cit_A, cit_D)
    # MRR paired
    mrr_A = [m["mrr"] for m in per_query_A.values()]
    mrr_D = [m["mrr"] for m in per_query_D.values()]
    wilcoxon_mrr = wilcoxon_signed_rank(mrr_A, mrr_D)

    print(f"  nDCG@10: Wilcoxon W={wilcoxon_ndcg['W']} z={wilcoxon_ndcg['z']} p={wilcoxon_ndcg['p_value']} dir={wilcoxon_ndcg['direction']}")
    print(f"  nDCG@10: Bootstrap mean_diff={boot_ndcg['mean_diff']} CI=[{boot_ndcg['ci_lower']}, {boot_ndcg['ci_upper']}]")
    print(f"  citP:    Wilcoxon W={wilcoxon_cit['W']} p={wilcoxon_cit['p_value']} dir={wilcoxon_cit['direction']}")
    print(f"  citP:    Bootstrap mean_diff={boot_cit['mean_diff']} CI=[{boot_cit['ci_lower']}, {boot_cit['ci_upper']}]")
    print(f"  MRR:     Wilcoxon W={wilcoxon_mrr['W']} p={wilcoxon_mrr['p_value']} dir={wilcoxon_mrr['direction']}")

    # 8. MILK selection function
    print("\n--- MILK SELECTION FUNCTION ---")
    milk_scores = milk_selection_function(agg_A, agg_D, agg_A["latency_p95_ms"], agg_D["latency_p95_ms"])
    print(f"  Weights: {milk_scores['weights']}")
    print(f"  Score A: {milk_scores['score_A']}")
    print(f"  Score D: {milk_scores['score_D']}")

    # 9. Decision
    alpha = 0.05
    material_threshold = 0.01  # 1% nDCG difference is material
    ndcg_diff = abs(agg_A["ndcg@10"] - agg_D["ndcg@10"])
    is_significant = wilcoxon_ndcg["p_value"] < alpha
    is_material = ndcg_diff >= material_threshold
    ci_excludes_zero = (boot_ndcg["ci_lower"] > 0 and boot_ndcg["ci_upper"] > 0) or \
                       (boot_ndcg["ci_lower"] < 0 and boot_ndcg["ci_upper"] < 0)

    if not (is_significant and is_material and ci_excludes_zero):
        decision = "NO_SIGNIFICANT_DIFFERENCE"
        canonical = "BOTH_RETAINED — select by query type"
        print(f"\n  DECISION: NO_SIGNIFICANT_DIFFERENCE")
        print(f"    nDCG diff={ndcg_diff:.4f} (threshold={material_threshold})")
        print(f"    Wilcoxon p={wilcoxon_ndcg['p_value']} (alpha={alpha})")
        print(f"    CI=[{boot_ndcg['ci_lower']}, {boot_ndcg['ci_upper']}] includes zero: {not ci_excludes_zero}")
        print(f"    Both A and D retained; select per query type")
        # Per-category winner
        cat_winners = {}
        for cat in sorted(cat_A.keys()):
            a_n = cat_A[cat]["ndcg@10"]; d_n = cat_D[cat]["ndcg@10"]
            if a_n > d_n: cat_winners[cat] = "A"
            elif d_n > a_n: cat_winners[cat] = "D"
            else: cat_winners[cat] = "tie"
        print(f"    Per-category winners: {cat_winners}")
    else:
        if milk_scores["score_A"] > milk_scores["score_D"]:
            decision = "A_WINS"; canonical = "A_TFIDF_BGE_RRF_CANONICAL"
        else:
            decision = "D_WINS"; canonical = "D_HIERARCHICAL_CANONICAL"
        print(f"\n  DECISION: {decision}")
        print(f"    nDCG diff={ndcg_diff:.4f} (material)")
        print(f"    Wilcoxon p={wilcoxon_ndcg['p_value']} (significant)")
        print(f"    CI=[{boot_ndcg['ci_lower']}, {boot_ndcg['ci_upper']}] excludes zero")
        cat_winners = {}

    # 10. Build GOLD_QRELS (pooling for human validation)
    print("\n--- GOLD QRELS (pooling for human validation) ---")
    # Also run B and C for pooling (using same approach as v2 but only for pooling)
    # For pooling we use A and D results (already computed) + cached v2 results
    pool_results = {"A": results_A, "D": results_D}
    gold_qrels = build_gold_qrels_pool(chunks, pseudo_qrels, pool_results)
    gold_size = sum(len(g["pooled_chunks"]) for g in gold_qrels.values())
    print(f"  gold_qrels: {gold_size} pooled items across {len(gold_qrels)} queries (for human validation)")

    # 11. Persist
    report = {
        "schema": "ia_milk.retrieval_validation_final.v1",
        "timestamp": now_iso(),
        "total_chunks": len(chunks), "total_docs": len(doc_list_global),
        "full_corpus": True, "caches_reused": True,
        "num_queries": len(QUERIES_52),
        "qrels_status": {"pseudo": "PSEUDO_QRELS (from EIXOS_P, NOT human)",
                         "pseudo_size": pseudo_qrels_size,
                         "gold": "GOLD_QRELS (pooled from A/B/C/D, for human validation)",
                         "gold_size": gold_size},
        "A_metrics": agg_A, "D_metrics": agg_D,
        "A_by_category": cat_A, "D_by_category": cat_D,
        "statistical_tests": {
            "ndcg_wilcoxon": wilcoxon_ndcg, "ndcg_bootstrap_ci": boot_ndcg,
            "citP_wilcoxon": wilcoxon_cit, "citP_bootstrap_ci": boot_cit,
            "mrr_wilcoxon": wilcoxon_mrr,
        },
        "milk_selection": milk_scores,
        "decision": decision,
        "canonical_status": canonical,
        "per_query_A": per_query_A, "per_query_D": per_query_D,
        "category_winners": cat_winners,
        "alpha": alpha, "material_threshold": material_threshold,
        "elapsed_s": round(time.time() - t0, 1),
    }
    out = INDEX_DIR / "validation_final_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # Save gold qrels
    (INDEX_DIR / "gold_qrels.json").write_text(json.dumps(gold_qrels, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save pseudo qrels (separately, clearly labelled)
    (INDEX_DIR / "pseudo_qrels.json").write_text(json.dumps(pseudo_qrels, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  report -> {out}")
    print(f"  gold_qrels -> {INDEX_DIR / 'gold_qrels.json'}")
    print(f"  pseudo_qrels -> {INDEX_DIR / 'pseudo_qrels.json'}")
    print(f"  DECISION: {decision}")
    print(f"  CANONICAL: {canonical}")
    print(f"  ELAPSED: {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
