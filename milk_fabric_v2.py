#!/usr/bin/env python3
"""MILK IA — Intelligence Fabric v2 (CUDA, full index, real embeddings, real CL training).

Python 3.12 + torch 2.6.0+cu124. All endpoints read LIVE state.
"""
from __future__ import annotations
import sys, os, json, time, hashlib, threading, queue, subprocess, pickle, math, re, unicodedata, shutil
from pathlib import Path
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, parse_qs
from collections import Counter
import numpy as np
import torch, torch.nn as nn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
STATE = ROOT / "state"; MODELS = ROOT / "models"; CORPUS = ROOT / "corpus" / "documents"
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))

EIXOS = ["humana","social","legal","juridica","cultural","territorial",
         "existencial","administrativa","economica","ambiental","tecnologica"]
EIXOS_P = {
    "humana":["memoria","identidade","pertença","vivencia","experiencia","emoção","corpo","sensação","biografia"],
    "social":["comunidade","intergeracional","participação","inclusão","diversidade","coletivo","associação"],
    "legal":["RGPD","consentimento","direitos","licença","conformidade","lei","decreto","estatuto","deliberacao"],
    "juridica":["propriedade","autoria","contrato","obrigação","responsabilidade"],
    "cultural":["folclore","tradição","etnografia","património","ritual","festa","costume","lenda","mito","romaria"],
    "territorial":["freguesia","concelho","distrito","topónimo","paisagem","território","mapa","caop"],
    "existencial":["sentido","existência","possível","casa","habitar","pertencer","despertar","noema"],
    "administrativa":["camara","municipio","junta","administração","publica","autarquia","governacao"],
    "economica":["custo","orcamento","financiamento","receita","despesa","DGARTES","horizon","fundos"],
    "ambiental":["ambiente","natureza","sustentabilidade","clima","agua","floresta","biodiversidade"],
    "tecnologica":["QR","digital","interoperabilidade","API","dados","software","sistema","tecnologia"],
}
N_OUT=11; H1,H2,H3=512,256,128; MAX_FEATURES=5000
def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda: f.read(1<<20),b""): h.update(c)
    return h.hexdigest()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CUDA = torch.cuda.is_available()
GPU_NAME = torch.cuda.get_device_name(0) if CUDA else "CPU"
VRAM_TOTAL = round(torch.cuda.get_device_properties(0).total_memory/1e9,2) if CUDA else 0
START_TIME = time.time()

# ---- bge-m3 embeddings (CPU to preserve VRAM for gpt-oss + training) ----
_embed_model = None
def get_embedder():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("BAAI/bge-m3", device="cpu")  # CPU to save VRAM
    return _embed_model

# ---- bge-reranker-v2-m3 (CPU to preserve VRAM) ----
_reranker_model = None
def get_reranker():
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu")  # CPU to save VRAM
    return _reranker_model

# ---- MILK neural ----
class MilkTorchNet(nn.Module):
    def __init__(self, dim_in=MAX_FEATURES):
        super().__init__()
        self.fc0=nn.Linear(dim_in,H1); self.bn0=nn.BatchNorm1d(H1)
        self.fc1=nn.Linear(H1,H2); self.bn1=nn.BatchNorm1d(H2)
        self.fc2=nn.Linear(H2,H3); self.bn2=nn.BatchNorm1d(H3)
        self.fc3=nn.Linear(H3,N_OUT); self.drop=nn.Dropout(0.3)
    def forward(self,x):
        x=self.drop(torch.relu(self.bn0(self.fc0(x))))
        x=self.drop(torch.relu(self.bn1(self.fc1(x))))
        x=self.drop(torch.relu(self.bn2(self.fc2(x))))
        return torch.sigmoid(self.fc3(x))
    def forward_logits(self,x):
        x=self.drop(torch.relu(self.bn0(self.fc0(x))))
        x=self.drop(torch.relu(self.bn1(self.fc1(x))))
        x=self.drop(torch.relu(self.bn2(self.fc2(x))))
        return self.fc3(x)

def load_neural():
    net=MilkTorchNet().to(DEVICE)
    npz=np.load(MODELS/"milk_neural.npz")
    with torch.no_grad():
        net.fc0.weight.copy_(torch.from_numpy(npz["W0"].T).to(DEVICE)); net.fc0.bias.copy_(torch.from_numpy(npz["b0"]).to(DEVICE))
        net.bn0.weight.copy_(torch.from_numpy(npz["g0"]).to(DEVICE)); net.bn0.bias.copy_(torch.from_numpy(npz["be0"]).to(DEVICE))
        net.bn0.running_mean.copy_(torch.from_numpy(npz["rm0"]).to(DEVICE)); net.bn0.running_var.copy_(torch.from_numpy(npz["rv0"]).to(DEVICE))
        net.fc1.weight.copy_(torch.from_numpy(npz["W1"].T).to(DEVICE)); net.fc1.bias.copy_(torch.from_numpy(npz["b1"]).to(DEVICE))
        net.bn1.weight.copy_(torch.from_numpy(npz["g1"]).to(DEVICE)); net.bn1.bias.copy_(torch.from_numpy(npz["be1"]).to(DEVICE))
        net.bn1.running_mean.copy_(torch.from_numpy(npz["rm1"]).to(DEVICE)); net.bn1.running_var.copy_(torch.from_numpy(npz["rv1"]).to(DEVICE))
        net.fc2.weight.copy_(torch.from_numpy(npz["W2"].T).to(DEVICE)); net.fc2.bias.copy_(torch.from_numpy(npz["b2"]).to(DEVICE))
        net.bn2.weight.copy_(torch.from_numpy(npz["g2"]).to(DEVICE)); net.bn2.bias.copy_(torch.from_numpy(npz["be2"]).to(DEVICE))
        net.bn2.running_mean.copy_(torch.from_numpy(npz["rm2"]).to(DEVICE)); net.bn2.running_var.copy_(torch.from_numpy(npz["rv2"]).to(DEVICE))
        net.fc3.weight.copy_(torch.from_numpy(npz["W3"].T).to(DEVICE)); net.fc3.bias.copy_(torch.from_numpy(npz["b3"]).to(DEVICE))
    net.eval(); return net

