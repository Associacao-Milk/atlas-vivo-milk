#!/usr/bin/env python3
"""MILK IA — Treino controlado com early stopping, best checkpoint, rollback.

Treina no split TRAIN, valida em VAL, compara com modelo canónico.
Promove apenas se superar baseline + modelo actual.
"""
from __future__ import annotations
import sys, os, json, pickle, shutil, tempfile
import numpy as np
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from milk_neural import MilkNet, MotorNeural, EIXOS, EIXOS_P, MAX_FEATURES, N_OUT, EPOCHS, BATCH, LR, DROPOUT, bce

CORPUS = ROOT / "corpus" / "documents"
MODELS = ROOT / "models"
STATE = ROOT / "state"

split = json.load(open(STATE / "dataset_split.json", "r", encoding="utf-8"))
train_hashes = split["train_hashes"]
val_hashes = split["val_hashes"]
print(f"TRAIN: {len(train_hashes)} | VAL: {len(val_hashes)}")

# Backup modelo actual
backup_dir = MODELS / "backup_pre_retrain"
backup_dir.mkdir(exist_ok=True)
for f in ["milk_neural.npz", "milk_vec.pkl", "milk_hist.json"]:
    src = MODELS / f
    if src.exists():
        shutil.copy2(src, backup_dir / f)
print(f"Backup: {backup_dir}")

# Load data
def load_data(hashes):
    textos, labels = [], []
    for h in hashes:
        p = CORPUS / f"{h}.json"
        try:
            r = json.load(open(p, "r", encoding="utf-8"))
            t = (r.get("text", "") or "")[:2000]
            if t.strip():
                textos.append(t)
                labels.append([1.0 if any(pp.lower() in t.lower() for pp in EIXOS_P[e]) else 0.0 for e in EIXOS])
        except:
            continue
    return textos, labels

print("Carregando TRAIN...")
tr_texts, tr_labels = load_data(train_hashes)
print(f"  {len(tr_texts)} docs")
print("Carregando VAL...")
va_texts, va_labels = load_data(val_hashes)
print(f"  {len(va_texts)} docs")

# Init motor
motor = MotorNeural()

# Vectorize
X_tr = motor.vec.transform(tr_texts).toarray().astype(np.float32)
Y_tr = np.array(tr_labels, dtype=np.float32)
X_va = motor.vec.transform(va_texts).toarray().astype(np.float32)
Y_va = np.array(va_labels, dtype=np.float32)
print(f"X_tr: {X_tr.shape}, X_va: {X_va.shape}")

# Evaluate current model on VAL (baseline)
pred_va, _ = motor.net.forward(X_va, train=False)
baseline_f1_macro = 0
for i in range(N_OUT):
    p_bin = (pred_va[:, i] > 0.5).astype(np.float32)
    tp = ((p_bin == 1) & (Y_va[:, i] == 1)).sum()
    fp = ((p_bin == 1) & (Y_va[:, i] == 0)).sum()
    fn = ((p_bin == 0) & (Y_va[:, i] == 1)).sum()
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    baseline_f1_macro += 2 * prec * rec / max(prec + rec, 1e-8)
baseline_f1_macro /= N_OUT
print(f"\nBaseline VAL F1 macro: {baseline_f1_macro:.4f}")

# Train with early stopping
best_f1 = baseline_f1_macro
best_epoch = -1
patience = 3
no_improve = 0
n = len(tr_texts)

for epoch in range(EPOCHS):
    idx = np.random.permutation(n)
    Xs, Ys = X_tr[idx], Y_tr[idx]
    el, nb = 0, 0
    for s in range(0, n, BATCH):
        e = min(s + BATCH, n)
        xb, yb = Xs[s:e], Ys[s:e]
        pred, cache = motor.net.forward(xb, train=True)
        el += bce(pred, yb); nb += 1
        gW, gb, gg, gbe = motor.net.backward(cache, yb)
        motor.net.adam(gW, gb, gg, gbe)
    train_loss = el / max(nb, 1)

    # Validate
    pred_va, _ = motor.net.forward(X_va, train=False)
    val_f1 = 0
    for i in range(N_OUT):
        p_bin = (pred_va[:, i] > 0.5).astype(np.float32)
        tp = ((p_bin == 1) & (Y_va[:, i] == 1)).sum()
        fp = ((p_bin == 1) & (Y_va[:, i] == 0)).sum()
        fn = ((p_bin == 0) & (Y_va[:, i] == 1)).sum()
        prec = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        val_f1 += 2 * prec * rec / max(prec + rec, 1e-8)
    val_f1 /= N_OUT
    print(f"  Epoch {epoch+1}/{EPOCHS}: train_loss={train_loss:.4f} val_f1={val_f1:.4f}")

    if val_f1 > best_f1:
        best_f1 = val_f1
        best_epoch = epoch
        no_improve = 0
        # Save best checkpoint
        motor.net.save(MODELS / "milk_neural_best.npz")
        with open(MODELS / "milk_vec_best.pkl", "wb") as f:
            pickle.dump(motor.vec, f)
        print(f"    → NEW BEST (saved)")
    else:
        no_improve += 1
        if no_improve >= patience:
            print(f"    → Early stopping at epoch {epoch+1}")
            break

print(f"\nBest VAL F1: {best_f1:.4f} at epoch {best_epoch+1}")
print(f"Baseline VAL F1: {baseline_f1_macro:.4f}")

# Promote if better
if best_f1 > baseline_f1_macro:
    print("PROMOTE: new model is better — replacing canonical")
    motor.net.load(MODELS / "milk_neural_best.npz")
    motor.ciclo = motor.ciclo + 1
    motor.hist["loss"].append(round(float(train_loss), 4))
    motor.hist["acc"].append(round(float(best_f1 * 100), 2))
    motor.hist["ciclos"].append({"ciclo": motor.ciclo, "loss": round(float(train_loss), 4), "acc": round(float(best_f1 * 100), 2), "n": n, "ts": datetime.now().isoformat()})
    motor._save()
    print("Canonical model updated.")
else:
    print("REJECT: new model did not beat baseline — keeping canonical")
    # Restore from backup
    for f in ["milk_neural.npz", "milk_vec.pkl", "milk_hist.json"]:
        shutil.copy2(backup_dir / f, MODELS / f)
    print("Canonical model restored from backup.")

# Cleanup
for f in ["milk_neural_best.npz", "milk_vec_best.pkl"]:
    p = MODELS / f
    if p.exists():
        p.unlink()

# Save training report
report = {
    "schema": "ia_milk.training_report.v1",
    "timestamp": datetime.now().isoformat(),
    "baseline_val_f1": round(baseline_f1_macro, 4),
    "best_val_f1": round(best_f1, 4),
    "best_epoch": best_epoch + 1 if best_epoch >= 0 else 0,
    "promoted": best_f1 > baseline_f1_macro,
    "epochs_run": epoch + 1,
    "train_size": n,
    "val_size": len(va_texts),
}
(STATE / "training_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nReport: {STATE / 'training_report.json'}")
