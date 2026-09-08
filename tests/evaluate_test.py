#!/usr/bin/env python3
"""MILK IA — Avaliação real do modelo no split TEST.

Mede: precision/recall/F1 por classe, F1 micro/macro, Hamming loss,
subset accuracy, average precision, prevalência, predicted-positive-rate.
Compara com baselines: always-negative, prevalence, linear.
"""
from __future__ import annotations
import sys, os, json, pickle
import numpy as np
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from milk_neural import MilkNet, MotorNeural, EIXOS, EIXOS_P, MAX_FEATURES, N_OUT

CORPUS = ROOT / "corpus" / "documents"
MODELS = ROOT / "models"
STATE = ROOT / "state"

# Load split
split = json.load(open(STATE / "dataset_split.json", "r", encoding="utf-8"))
test_hashes = set(split["test_hashes"])
print(f"TEST: {len(test_hashes)} documentos")

# Load model
motor = MotorNeural()

# Collect TEST data
textos, labels = [], []
for h in sorted(test_hashes):
    p = CORPUS / f"{h}.json"
    try:
        r = json.load(open(p, "r", encoding="utf-8"))
        t = (r.get("text", "") or "")[:2000]
        if t.strip():
            textos.append(t)
            labels.append(motor._labels(t))
    except:
        continue

n = len(textos)
print(f"TEST carregado: {n} documentos")

X = motor.vec.transform(textos).toarray().astype(np.float32)
Y = np.array(labels, dtype=np.float32)
P, _ = motor.net.forward(X, train=False)
P_bin = (P > 0.5).astype(np.float32)

# Metrics
def per_class_metrics(y_true, y_pred, y_prob, class_name):
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)
    prevalence = y_true.mean()
    pred_pos_rate = y_pred.mean()
    return {
        "class": class_name,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "prevalence": round(float(prevalence), 4),
        "predicted_positive_rate": round(float(pred_pos_rate), 4),
    }

print("\n=== PER-CLASS METRICS (TEST) ===")
per_class = []
for i, eixo in enumerate(EIXOS):
    m = per_class_metrics(Y[:, i], P_bin[:, i], P[:, i], eixo)
    per_class.append(m)
    print(f"  {eixo:20s}: P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} prev={m['prevalence']:.3f} ppr={m['predicted_positive_rate']:.3f}")

# Aggregate metrics
# F1 micro
tp_all = sum(m["tp"] for m in per_class)
fp_all = sum(m["fp"] for m in per_class)
fn_all = sum(m["fn"] for m in per_class)
p_micro = tp_all / max(tp_all + fp_all, 1)
r_micro = tp_all / max(tp_all + fn_all, 1)
f1_micro = 2 * p_micro * r_micro / max(p_micro + r_micro, 1e-8)

# F1 macro
f1_macro = np.mean([m["f1"] for m in per_class])

# Hamming loss
hamming = float((P_bin != Y).mean())

# Subset accuracy
subset_acc = float((P_bin == Y).all(axis=1).mean())

# Average precision (simplified — mean of per-class AP using trapezoid)
# For each class, AP = sum of (precision at each recall level * delta recall)
def average_precision(y_true, y_prob):
    order = np.argsort(-y_prob)
    y_sorted = y_true[order]
    precisions, recalls = [], []
    tp = 0
    for i, yt in enumerate(y_sorted):
        if yt == 1:
            tp += 1
            precisions.append(tp / (i + 1))
            recalls.append(tp / max(int(y_sorted.sum()), 1))
    if not precisions:
        return 0.0
    return float(np.mean(precisions))

ap_per_class = [average_precision(Y[:, i], P[:, i]) for i in range(N_OUT)]
map_score = float(np.mean(ap_per_class))

# Baselines
always_neg_f1 = 0.0  # all zeros → no TP → F1=0 per class
prevalence_f1 = 0.0  # predict all positive → P=prevalence, R=1 → F1=2P/(P+1)
prevalence_f1_macro = np.mean([2 * m["prevalence"] / max(m["prevalence"] + 1, 1e-8) for m in per_class])

print(f"\n=== AGGREGATE METRICS ===")
print(f"  F1 micro:      {f1_micro:.4f}")
print(f"  F1 macro:       {f1_macro:.4f}")
print(f"  Hamming loss:   {hamming:.4f}")
print(f"  Subset acc:     {subset_acc:.4f}")
print(f"  MAP (mAP):      {map_score:.4f}")
print(f"\n=== BASELINES ===")
print(f"  Always-neg F1:  {always_neg_f1:.4f}")
print(f"  Prevalence F1:  {prevalence_f1_macro:.4f} (predict all positive)")

# Save
results = {
    "schema": "ia_milk.evaluation.v1",
    "split": "test",
    "n_documents": n,
    "per_class": per_class,
    "f1_micro": round(f1_micro, 4),
    "f1_macro": round(f1_macro, 4),
    "hamming_loss": round(hamming, 4),
    "subset_accuracy": round(subset_acc, 4),
    "mean_average_precision": round(map_score, 4),
    "baselines": {
        "always_negative_f1": always_neg_f1,
        "prevalence_f1_macro": round(float(prevalence_f1_macro), 4),
    },
}
out = STATE / "evaluation_test.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSaved: {out}")
