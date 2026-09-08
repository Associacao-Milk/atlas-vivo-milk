#!/usr/bin/env python3
"""MILK IA — Modelo Neural (numpy puro, backpropagation real).

Rede neural MLP 4 camadas com backpropagation manual, Adam optimizer,
BatchNorm, Dropout, pesos persistentes e fine-tuning continuo.

Arquitetura: 5000 -> 512 -> 256 -> 128 -> 11 (multi-label sigmoid)

Autor: Eduardo Mauricio Vieira Cabral e Araujo (Eduardo Mauer)
"""
from __future__ import annotations
import json, os, sys, datetime, pickle, time
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from sklearn.feature_extraction.text import TfidfVectorizer

STATE_DIR = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
CORPUS = STATE_DIR / "corpus" / "documents"
MODELS_DIR = STATE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
AUTOR = "Eduardo Mauricio Vieira Cabral e Araujo"

MAX_FEATURES = 5000; H1, H2, H3 = 512, 256, 128; N_OUT = 11
EPOCHS = 5; BATCH = 64; LR = 0.001; DROPOUT = 0.3

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

def relu(x): return np.maximum(0, x)
def relu_g(x): return (x > 0).astype(np.float32)
def sig(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))
def bce(p, t): return -float(np.mean(t*np.log(p+1e-8) + (1-t)*np.log(1-p+1e-8)))

class MilkNet:
    """MLP 4 camadas: input -> H1 -> H2 -> H3 -> output. Backprop + Adam."""
    def __init__(self, dim_in=MAX_FEATURES):
        dims = [dim_in, H1, H2, H3, N_OUT]
        rng = np.random.default_rng(42)
        self.W = []; self.b = []
        for i in range(4):
            fi = dims[i]
            self.W.append((rng.standard_normal((dims[i], dims[i+1])) * np.sqrt(2.0/fi)).astype(np.float32))
            self.b.append(np.zeros(dims[i+1], dtype=np.float32))
        # BatchNorm (3 camadas ocultas)
        self.g = [np.ones(d, dtype=np.float32) for d in [H1,H2,H3]]
        self.be = [np.zeros(d, dtype=np.float32) for d in [H1,H2,H3]]
        self.rm = [np.zeros(d, dtype=np.float32) for d in [H1,H2,H3]]
        self.rv = [np.ones(d, dtype=np.float32) for d in [H1,H2,H3]]
        # Adam
        self._adam_init()
        self.t = 0; self.b1=0.9; self.b2=0.999; self.eps=1e-8

    def _adam_init(self):
        z = lambda s: np.zeros_like(s)
        self.mW=[z(w) for w in self.W]; self.vW=[z(w) for w in self.W]
        self.mb=[z(b) for b in self.b]; self.vb=[z(b) for b in self.b]
        self.mg=[z(g) for g in self.g]; self.vg=[z(g) for g in self.g]
        self.mbe=[z(b) for b in self.be]; self.vbe=[z(b) for b in self.be]

    def forward(self, x, train=True):
        c = {"x": x}; a = x
        for i in range(4):
            z = a @ self.W[i] + self.b[i]
            if i < 3:
                if train:
                    m = z.mean(0); v = z.var(0)
                    self.rm[i] = 0.9*self.rm[i]+0.1*m; self.rv[i] = 0.9*self.rv[i]+0.1*v
                else: m, v = self.rm[i], self.rv[i]
                z = (z - m) / np.sqrt(v + 1e-8)
                z = z * self.g[i] + self.be[i]
                c[f"z{i}"] = z
                a = relu(z)
                if train:
                    mask = (np.random.rand(*a.shape) > DROPOUT).astype(np.float32) / (1-DROPOUT)
                    a = a * mask; c[f"m{i}"] = mask
                c[f"a{i}"] = a
            else:
                a = sig(z)
            c[f"o{i}"] = a
        return a, c

    def backward(self, c, y):
        m = y.shape[0]
        gW = [None]*4; gb = [None]*4; gg = [None]*3; gbe = [None]*3
        da = (c["o3"] - y) / y.size  # (batch, 11) — divide by total elements (batch * n_classes)
        for i in range(3, -1, -1):
            a_prev = c["x"] if i == 0 else c[f"a{i-1}"]
            gW[i] = a_prev.T @ da
            gb[i] = da.sum(0)
            if i > 0:
                # 1. Propagar gradiente atraves de W[i] (antes de activacao)
                da = da @ self.W[i].T  # (batch, dims[i-1])
                # 2. ReLU grad — usar z[i-1] que e o output do BatchNorm
                da = da * relu_g(c[f"z{i-1}"])
                # 3. Dropout grad
                if f"m{i-1}" in c: da = da * c[f"m{i-1}"]
                # 4. BatchNorm grad
                gg[i-1] = (da * c[f"z{i-1}"]).sum(0)
                gbe[i-1] = da.sum(0)
                da = (da * self.g[i-1]) / np.sqrt(self.rv[i-1] + 1e-8)
        return gW, gb, gg, gbe

    def adam(self, gW, gb, gg, gbe, lr=LR):
        self.t += 1
        bc1 = 1 - self.b1**self.t; bc2 = 1 - self.b2**self.t
        for i in range(4):
            self.mW[i] = self.b1*self.mW[i]+(1-self.b1)*gW[i]
            self.vW[i] = self.b2*self.vW[i]+(1-self.b2)*(gW[i]**2)
            self.W[i] -= lr * (self.mW[i]/bc1) / (np.sqrt(self.vW[i]/bc2) + self.eps)
            self.mb[i] = self.b1*self.mb[i]+(1-self.b1)*gb[i]
            self.vb[i] = self.b2*self.vb[i]+(1-self.b2)*(gb[i]**2)
            self.b[i] -= lr * (self.mb[i]/bc1) / (np.sqrt(self.vb[i]/bc2) + self.eps)
        for i in range(3):
            self.mg[i] = self.b1*self.mg[i]+(1-self.b1)*gg[i]
            self.vg[i] = self.b2*self.vg[i]+(1-self.b2)*(gg[i]**2)
            self.g[i] -= lr * (self.mg[i]/bc1) / (np.sqrt(self.vg[i]/bc2) + self.eps)
            self.mbe[i] = self.b1*self.mbe[i]+(1-self.b1)*gbe[i]
            self.vbe[i] = self.b2*self.vbe[i]+(1-self.b2)*(gbe[i]**2)
            self.be[i] -= lr * (self.mbe[i]/bc1) / (np.sqrt(self.vbe[i]/bc2) + self.eps)

    def n_params(self):
        return sum(w.size+b.size for w,b in zip(self.W,self.b)) + sum(g.size+b.size for g,b in zip(self.g,self.be))

    def save(self, path):
        d = {}
        for i in range(4): d[f"W{i}"]=self.W[i]; d[f"b{i}"]=self.b[i]
        for i in range(3): d[f"g{i}"]=self.g[i]; d[f"be{i}"]=self.be[i]; d[f"rm{i}"]=self.rm[i]; d[f"rv{i}"]=self.rv[i]
        np.savez(path, **d)

    def load(self, path):
        d = np.load(path)
        for i in range(4): self.W[i]=d[f"W{i}"]; self.b[i]=d[f"b{i}"]
        for i in range(3): self.g[i]=d[f"g{i}"]; self.be[i]=d[f"be{i}"]; self.rm[i]=d[f"rm{i}"]; self.rv[i]=d[f"rv{i}"]


