#!/usr/bin/env python3
"""MILK IA — Treino PyTorch controlado com monitorização ao vivo.

Carga corpus/splits/vectorizer/modelo promovido, treino em PyTorch,
AMP quando CUDA, early stopping, grad clip, threshold tuning por classe,
checkpoints por epoch com SHA, TensorBoard, eventos ao vivo para /milk-live.
"""
from __future__ import annotations
import sys, os, json, pickle, hashlib, time, shutil, signal, threading, psutil
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
MODELS = ROOT / "models"
STATE = ROOT / "state"
CORPUS = ROOT / "corpus" / "documents"

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
N_OUT = 11; MAX_FEATURES = 5000; H1, H2, H3 = 512, 256, 128

SEED = 2026
MAX_EPOCHS = 20
BATCH = 128
LR = 1e-3
DROPOUT = 0.3
PATIENCE = 5
GRAD_CLIP = 5.0
THR_GRID = np.arange(0.05, 0.96, 0.05, dtype=np.float32)

LIVE_FILE = STATE / "training_live.json"
TB_DIR = STATE / "tensorboard"
CKPT_DIR = MODELS / "checkpoints_torch"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1<<20), b""): h.update(c)
    return h.hexdigest()

# ---------- model ----------
class MilkTorchNet(nn.Module):
    def __init__(self, dim_in=MAX_FEATURES):
        super().__init__()
        self.fc0 = nn.Linear(dim_in, H1)
        self.bn0 = nn.BatchNorm1d(H1)
        self.fc1 = nn.Linear(H1, H2)
        self.bn1 = nn.BatchNorm1d(H2)
        self.fc2 = nn.Linear(H2, H3)
        self.bn2 = nn.BatchNorm1d(H3)
        self.fc3 = nn.Linear(H3, N_OUT)
        self.drop = nn.Dropout(DROPOUT)

    def forward(self, x):
        x = self.drop(torch.relu(self.bn0(self.fc0(x))))
        x = self.drop(torch.relu(self.bn1(self.fc1(x))))
        x = self.drop(torch.relu(self.bn2(self.fc2(x))))
        return torch.sigmoid(self.fc3(x))

def load_weights_from_npz(net, npz_path):
    d = np.load(npz_path)
    with torch.no_grad():
        net.fc0.weight.copy_(torch.from_numpy(d["W0"].T))
        net.fc0.bias.copy_(torch.from_numpy(d["b0"]))
        net.bn0.weight.copy_(torch.from_numpy(d["g0"]))
        net.bn0.bias.copy_(torch.from_numpy(d["be0"]))
        net.bn0.running_mean.copy_(torch.from_numpy(d["rm0"]))
        net.bn0.running_var.copy_(torch.from_numpy(d["rv0"]))
        net.fc1.weight.copy_(torch.from_numpy(d["W1"].T))
        net.fc1.bias.copy_(torch.from_numpy(d["b1"]))
        net.bn1.weight.copy_(torch.from_numpy(d["g1"]))
        net.bn1.bias.copy_(torch.from_numpy(d["be1"]))
        net.bn1.running_mean.copy_(torch.from_numpy(d["rm1"]))
        net.bn1.running_var.copy_(torch.from_numpy(d["rv1"]))
        net.fc2.weight.copy_(torch.from_numpy(d["W2"].T))
        net.fc2.bias.copy_(torch.from_numpy(d["b2"]))
        net.bn2.weight.copy_(torch.from_numpy(d["g2"]))
        net.bn2.bias.copy_(torch.from_numpy(d["be2"]))
        net.bn2.running_mean.copy_(torch.from_numpy(d["rm2"]))
        net.bn2.running_var.copy_(torch.from_numpy(d["rv2"]))
        net.fc3.weight.copy_(torch.from_numpy(d["W3"].T))
        net.fc3.bias.copy_(torch.from_numpy(d["b3"]))
    return net