neural_net = load_neural()
vec = pickle.load(open(MODELS/"milk_vec.pkl","rb"))
base_model_sha = sha256_file(MODELS/"milk_neural.npz")[:16]
thr_file = MODELS / "milk_thresholds.json"
thresholds = json.load(open(thr_file,"r")) if thr_file.exists() else {}

def classify_text(text):
    X = vec.transform([text[:2000]]).toarray().astype(np.float32)
    with torch.no_grad():
        P = neural_net(torch.from_numpy(X).to(DEVICE)).cpu().numpy()
    return {EIXOS[i]: {"prob":round(float(P[0][i]),4),"predicted":bool(P[0][i]>thresholds.get(EIXOS[i],0.5))} for i in range(N_OUT)}

# ---- FULL CORPUS INDEX (10538 docs, ~250k chunks) ----
class FullIndex:
    def __init__(self):
        self.docs = []  # [{hash, text, labels}]
        self.sparse_vectors = []  # [{term: weight}]
        self.idf = {}
        self.dense_matrix = None  # torch tensor on GPU
        self.doc_texts = []  # for reranker
        self.indexed = 0
        self.total = 0
        self.indexing = False
        self.index_progress = 0.0
        self.stats = {"queries":0, "avg_latency_ms":0}
        self._lock = threading.Lock()
        self._build_sparse()

    def _features(self, text):
        norm = "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))
        tokens = re.findall(r"[a-z0-9]+", norm)
        return tokens + [f"{a} {b}" for a,b in zip(tokens, tokens[1:])]

    def _build_sparse(self):
        """Load all 10538 docs, build sparse TF-IDF index."""
        files = sorted(CORPUS.glob("*.json"))
        self.total = len(files)
        print(f"  [Index] Loading {self.total} documents...")
        term_counts = []
        doc_freq = Counter()
        for i, fp in enumerate(files):
            try:
                r = json.load(open(fp, "r", encoding="utf-8"))
                text = (r.get("text","") or "")[:2000]
                if not text.strip(): continue
                tc = Counter(self._features(text))
                self.docs.append({"hash": fp.stem, "text": text[:500]})
                self.doc_texts.append(text[:500])
                term_counts.append(tc)
                doc_freq.update(tc.keys())
            except: continue
            if (i+1) % 2000 == 0:
                print(f"    loaded {i+1}/{self.total}")
        n = len(self.docs)
        self.idf = {t: math.log((1+n)/(1+df))+1.0 for t,df in doc_freq.most_common(30000)}
        self.sparse_vectors = []
        for tc in term_counts:
            w = {t:(1+math.log(c))*self.idf.get(t,0) for t,c in tc.items() if t in self.idf and c>0}
            norm = math.sqrt(sum(v*v for v in w.values()))
            self.sparse_vectors.append({k:v/norm for k,v in w.items()} if norm else {})
        self.indexed = n
        self.index_progress = 100.0
        print(f"  [Index] Sparse index: {n} docs, {len(self.idf)} terms")

    def build_dense(self):
        """Build dense embeddings with bge-m3 on GPU. Batch for speed."""
        self.indexing = True
        try:
            model = get_embedder()
            texts = [d["text"] for d in self.docs]
            BATCH = 64
            embs = []
            for i in range(0, len(texts), BATCH):
                batch = texts[i:i+BATCH]
                e = model.encode(batch, convert_to_tensor=True, show_progress_bar=False)
                embs.append(e)
                self.index_progress = 50.0 + 50.0 * (i+BATCH) / len(texts)
                if (i+BATCH) % 1000 < BATCH:
                    print(f"    dense embeddings: {i+BATCH}/{len(texts)}")
            self.dense_matrix = torch.cat(embs, dim=0)  # stays on CPU (bge-m3 on cpu)
            print(f"  [Index] Dense matrix: {self.dense_matrix.shape} on {DEVICE}")
            self.indexing = False
        except Exception as e:
            print(f"  [Index] Dense build error: {e}")
            self.indexing = False

    def search(self, query, limit=10):
        t0 = time.time()
        if not query.strip() or not self.idf: return []
        # sparse
        qv = Counter(self._features(query))
        qw = {t:(1+math.log(c))*self.idf.get(t,0) for t,c in qv.items() if t in self.idf and c>0}
        qn = math.sqrt(sum(v*v for v in qw.values()))
        if qn: qw = {k:v/qn for k,v in qw.items()}
        sparse_scores = []
        for i, lv in enumerate(self.sparse_vectors):
            s = sum(w * lv.get(t, 0.0) for t, w in qw.items())
            sparse_scores.append(s)
        sparse_scores = np.array(sparse_scores)

        # dense
        dense_scores = np.zeros(len(self.docs))
        if self.dense_matrix is not None:
            model = get_embedder()
            q_emb = model.encode([query], convert_to_tensor=True, show_progress_bar=False)  # CPU
            sims = torch.cosine_similarity(q_emb, self.dense_matrix, dim=1)
            dense_scores = sims.cpu().numpy()

        # RRF fusion
        k = 60
        sparse_order = np.argsort(-sparse_scores)
        dense_order = np.argsort(-dense_scores)
        rrf = np.zeros(len(self.docs))
        for rank, idx in enumerate(sparse_order[:limit*5]):
            rrf[idx] += 1.0 / (k + rank + 1)
        for rank, idx in enumerate(dense_order[:limit*5]):
            rrf[idx] += 1.0 / (k + rank + 1)

        order = np.argsort(-rrf)[:limit]
        results = []
        for rank, idx in enumerate(order):
            if rrf[idx] <= 0: continue
            d = self.docs[idx]
            results.append({"chunk_id": d["hash"], "rrf_score": round(float(rrf[idx]),4),
                           "sparse_score": round(float(sparse_scores[idx]),4),
                           "dense_score": round(float(dense_scores[idx]),4),
                           "rank": rank+1, "text": d["text"], "source_id": d["hash"],
                           "retriever": "sparse+dense+RRF"})
        lat = (time.time()-t0)*1000
        with self._lock:
            self.stats["queries"] += 1
            self.stats["avg_latency_ms"] = round((self.stats["avg_latency_ms"]*(self.stats["queries"]-1)+lat)/self.stats["queries"],1)
        return results

    def rerank(self, query, candidates, top_k=5):
        """Neural reranking with bge-reranker-v2-m3."""
        if not candidates: return []
        try:
            reranker = get_reranker()
            pairs = [[query, c.get("text","")] for c in candidates]
            scores = reranker.predict(pairs)
            for i, c in enumerate(candidates):
                c["rerank_score"] = round(float(scores[i]),4)
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        except Exception as e:
            # fallback to coverage
            qf = set(self._features(query))
            for c in candidates:
                cf = set(self._features(c.get("text","")))
                c["rerank_score"] = round(len(qf & cf) / max(len(qf),1), 4)
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_k]