class MotorNeural:
    def __init__(self):
        self.vec = TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=(1,3), sublinear_tf=True, max_df=0.95, min_df=2)
        self.net = MilkNet()
        self.hist = {"loss":[], "acc":[], "ciclos":[], "total":0}
        self.ciclo = 0; self.fit = False
        self._load()

    def _load(self):
        pf = MODELS_DIR/"milk_neural.npz"; vf = MODELS_DIR/"milk_vec.pkl"; hf = MODELS_DIR/"milk_hist.json"
        if pf.exists():
            self.net.load(pf); print(f"  [Neural] Pesos carregados")
        else:
            print(f"  [Neural] Fresh — {self.net.n_params():,} params")
        if vf.exists():
            with open(vf,"rb") as f: self.vec = pickle.load(f); self.fit = True
            print(f"  [Neural] Vectorizer OK")
        if hf.exists():
            with open(hf,"r",encoding="utf-8") as f: self.hist = json.load(f)
            self.ciclo = self.hist.get("ciclos",[{}])[-1].get("ciclo",0) if self.hist.get("ciclos") else 0
            print(f"  [Neural] {self.ciclo} ciclos, {self.hist.get('total',0):,} docs")

    def _save(self):
        self.net.save(MODELS_DIR/"milk_neural.npz")
        with open(MODELS_DIR/"milk_vec.pkl","wb") as f: pickle.dump(self.vec, f)
        with open(MODELS_DIR/"milk_hist.json","w",encoding="utf-8") as f: json.dump(self.hist, f, ensure_ascii=False, indent=2)

    def _labels(self, t):
        tl = t.lower()
        return [1.0 if any(p.lower() in tl for p in EIXOS_P[e]) else 0.0 for e in EIXOS]

    def treinar(self, ciclo, amostra=None):
        print(f"  [Neural] Preparando dados...")
        docs = sorted(CORPUS.glob("*.json"))
        if amostra: docs = docs[:amostra]
        textos, labels = [], []
        for fp in docs:
            try:
                with open(fp,"r",encoding="utf-8") as f: r = json.load(f)
                t = (r.get("text","") or "")[:2000]
                if t.strip(): textos.append(t); labels.append(self._labels(t))
            except: continue
        n = len(textos)
        print(f"  [Neural] {n} docs para treino")
        if n < 10: return {"loss":0,"acc":0,"n":n,"params":self.net.n_params(),"ev":"","total":self.hist["total"]}

        if not self.fit:
            print(f"  [Neural] Fit TF-IDF...")
            self.vec.fit(textos); self.fit = True

        X = self.vec.transform(textos).toarray().astype(np.float32)
        Y = np.array(labels, dtype=np.float32)
        print(f"  [Neural] Features: {X.shape}")

        lf, af = 0, 0
        for ep in range(EPOCHS):
            idx = np.random.permutation(n)
            Xs, Ys = X[idx], Y[idx]
            el, nb, cor, tot = 0, 0, 0, 0
            for s in range(0, n, BATCH):
                e = min(s+BATCH, n)
                xb, yb = Xs[s:e], Ys[s:e]
                pred, c = self.net.forward(xb, train=True)
                el += bce(pred, yb); nb += 1
                gW, gb, gg, gbe = self.net.backward(c, yb)
                self.net.adam(gW, gb, gg, gbe)
                cor += ((pred>0.5).astype(np.float32)==yb).sum(); tot += yb.size
            lf = el/max(nb,1); af = cor/max(tot,1)*100
            print(f"  [Neural] Epoch {ep+1}/{EPOCHS}: loss={lf:.4f} acc={af:.1f}%")

        # Avaliacao final
        pe, _ = self.net.forward(X, train=False)
        fa = ((pe>0.5).astype(np.float32)==Y).sum()/Y.size*100

        self.ciclo = ciclo
        self.hist["total"] += n
        self.hist["loss"].append(round(lf,4))
        self.hist["acc"].append(round(fa,2))
        self.hist["ciclos"].append({"ciclo":ciclo,"loss":round(lf,4),"acc":round(fa,2),"n":n,"ts":datetime.datetime.now().isoformat()})
        self.hist["ciclos"] = self.hist["ciclos"][-100:]

        ev = ""
        if len(self.hist["loss"])>1:
            dl = round(self.hist["loss"][-1]-self.hist["loss"][-2],4)
            da = round(self.hist["acc"][-1]-self.hist["acc"][-2],2)
            ev = f"loss {'+' if dl>=0 else ''}{dl} acc {'+' if da>=0 else ''}{da}%"

        self._save()
        np_ = self.net.n_params()
        print(f"  [Neural] Gravado. Acc: {fa:.1f}%. {ev}. Params: {np_:,}")
        return {"loss":round(lf,4),"acc":round(fa,2),"n":n,"params":np_,"ev":ev,"total":self.hist["total"]}

    def prever(self, texto):
        f = self.vec.transform([texto[:2000]]).toarray().astype(np.float32)
        p, _ = self.net.forward(f, train=False)
        return {EIXOS[i]: round(float(p[0][i]),3) for i in range(N_OUT)}