def save_torch_npz(net, path):
    """Save in the same npz format as the numpy model for backward compat."""
    with torch.no_grad():
        d = {}
        for i, (fc, bn) in enumerate([(net.fc0,net.bn0),(net.fc1,net.bn1),(net.fc2,net.bn2)]):
            d[f"W{i}"] = fc.weight.cpu().numpy().T
            d[f"b{i}"] = fc.bias.cpu().numpy()
            d[f"g{i}"] = bn.weight.cpu().numpy()
            d[f"be{i}"] = bn.bias.cpu().numpy()
            d[f"rm{i}"] = bn.running_mean.cpu().numpy()
            d[f"rv{i}"] = bn.running_var.cpu().numpy()
        d["W3"] = net.fc3.weight.cpu().numpy().T
        d["b3"] = net.fc3.bias.cpu().numpy()
    np.savez(path, **d)

# ---------- data ----------
def load_docs(hashes):
    textos, labels = [], []
    for h in hashes:
        p = CORPUS / f"{h}.json"
        try:
            r = json.load(open(p, "r", encoding="utf-8"))
            t = (r.get("text", "") or "")[:2000]
            if t.strip():
                textos.append(t)
                labels.append([1.0 if any(pp.lower() in t.lower() for pp in EIXOS_P[e]) else 0.0 for e in EIXOS])
        except Exception:
            continue
    return textos, np.array(labels, dtype=np.float32)

def per_class_metrics(Y, Pbin, Pprob):
    out = []
    for i in range(N_OUT):
        yt, yp = Y[:, i], Pbin[:, i]
        tp = int(((yp==1)&(yt==1)).sum()); fp = int(((yp==1)&(yt==0)).sum())
        fn = int(((yp==0)&(yt==1)).sum()); tn = int(((yp==0)&(yt==0)).sum())
        prec = tp/max(tp+fp,1); rec = tp/max(tp+fn,1)
        f1 = 2*prec*rec/max(prec+rec,1e-8)
        out.append({"class": EIXOS[i], "precision": round(prec,4), "recall": round(rec,4),
                     "f1": round(f1,4), "tp": tp, "fp": fp, "fn": fn, "tn": tn})
    return out

def aggregate(pc):
    tp_all = sum(m["tp"] for m in pc); fp_all = sum(m["fp"] for m in pc)
    fn_all = sum(m["fn"] for m in pc)
    pm = tp_all/max(tp_all+fp_all,1); rm = tp_all/max(tp_all+fn_all,1)
    f1m = 2*pm*rm/max(pm+rm,1e-8)
    f1M = float(np.mean([m["f1"] for m in pc]))
    det = int(sum(1 for m in pc if m["f1"]>0))
    return {"f1_micro": round(f1m,4), "f1_macro": round(f1M,4), "classes_detected": det}

def hamming(Y, Pbin):
    return round(float((Pbin != Y).mean()), 4)

def optimize_thresholds(Y, P):
    thr = np.full(N_OUT, 0.5, dtype=np.float32)
    for i in range(N_OUT):
        yt = Y[:, i]; pr = P[:, i]
        if yt.sum() == 0: continue
        best_f1, best_t = -1, 0.5
        for t in THR_GRID:
            yp = (pr > t).astype(np.float32)
            tp = int(((yp==1)&(yt==1)).sum()); fp = int(((yp==1)&(yt==0)).sum()); fn = int(((yp==0)&(yt==1)).sum())
            prec = tp/max(tp+fp,1); rec = tp/max(tp+fn,1)
            f1 = 2*prec*rec/max(prec+rec,1e-8)
            if f1 > best_f1: best_f1, best_t = f1, float(t)
        thr[i] = best_t
    return thr

# ---------- live status writer ----------
_live_lock = threading.Lock()

def write_live(status: dict):
    with _live_lock:
        status["heartbeat"] = now_iso()
        status["pid"] = os.getpid()
        tmp = LIVE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(LIVE_FILE)

# ---------- TensorBoard (lightweight, no TB dependency) ----------
def tb_log(epoch, metrics: dict):
    """Write a simple JSON-lines metrics log (TensorBoard-compatible via torch.utils.tensorboard if available)."""
    log_path = TB_DIR / "metrics.jsonl"
    log_path.parent.mkdir(exist_ok=True)
    entry = {"epoch": epoch, "ts": now_iso(), **metrics}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Also try real TensorBoard
    try:
        from torch.utils.tensorboard import SummaryWriter
        writer = SummaryWriter(str(TB_DIR))
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                writer.add_scalar(f"train/{k}", v, epoch)
        writer.close()
    except Exception:
        pass