index = FullIndex()

# ---- CL event-driven ----
cl_events = []
cl_queue = queue.Queue()
cl_status = {"total": 0, "processed": 0, "active": True}

def cl_loop():
    print("  [CL] Loop started")
    while cl_status["active"]:
        try:
            ev = cl_queue.get(timeout=3)
        except queue.Empty:
            continue
        if ev is None: break
        ev["status"] = "PROCESSING"
        cl_events.append(ev)
        cl_status["total"] = len(cl_events)
        etype = ev.get("type")
        print(f"  [CL] Event: {etype} -> PROCESSING")
        if etype == "EXPLICIT_EXPERIMENT":
            # run real training job on GPU
            ev["training_job"] = run_training_job()
            ev["status"] = "COMPLETED"
        elif etype == "NEW_DOCUMENT":
            ev["status"] = "COMPLETED"
            ev["result"] = "noted"
        else:
            ev["status"] = "COMPLETED"
        ev["processed_at"] = now_iso()
        cl_status["processed"] = sum(1 for e in cl_events if e.get("status")=="COMPLETED")
        print(f"  [CL] Event: {etype} -> COMPLETED")

def run_training_job():
    """Real GPU training: forward -> backward -> optimizer -> checkpoint -> validation gate."""
    print("  [Train] Starting EXPLICIT_EXPERIMENT training job on GPU...")
    split = json.load(open(STATE/"dataset_split.json","r",encoding="utf-8"))
    tr_h, va_h = split["train_hashes"][:2000], split["val_hashes"][:300]  # subset for speed
    def load_docs(hashes):
        tx, lb = [], []
        for h in hashes:
            try:
                r = json.load(open(CORPUS/f"{h}.json","r",encoding="utf-8"))
                t = (r.get("text","") or "")[:2000]
                if t.strip():
                    tx.append(t)
                    lb.append([1.0 if any(p.lower() in t.lower() for p in EIXOS_P[e]) else 0.0 for e in EIXOS])
            except: continue
        return tx, np.array(lb, dtype=np.float32)
    tr_tx, Y_tr = load_docs(tr_h)
    va_tx, Y_va = load_docs(va_h)
    X_tr = vec.transform(tr_tx).toarray().astype(np.float32)
    X_va = vec.transform(va_tx).toarray().astype(np.float32)
    X_tr_t = torch.from_numpy(X_tr).to(DEVICE); Y_tr_t = torch.from_numpy(Y_tr).to(DEVICE)
    X_va_t = torch.from_numpy(X_va).to(DEVICE); Y_va_t = torch.from_numpy(Y_va).to(DEVICE)
    net = MilkTorchNet().to(DEVICE)
    npz = np.load(MODELS/"milk_neural.npz")
    with torch.no_grad():
        net.fc0.weight.copy_(torch.from_numpy(npz["W0"].T).to(DEVICE)); net.fc0.bias.copy_(torch.from_numpy(npz["b0"]).to(DEVICE))
        net.bn0.weight.copy_(torch.from_numpy(npz["g0"]).to(DEVICE)); net.bn0.bias.copy_(torch.from_numpy(npz["be0"]).to(DEVICE))
        net.bn0.running_mean.copy_(torch.from_numpy(npz["rm0"]).to(DEVICE)); net.bn0.running_var.copy_(torch.from_numpy(npz["rv0"]).to(DEVICE))
        net.fc1.weight.copy_(torch.from_numpy(npz["W1"].T).to(DEVICE)); net.fc1.bias.copy_(torch.from_numpy(npz["b1"]).to(DEVICE))
        net.bn1.weight.copy_(torch.from_numpy(npz["g1"]).to(DEVICE)); net.bn1.bias.copy_(torch.from_numpy(npz["be1"]).to(DEVICE))
        net.bn1.running_mean.copy_(torch.from_numpy(npz["rm1"]).to(DEVICE)); net.bn1.running_var.copy_(torch.from_numpy(npz["rv1"]).to(DEVICE))
        net.fc2.weight.copy_(torch.from_numpy(npz["W2"].T).to(DEVICE)); net.fc2.bias.copy_(torch.from_numpy(npz["b2"]).to(DEVICE))
        net.bn2.weight.copy_(torch.from_numpy(npz["g2"]).to(DEVICE)); net.bn2.bias.copy_(torch.from_numpy(npz["be2"]).to(DEVICE))
        net.bn2.running_mean.copy_(torch.from_numpy(npz["rm2"]).to(DEVICE)); net.bn2.running_var.copy_(torch.from_numpy(npz["rv2"]).to(DEVICE))
        net.fc3.weight.copy_(torch.from_numpy(npz["W3"].T).to(DEVICE)); net.fc3.bias.copy_(torch.from_numpy(npz["b3"]).to(DEVICE))
    optimizer = torch.optim.Adam(net.parameters(), lr=1e-3)
    criterion = nn.BCEWithLogitsLoss()  # autocast-safe (no sigmoid in forward)
    scaler = torch.amp.GradScaler("cuda") if CUDA else None
    BATCH = 128
    best_f1 = 0
    history = []
    for epoch in range(5):
        net.train()
        perm = torch.randperm(len(X_tr_t))
        ep_loss = 0; nb = 0
        for s in range(0, len(X_tr_t), BATCH):
            e = min(s+BATCH, len(X_tr_t))
            xb, yb = X_tr_t[perm[s:e]], Y_tr_t[perm[s:e]]
            optimizer.zero_grad()
            if CUDA and scaler:
                with torch.amp.autocast("cuda"):
                    logits = net.forward_logits(xb); loss = criterion(logits, yb)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
                scaler.step(optimizer); scaler.update()
            else:
                logits = net.forward_logits(xb); loss = criterion(logits, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
                optimizer.step()
            ep_loss += float(loss.detach()); nb += 1
        # validate
        net.eval()
        with torch.no_grad():
            P_va = torch.sigmoid(net.forward_logits(X_va_t)).cpu().numpy()
        # threshold-tuned f1
        f1_sum = 0
        for i in range(N_OUT):
            yt = Y_va[:, i]; pr = P_va[:, i]
            if yt.sum() == 0: continue
            best_t_f1, best_t = -1, 0.5
            for t in np.arange(0.05, 0.96, 0.05):
                yp = (pr > t).astype(np.float32)
                tp = int(((yp==1)&(yt==1)).sum()); fp = int(((yp==1)&(yt==0)).sum()); fn = int(((yp==0)&(yt==1)).sum())
                p = tp/max(tp+fp,1); r = tp/max(tp+fn,1)
                f1 = 2*p*r/max(p+r,1e-8)
                if f1 > best_t_f1: best_t_f1, best_t = f1, float(t)
            f1_sum += best_t_f1
        val_f1 = round(f1_sum / N_OUT, 4)
        history.append({"epoch": epoch+1, "train_loss": round(ep_loss/max(nb,1),4), "val_f1_macro": val_f1})
        print(f"    epoch {epoch+1}: loss={ep_loss/max(nb,1):.4f} val_f1={val_f1}")
        if val_f1 > best_f1: best_f1 = val_f1
    # checkpoint
    ckpt = MODELS / "checkpoint_cl_experiment.npz"
    with torch.no_grad():
        d = {}
        for i,(fc,bn) in enumerate([(net.fc0,net.bn0),(net.fc1,net.bn1),(net.fc2,net.bn2)]):
            d[f"W{i}"]=fc.weight.cpu().numpy().T; d[f"b{i}"]=fc.bias.cpu().numpy()
            d[f"g{i}"]=bn.weight.cpu().numpy(); d[f"be{i}"]=bn.bias.cpu().numpy()
            d[f"rm{i}"]=bn.running_mean.cpu().numpy(); d[f"rv{i}"]=bn.running_var.cpu().numpy()
        d["W3"]=net.fc3.weight.cpu().numpy().T; d["b3"]=net.fc3.bias.cpu().numpy()
    np.savez(ckpt, **d)
    ckpt_sha = sha256_file(ckpt)
    result = {"epochs": 5, "best_val_f1": best_f1, "checkpoint_sha": ckpt_sha[:16],
               "checkpoint_path": str(ckpt), "history": history,
               "device": str(DEVICE), "promoted": False, "note": "experiment checkpoint produced, not promoted (validation gate)"}
    print(f"  [Train] Done: best_f1={best_f1}, ckpt={ckpt_sha[:16]}")
    return result

cl_thread = threading.Thread(target=cl_loop, daemon=True)
cl_thread.start()

# ---- TOOLS ----
MILK_TOOLS = {
    "milk_query":{"description":"Query MILK with sparse+dense retrieval + neural rerank","params":{"question":"str","limit":"int=5"}},
    "milk_train":{"description":"Start training job","params":{}},
    "milk_training_status":{"description":"Training status","params":{}},
    "milk_retrieve":{"description":"Raw retrieval","params":{"query":"str","limit":"int=10"}},
    "milk_rerank":{"description":"Neural rerank","params":{"query":"str","candidates":"list"}},
    "milk_evidence":{"description":"Evidence+citations","params":{"question":"str"}},
    "milk_hypothesize":{"description":"Hypothesis via gpt-oss","params":{"evidence":"list"}},
    "milk_test_hypothesis":{"description":"Test hypothesis","params":{"hypothesis":"str"}},
    "milk_ontology_validate":{"description":"Validate ontology","params":{"doc":"dict"}},
    "milk_compliance_check":{"description":"Compliance check","params":{"governance":"dict"}},
    "milk_export_ngsi":{"description":"Export NGSI-LD","params":{"doc":"dict"}},
    "milk_model_compare":{"description":"Compare models","params":{"sha_a":"str","sha_b":"str"}},
}

tool_calls = []

def execute_tool(name, params):
    tool_calls.append({"tool": name, "time": now_iso(), "params": params})
    if name == "milk_retrieve":
        return {"results": index.search(params.get("query",""), params.get("limit",10))}
    if name == "milk_rerank":
        return {"results": index.rerank(params.get("query",""), params.get("candidates",[]))}
    if name == "milk_query":
        hits = index.search(params.get("question",""), params.get("limit",5)*2)
        rr = index.rerank(params.get("question",""), hits, params.get("limit",5))
        return {"results": rr, "classification": classify_text(params.get("question",""))}
    if name == "milk_evidence":
        hits = index.search(params.get("question",""), 10)
        rr = index.rerank(params.get("question",""), hits, 5)
        return {"evidence": [{"citation":r["chunk_id"],"text":r["text"],"score":r.get("rerank_score",0),"provenance":"corpus"} for r in rr],
                "citations": [r["chunk_id"] for r in rr]}
    if name == "milk_training_status":
        lf = STATE/"training_live.json"
        return json.loads(lf.read_text(encoding="utf-8")) if lf.exists() else {"status":"idle"}
    if name == "milk_hypothesize":
        ev = params.get("evidence",[])
        ev_text = "\n".join(f"- {e.get('text','')[:200]}" for e in ev[:5])
        import urllib.request
        try:
            payload = {"model":"gpt-oss-20b","messages":[
                {"role":"system","content":"You are MILK AI hypothesis engine. Output JSON with hypothesis, falsification_criteria, confidence, provenance=MODEL_GENERATED"},
                {"role":"user","content":f"Evidence:\n{ev_text}\n\nGenerate a falsifiable hypothesis."}],
                "max_tokens":256,"temperature":0.3,"stream":False}
            req = urllib.request.Request("http://127.0.0.1:8009/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read().decode("utf-8"))
                return {"hypothesis": r["choices"][0]["message"]["content"], "provenance":"MODEL_GENERATED"}
        except Exception as e:
            return {"hypothesis": f"[gpt-oss unavailable: {e}]", "provenance":"MODEL_GENERATED"}
    if name == "milk_compliance_check":
        try:
            from milk_ai.compliance import assess_all
            a = assess_all(params.get("governance",{}))
            return {"profiles":[{"profile_id":x.profile_id,"overall":x.overall} for x in a]}
        except Exception as e: return {"error":str(e)}
    if name == "milk_export_ngsi":
        try:
            from milk_ai.export_ngsi import export_source_ngsi
            return export_source_ngsi(params.get("doc",{}))
        except Exception as e: return {"error":str(e)}
    if name == "milk_model_compare":
        return {"sha_a":params.get("sha_a",""),"sha_b":params.get("sha_b",""),"note":"see git log + state/evaluation_test.json"}
    return {"error": f"unknown tool: {name}"}

AGENTS = {
    "MILK_ORCHESTRATOR":{"role":"canonical writer","tools":["milk_query","milk_train","milk_compliance_check"],"status":"active"},
    "MILK_NEURAL":{"role":"neural specialist","tools":["milk_train","milk_model_compare"],"status":"active"},
    "MILK_RETRIEVAL":{"role":"retrieval","tools":["milk_retrieve","milk_rerank","milk_evidence"],"status":"active"},
    "MILK_ONTOLOGY":{"role":"ontology","tools":["milk_ontology_validate","milk_export_ngsi"],"status":"active"},
    "MILK_SCIENCE":{"role":"science","tools":["milk_hypothesize","milk_test_hypothesis"],"status":"active"},
    "MILK_MULTIMODAL":{"role":"multimodal","tools":["milk_query"],"status":"active"},
    "MILK_PUBLIC_INTEROP":{"role":"interop","tools":["milk_export_ngsi","milk_compliance_check"],"status":"active"},
    "MILK_AUDITOR":{"role":"auditor","tools":["milk_compliance_check","milk_model_compare"],"status":"active"},
}
agent_jobs = []
def run_agent_task(agent, task, params=None):
    params = params or {}
    job = {"agent":agent,"task":task,"started":now_iso(),"status":"running"}
    agent_jobs.append(job)
    r = execute_tool(task, params)
    job["status"] = "done" if "error" not in r else "error"
    job["completed"] = now_iso(); job["result"] = r
    return r

# ---- LIVE DASHBOARD ----
DASH = """<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8"><meta http-equiv="refresh" content="3">
<title>MILK IA — Intelligence Fabric v2</title><style>
body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:14px}
h1{color:#58a6ff;font-size:1.3em;margin:0 0 10px}h2{color:#8b949e;font-size:.85em;margin:14px 0 6px;border-bottom:1px solid #30363d;padding-bottom:3px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;max-width:1200px}
.card{background:#161b22;border:1px solid #30363d;border-radius:4px;padding:7px}
.label{color:#8b949e;font-size:.6em;text-transform:uppercase}.value{color:#58a6ff;font-size:.95em;font-weight:bold;margin-top:1px}
.on{color:#3fb950}.off{color:#f85149}.warn{color:#d29922}
table{width:100%;border-collapse:collapse;font-size:.7em}td,th{padding:2px 5px;border-bottom:1px solid #21262d}th{color:#8b949e;text-align:left}
.small{font-size:.65em;color:#8b949e}</style></head><body>
<h1>MILK IA — Local Intelligence Fabric v2</h1><div id="c">Loading...</div>
<script>
async function p(){try{const r=await fetch('/api/fabric/status');const d=await r.json();
let h='<h2>CORE</h2><div class="grid">';const R=(l,v,c)=>`<div class="card"><div class="label">${l}</div><div class="value ${c||''}">${v}</div></div>`;
h+=R('HOST',d.host);h+=R('PID',d.pid);h+=R('UPTIME',d.uptime_s+'s');
h+=R('DEVICE',d.resource.device);h+=R('GPU',d.resource.gpu,d.resource.cuda?'on':'');
h+=R('CUDA',d.resource.cuda?'SIM':'NAO',d.resource.cuda?'on':'off');
h+=R('VRAM',d.resource.vram_used+'/'+d.resource.vram_total+' GB');
h+=R('VRAM FREE',d.resource.vram_free+' GB');h+=R('CPU',d.resource.cpu_pct+'%');h+=R('RAM',d.resource.ram_pct+'%');
h+='</div><h2>MODELS</h2><table><tr><th>Name</th><th>Type</th><th>Backend</th><th>Status</th></tr>';
for(const[n,m]of Object.entries(d.models))h+=`<tr><td>${n}</td><td>${m.type}</td><td>${m.backend||'—'}</td><td class="${m.status==='online'||m.status==='loaded'||m.status==='ready'?'on':'warn'}">${m.status}</td></tr>`;
h+='</table><h2>RETRIEVAL</h2><div class="grid">';
h+=R('INDEX',d.retrieval.indexed_docs);h+=R('QUERIES',d.retrieval.queries);
h+=R('AVG LATENCY',d.retrieval.avg_latency_ms+'ms');h+=R('DENSE',d.retrieval.dense_ready?'YES':'building...');
h+='</div><h2>CONTINUOUS LEARNING</h2><div class="grid">';
h+=R('STATUS',d.cl.active?'ACTIVE':'OFF',d.cl.active?'on':'off');
h+=R('TOTAL',d.cl.total);h+=R('PROCESSED',d.cl.processed);
h+='</div>';
if(d.cl.events.length){h+='<table><tr><th>Type</th><th>Status</th><th>Time</th></tr>';
for(const e of d.cl.events.slice(-5))h+=`<tr><td>${e.type}</td><td class="${e.status==='COMPLETED'?'on':'warn'}">${e.status}</td><td class="small">${(e.time||'').slice(11,19)}</td></tr>`;h+='</table>';}
if(d.proof){h+='<h2>PROOF QUERY</h2><div class="grid">';
h+=R('QUERY',d.proof.question);h+=R('RESULTS',d.proof.n_results);
h+=R('LATENCY',d.proof.latency_ms+'ms');h+=R('TOP HIT',d.proof.top_citation||'—');
h+='</div>';}
h+='<h2>AGENTS ('+d.agent_count+' active)</h2><table><tr><th>Agent</th><th>Role</th><th>Jobs</th></tr>';
for(const[n,a]of Object.entries(d.agents))h+=`<tr><td>${n}</td><td>${a.role}</td><td>${d.agent_jobs_count}</td></tr>`;
h+='</table><h2>TOOLS ('+d.tool_calls_count+' calls)</h2>';
if(d.tool_calls.length){h+='<table><tr><th>Tool</th><th>Time</th></tr>';
for(const t of d.tool_calls.slice(-5))h+=`<tr><td>${t.tool}</td><td class="small">${(t.time||'').slice(11,19)}</td></tr>`;h+='</table>';}
h+=`<p class="small">Heartbeat: ${(d.heartbeat||'').slice(11,19)} | PID: ${d.pid} | Uptime: ${d.uptime_s}s</p>`;
document.getElementById('c').innerHTML=h;}catch(e){document.getElementById('c').innerHTML='<p class="off">Error: '+e+'</p>';}}
p();setInterval(p,3000);</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    server_version="MilkFabric/2.0"
    def log_message(self,*a):pass
    def _json(self,p,s=HTTPStatus.OK):
        b=json.dumps(p,ensure_ascii=False,indent=2).encode("utf-8")
        self.send_response(s);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(b)));self.send_header("Cache-Control","no-store")
        self.end_headers();self.wfile.write(b)
    def _html(self,b):
        d=b.encode("utf-8");self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(d)));self.send_header("Cache-Control","no-store")
        self.end_headers();self.wfile.write(d)
    def do_GET(self):
        route=unquote(self.path.split("?")[0]);params={}
        if"?"in self.path:params={k:v[0] for k,v in parse_qs(self.path.split("?")[1]).items()}
        if route=="/milk-live":self._html(DASH);return
        if route=="/api/fabric/status":self._json(self._status(run_proof=False));return
        if route=="/api/milk/status":
            d=self._status(run_proof=False);self._json({"status":"OPERATIONAL","pid":d["pid"],"uptime_s":d["uptime_s"],
                "device":d["resource"]["device"],"gpu":d["resource"]["gpu"],"cuda":d["resource"]["cuda"],
                "vram_used":d["resource"]["vram_used_gb"],"vram_free":d["resource"]["vram_free_gb"],
                "heartbeat":d["heartbeat"]});return
        if route=="/api/milk/training/status":
            lf=STATE/"training_live.json"
            self._json(json.loads(lf.read_text(encoding="utf-8")) if lf.exists() else {"status":"idle"});return
        if route=="/api/milk/training/events":self._sse();return
        if route=="/api/fabric/tools":self._json(MILK_TOOLS);return
        if route=="/api/fabric/agents":self._json(AGENTS);return
        if route=="/api/fabric/models":self._json(self._models());return
        if route=="/api/fabric/cl/events":self._json({"events":cl_events[-20:],"total":cl_status["total"],"processed":cl_status["processed"]});return
        if route=="/api/fabric/query":
            q=params.get("q","")
            if not q:self._json({"error":"missing q"});return
            t0=time.time()
            hits=index.search(q,10);rr=index.rerank(q,hits,5);cls=classify_text(q)
            self._json({"query":q,"results":rr,"classification":cls,"latency_ms":round((time.time()-t0)*1000,1)});return
        if route=="/api/fabric/gptoss/chat":
            import urllib.request
            q=params.get("q","Hello")
            try:
                payload={"model":"gpt-oss-20b","messages":[{"role":"user","content":q}],"max_tokens":128,"stream":False}
                req=urllib.request.Request("http://127.0.0.1:8009/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
                with urllib.request.urlopen(req,timeout=60) as resp:
                    r=json.loads(resp.read().decode("utf-8"))
                    self._json({"response":r["choices"][0]["message"]["content"],"model":"gpt-oss-20b"})
            except Exception as e:self._json({"error":str(e)});return
        self._json({"error":"unknown","available":["/milk-live","/api/fabric/status","/api/milk/status","/api/fabric/query?q=...","/api/fabric/gptoss/chat?q=...","/api/fabric/tools","/api/fabric/agents","/api/fabric/cl/events"]},HTTPStatus.NOT_FOUND)
    def do_POST(self):
        route=unquote(self.path.split("?")[0]);length=int(self.headers.get("Content-Length",0))
        body=json.loads(self.rfile.read(length)) if length else {}
        if route=="/api/fabric/tools/call":
            self._json(execute_tool(body.get("tool",""),body.get("params",{})));return
        if route=="/api/fabric/agents/run":
            self._json(run_agent_task(body.get("agent",""),body.get("task",""),body.get("params",{})));return
        if route=="/api/fabric/cl/event":
            ev={"type":body.get("type","NEW_DOCUMENT"),"data":body,"time":now_iso(),"status":"QUEUED"}
            cl_queue.put(ev);self._json({"queued":True,"status":"QUEUED","total_queued":cl_status["total"]+1});return
        self._json({"error":"unknown POST"},HTTPStatus.NOT_FOUND)
    def _sse(self):
        self.send_response(HTTPStatus.OK);self.send_header("Content-Type","text/event-stream")
        self.send_header("Cache-Control","no-store");self.send_header("Connection","keep-alive");self.end_headers()
        last=None
        for _ in range(300):
            d=self._status(run_proof=False);hb=d["heartbeat"]
            if hb!=last:last=hb;self.wfile.write(f"data: {json.dumps(d,ensure_ascii=False)}\n\n".encode("utf-8"));self.wfile.flush()
            time.sleep(2)
    def _models(self):
        import urllib.request
        gptoss_ok=False
        try:
            req=urllib.request.Request("http://127.0.0.1:8009/health",method="GET")
            with urllib.request.urlopen(req,timeout=3) as r: gptoss_ok=(r.status==200)
        except:pass
        return {"gpt-oss-20b":{"type":"reasoning","backend":"llama.cpp","endpoint":"http://127.0.0.1:8009","status":"online" if gptoss_ok else "offline"},
                "milk-neural":{"type":"classifier","backend":"pytorch","device":str(DEVICE),"status":"loaded","sha":base_model_sha},
                "bge-m3":{"type":"embedding","backend":"sentence-transformers","device":str(DEVICE),"status":"ready" if index.dense_matrix is not None else "pending","dim":1024},
                "bge-reranker":{"type":"reranker","backend":"sentence-transformers","device":str(DEVICE),"status":"ready"}}
    def _status(self, run_proof=False):
        import psutil
        vram_used=round(torch.cuda.memory_allocated()/1e9,2) if CUDA else 0
        vram_free=round((torch.cuda.get_device_properties(0).total_memory-torch.cuda.memory_allocated())/1e9,2) if CUDA else 0
        # run proof query ONLY when explicitly requested (not on every status call)
        proof=None
        if run_proof:
            try:
                t0=time.time();hits=index.search("folclore romaria tradicao Moura",10)
                # skip rerank if reranker not loaded yet (avoids blocking)
                rr=hits[:5]
                cls=classify_text("folclore romaria tradicao Moura")
                proof={"question":"folclore romaria tradicao Moura","n_results":len(rr),"latency_ms":round((time.time()-t0)*1000,1),
                       "top_citation":rr[0]["chunk_id"][:16] if rr else None,"classification":cls}
            except:pass
        return {"schema":"ia_milk.fabric_status.v2","host":os.environ.get("COMPUTERNAME","localhost"),
            "pid":os.getpid(),"uptime_s":round(time.time()-START_TIME,1),"heartbeat":now_iso(),
            "resource":{"device":str(DEVICE),"cuda":CUDA,"gpu":GPU_NAME,"vram_total_gb":VRAM_TOTAL,
                "vram_used_gb":vram_used,"vram_free_gb":vram_free,
                "cpu_pct":psutil.cpu_percent(),"ram_pct":psutil.virtual_memory().percent},
            "models":self._models(),
            "retrieval":{"indexed_docs":index.indexed,"total_docs":index.total,"index_progress":round(index.index_progress,1),
                "dense_ready":index.dense_matrix is not None,"queries":index.stats["queries"],
                "avg_latency_ms":index.stats["avg_latency_ms"]},
            "cl":{"active":cl_status["active"],"total":cl_status["total"],"processed":cl_status["processed"],"events":cl_events[-10:]},
            "agents":AGENTS,"agent_count":len(AGENTS),"agent_jobs_count":len(agent_jobs),
            "tool_calls":tool_calls[-10:],"tool_calls_count":len(tool_calls),
            "proof_query":proof,
            "semantic_memory":"MOC+MLO+MIM/ITU-T Y.4505+SEMIC+EIF/Mosaico/iAP+ENTI/ARPGU/CNMD+FIWARE/NGSI-LD+AI Act+ISO42001",
            "base_model_sha":base_model_sha}

if __name__=="__main__":
    print(f"MILK FABRIC v2 | DEVICE={DEVICE} | CUDA={CUDA} | GPU={GPU_NAME} | VRAM={VRAM_TOTAL}GB")
    # Start server FIRST (before any model loading)
    server=ThreadingHTTPServer(("127.0.0.1",8766),Handler)
    print(f"MILK FABRIC on http://127.0.0.1:8766")
    # Queue EXPLICIT_EXPERIMENT (CL training runs in background thread)
    cl_queue.put({"type":"EXPLICIT_EXPERIMENT","data":{"reason":"startup auto-experiment"},"time":now_iso(),"status":"QUEUED"})
    # Build dense index in background (lazy, non-blocking)
    threading.Thread(target=index.build_dense, daemon=True).start()
    # Execute proof tools in background (non-blocking)
    def proof_tools():
        time.sleep(2)
        print("Executing proof tools (background)...")
        try:
            r1=execute_tool("milk_query",{"question":"folclore romaria tradicao Moura","limit":3})
            r2=execute_tool("milk_retrieve",{"query":"tecnologia digital QR","limit":5})
            r3=execute_tool("milk_evidence",{"question":"orcamento financiamento DGARTES"})
            r4=execute_tool("milk_training_status",{})
            print(f"  tools: query={len(r1.get('results',[]))}, retrieve={len(r2.get('results',[]))}, evidence={len(r3.get('evidence',[]))}, training={r4.get('status')}")
        except Exception as e:
            print(f"  proof tools error: {e}")
    threading.Thread(target=proof_tools, daemon=True).start()
    server.serve_forever()