def loop_treino(intervalo=120, max_ciclos=None, amostra=None):
    print("="*60)
    print("MILK IA — MODELO NEURAL (numpy + backpropagation real)")
    print("="*60)
    print(f"Autor: {AUTOR} (Eduardo Mauer)")
    print(f"Arq: {MAX_FEATURES} -> {H1} -> {H2} -> {H3} -> {N_OUT}")
    print(f"Epochs: {EPOCHS} | Batch: {BATCH} | LR: {LR} | Dropout: {DROPOUT}")
    print(f"Optimizer: Adam (b1=0.9 b2=0.999) | Loss: BCE")
    print(f"Corpus: {CORPUS} | Modelos: {MODELS_DIR}")
    print("="*60)
    motor = MotorNeural()
    print(f"Parametros: {motor.net.n_params():,}")
    print("="*60)
    ciclo = motor.ciclo + 1
    while True:
        print(f"\n{'='*60}\nCICLO NEURAL {ciclo} — {datetime.datetime.now().strftime('%H:%M:%S')}\n{'='*60}")
        try:
            t0 = datetime.datetime.now()
            r = motor.treinar(ciclo, amostra)
            d = (datetime.datetime.now()-t0).total_seconds()
            print(f"\n  Loss: {r['loss']} | Acc: {r['acc']}% | Docs: {r['n']}")
            print(f"  Params: {r['params']:,} | Ev: {r['ev'] or 'primeiro'}")
            print(f"  Total: {r['total']:,} | Dur: {d:.1f}s")
        except Exception as e:
            print(f"  ERRO: {e}")
        if max_ciclos and ciclo >= max_ciclos: break
        ciclo += 1
        print(f"\n  Proximo em {intervalo}s...")
        time.sleep(intervalo)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="MILK IA Modelo Neural")
    p.add_argument("--ciclos", type=int, default=None)
    p.add_argument("--intervalo", type=int, default=120)
    p.add_argument("--amostra", type=int, default=None)
    p.add_argument("--um-ciclo", action="store_true")
    a = p.parse_args()
    if a.um_ciclo:
        m = MotorNeural()
        print(f"Params: {m.net.n_params():,}")
        r = m.treinar(1, a.amostra)
        print(f"\nLoss: {r['loss']} | Acc: {r['acc']}% | Docs: {r['n']} | Params: {r['params']:,}")
        print(f"Total: {r['total']:,}")
        print("\nPrevisao teste:")
        pr = m.prever("A Moura Encantada e uma figura do folclore na freguesia de Lisboa")
        for e, s in pr.items(): print(f"  {e:20s}: {s}")
    else:
        loop_treino(a.intervalo, a.ciclos, a.amostra)