# ---------- main ----------
def main():
    t_start = time.time()
    torch.manual_seed(SEED); np.random.seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cuda = torch.cuda.is_available()
    print(f"DEVICE: {device} | CUDA: {cuda} | torch: {torch.__version__}")

    # hardware info
    hw = {"device": str(device), "cuda": cuda, "torch_version": torch.__version__,
          "gpu_name": torch.cuda.get_device_name(0) if cuda else "CPU",
          "vram_total_gb": round(torch.cuda.get_device_properties(0).total_memory/1e9,2) if cuda else 0,
          "cpu_count": os.cpu_count(), "ram_gb": round(psutil.virtual_memory().total/1e9,2)}

    # load split + vectorizer + baseline model
    split = json.load(open(STATE / "dataset_split.json", "r", encoding="utf-8"))
    tr_h, va_h, te_h = split["train_hashes"], split["val_hashes"], split["test_hashes"]
    vec = pickle.load(open(MODELS / "milk_vec.pkl", "rb"))
    base_sha = sha256_file(MODELS / "milk_neural.npz")
    print(f"BASE MODEL SHA: {base_sha[:16]}...")

    # backup baseline
    backup = MODELS / "backup_torch_baseline"
    backup.mkdir(exist_ok=True)
    if not (backup / "milk_neural.npz").exists():
        shutil.copy2(MODELS / "milk_neural.npz", backup / "milk_neural.npz")
        shutil.copy2(MODELS / "milk_vec.pkl", backup / "milk_vec.pkl")
        print(f"BACKUP baseline -> {backup}")

    CKPT_DIR.mkdir(exist_ok=True)

    print("loading TRAIN+VAL docs...")
    tr_texts, Y_tr = load_docs(tr_h)
    va_texts, Y_va = load_docs(va_h)
    print(f"  train={len(tr_texts)} val={len(va_texts)}")

    X_tr = vec.transform(tr_texts).toarray().astype(np.float32)
    X_va = vec.transform(va_texts).toarray().astype(np.float32)
    print(f"  X_tr={X_tr.shape} X_va={X_va.shape}")

    # to tensors
    X_tr_t = torch.from_numpy(X_tr); Y_tr_t = torch.from_numpy(Y_tr)
    X_va_t = torch.from_numpy(X_va); Y_va_t = torch.from_numpy(Y_va)

    ds_tr = TensorDataset(X_tr_t, Y_tr_t)
    dl_tr = DataLoader(ds_tr, batch_size=BATCH, shuffle=True,
                      pin_memory=cuda, num_workers=0, drop_last=False)

    # model
    net = MilkTorchNet().to(device)
    net = load_weights_from_npz(net, MODELS / "milk_neural.npz")
    net.train()
    optimizer = torch.optim.Adam(net.parameters(), lr=LR)
    criterion = nn.BCELoss()
    scaler = torch.amp.GradScaler("cuda") if cuda else None

    # baseline VAL metrics (threshold-tuned)
    net.eval()
    with torch.no_grad():
        P_va_base = net(X_va_t.to(device)).cpu().numpy()
    thr_base = optimize_thresholds(Y_va, P_va_base)
    Pbin_base = (P_va_base > thr_base.reshape(1,-1)).astype(np.float32)
    base_val = aggregate(per_class_metrics(Y_va, Pbin_base, P_va_base))
    print(f"BASELINE VAL: f1_macro={base_val['f1_macro']} f1_micro={base_val['f1_micro']} det={base_val['classes_detected']}")

    best_val_f1 = base_val["f1_macro"]
    best_epoch = -1; no_improve = 0
    best_state = None; best_thr = None

    live = {
        "schema": "ia_milk.training_live.v1",
        "host": os.environ.get("COMPUTERNAME", "localhost"),
        "pid": os.getpid(),
        "device": str(device), "cuda": cuda,
        "gpu": hw["gpu_name"], "vram_total_gb": hw["vram_total_gb"],
        "base_model_sha": base_sha,
        "training_model_sha": None,
        "epoch": 0, "total_epochs": MAX_EPOCHS,
        "train_loss": None, "val_loss": None,
        "val_f1_macro": base_val["f1_macro"], "val_f1_micro": base_val["f1_micro"],
        "val_classes_detected": base_val["classes_detected"],
        "per_class": per_class_metrics(Y_va, Pbin_base, P_va_base),
        "docs_processed": 0, "batches_processed": 0,
        "checkpoint_sha": None,
        "status": "TRAINING",
        "started_at": now_iso(),
        "elapsed_s": 0,
        "seed": SEED, "batch_size": BATCH, "lr": LR,
        "hardware": hw,
    }
    write_live(live)

    n_batches_per_epoch = (len(dl_tr) + BATCH - 1) // BATCH
    docs_done = 0; batches_done = 0

    for epoch in range(MAX_EPOCHS):
        net.train()
        epoch_loss = 0.0; nb = 0
        t_ep = time.time()
        for xb, yb in dl_tr:
            xb, yb = xb.to(device, non_blocking=cuda), yb.to(device, non_blocking=cuda)
            optimizer.zero_grad()
            if cuda and scaler:
                with torch.amp.autocast("cuda"):
                    pred = net(xb); loss = criterion(pred, yb)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP)
                scaler.step(optimizer); scaler.update()
            else:
                pred = net(xb); loss = criterion(pred, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP)
                optimizer.step()
            epoch_loss += float(loss); nb += 1; batches_done += 1; docs_done += xb.shape[0]

            # periodic live update within epoch
            if batches_done % 20 == 0:
                live.update({"docs_processed": docs_done, "batches_processed": batches_done,
                              "epoch": epoch+1, "elapsed_s": round(time.time()-t_start,1),
                              "vram_used_gb": round(torch.cuda.memory_allocated()/1e9,2) if cuda else 0,
                              "cpu_pct": psutil.cpu_percent(),
                              "ram_pct": psutil.virtual_memory().percent})
                write_live(live)

        train_loss = epoch_loss / max(nb, 1)

        # validation
        net.eval()
        with torch.no_grad():
            P_va = net(X_va_t.to(device)).cpu().numpy()
        val_loss = float(criterion(torch.from_numpy(P_va), Y_va_t))
        thr = optimize_thresholds(Y_va, P_va)
        Pbin = (P_va > thr.reshape(1,-1)).astype(np.float32)
        pc = per_class_metrics(Y_va, Pbin, P_va)
        agg = aggregate(pc)
        val_f1 = agg["f1_macro"]
        ham = hamming(Y_va, Pbin)

        # per-class F1 dict
        pc_f1 = {m["class"]: m["f1"] for m in pc}

        # checkpoint
        ckpt_path = CKPT_DIR / f"epoch_{epoch+1:03d}.npz"
        save_torch_npz(net, ckpt_path)
        ckpt_sha = sha256_file(ckpt_path)

        ep_dt = time.time() - t_ep
        elapsed = time.time() - t_start

        # TensorBoard + metrics
        tb_metrics = {"train_loss": train_loss, "val_loss": val_loss,
                       "val_f1_macro": val_f1, "val_f1_micro": agg["f1_micro"],
                       "val_hamming": ham, "val_classes_detected": agg["classes_detected"],
                       "lr": LR, "epoch_time_s": ep_dt, **{f"f1_{k}": v for k,v in pc_f1.items()}}
        tb_log(epoch+1, tb_metrics)

        print(f"  EPOCH {epoch+1:2d}/{MAX_EPOCHS}: train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
              f"val_f1={val_f1:.4f} micro={agg['f1_micro']:.4f} det={agg['classes_detected']} "
              f"hamming={ham} ckpt={ckpt_sha[:12]} {ep_dt:.1f}s")

        # update live status
        live.update({
            "epoch": epoch+1, "train_loss": round(train_loss,4), "val_loss": round(val_loss,4),
            "val_f1_macro": round(val_f1,4), "val_f1_micro": agg["f1_micro"],
            "val_classes_detected": agg["classes_detected"], "val_hamming": ham,
            "per_class": pc, "docs_processed": docs_done, "batches_processed": batches_done,
            "checkpoint_sha": ckpt_sha, "checkpoint_path": str(ckpt_path),
            "elapsed_s": round(elapsed,1),
            "vram_used_gb": round(torch.cuda.memory_allocated()/1e9,2) if cuda else 0,
            "cpu_pct": psutil.cpu_percent(), "ram_pct": psutil.virtual_memory().percent,
        })
        write_live(live)

        # early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1; best_epoch = epoch+1; no_improve = 0
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
            best_thr = thr.copy()
            live["training_model_sha"] = ckpt_sha
            live["best_epoch"] = best_epoch
            write_live(live)
            print(f"    -> NEW BEST (val_f1={val_f1:.4f})")
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                print(f"  EARLY STOP at epoch {epoch+1} (patience {PATIENCE})")
                break

    # ---- promotion gate ----
    print(f"\n=== TRAINING COMPLETE ===")
    print(f"  BASELINE val_f1_macro: {base_val['f1_macro']}")
    print(f"  BEST val_f1_macro: {best_val_f1} (epoch {best_epoch})")

    promote = best_val_f1 > base_val["f1_macro"]
    if promote and best_state is not None:
        # reload best state
        net.load_state_dict(best_state)
        cand_path = MODELS / "milk_neural_candidate_torch.npz"
        save_torch_npz(net, cand_path)
        cand_sha = sha256_file(cand_path)

        # one-shot TEST eval
        te_texts, Y_te = load_docs(te_h)
        X_te = vec.transform(te_texts).toarray().astype(np.float32)
        X_te_t = torch.from_numpy(X_te)
        net.eval()
        with torch.no_grad():
            P_te = net(X_te_t.to(device)).cpu().numpy()
        Pbin_te = (P_te > best_thr.reshape(1,-1)).astype(np.float32)
        pc_te = per_class_metrics(Y_te, Pbin_te, P_te)
        test_agg = aggregate(pc_te)
        test_ham = hamming(Y_te, Pbin_te)

        REF = {"f1_macro": 0.5566, "f1_micro": 0.6397, "hamming": 0.0513, "classes": 11}
        FUNC = {"cultural", "economica", "tecnologica"}
        g_macro = test_agg["f1_macro"] > REF["f1_macro"]
        g_micro = test_agg["f1_micro"] >= REF["f1_micro"] - 0.03
        g_func = all(m["f1"] > 0.10 for m in pc_te if m["class"] in FUNC)
        g_classes = test_agg["classes_detected"] >= REF["classes"]
        promote = g_macro and g_micro and g_func and g_classes

        print(f"  TEST: f1_macro={test_agg['f1_macro']} f1_micro={test_agg['f1_micro']} det={test_agg['classes_detected']} hamming={test_ham}")
        print(f"  GATE: macro={g_macro} micro={g_micro} func={g_func} classes={g_classes} => {'PROMOTE' if promote else 'REJECT'}")

        if promote:
            prev_sha = sha256_file(MODELS / "milk_neural.npz")
            shutil.copy2(cand_path, MODELS / "milk_neural.npz")
            new_sha = sha256_file(MODELS / "milk_neural.npz")
            # save thresholds
            json.dump({e: round(float(best_thr[i]),2) for i,e in enumerate(EIXOS)},
                      open(MODELS / "milk_thresholds.json", "w", encoding="utf-8"), ensure_ascii=True, indent=2)
            print(f"  PROMOTED: {prev_sha[:12]} -> {new_sha[:12]}")
        else:
            print(f"  REJECTED — canonical model preserved")

        live.update({"status": "DONE_PROMOTED" if promote else "DONE_REJECTED",
                      "test_f1_macro": test_agg["f1_macro"], "test_f1_micro": test_agg["f1_micro"],
                      "test_classes_detected": test_agg["classes_detected"],
                      "test_hamming": test_ham,
                      "final_val_f1_macro": round(best_val_f1,4), "best_epoch": best_epoch,
                      "promoted": promote})
    else:
        live.update({"status": "DONE_NO_IMPROVEMENT", "final_val_f1_macro": round(best_val_f1,4),
                      "best_epoch": best_epoch, "promoted": False})
        print("  NO IMPROVEMENT — canonical model preserved")

    write_live(live)
    elapsed_total = time.time() - t_start
    print(f"\n  ELAPSED: {elapsed_total:.1f}s")
    print(f"  LIVE STATUS: {LIVE_FILE}")

if __name__ == "__main__":
    main()
