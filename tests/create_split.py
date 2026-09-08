#!/usr/bin/env python3
"""MILK IA — Split persistente TRAIN/VAL/TEST com hashes.

Cria split deterministico por SHA-256 dos documentos, sem leakage.
Guarda hashes exactos em state/dataset_split.json.
"""
from __future__ import annotations
import sys, os, json, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "documents"
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

# Split: 80% train, 10% val, 10% test — deterministic by hash
TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
# TEST_RATIO = 0.10 (resto)

docs = sorted(f for f in os.listdir(CORPUS) if f.endswith(".json"))
total = len(docs)
print(f"Documentos: {total}")

train, val, test = [], [], []
for f in docs:
    h = int(f[:-5][:16], 16)  # usar primeiros 16 hex chars como int
    ratio = (h % 100) / 100.0
    if ratio < TRAIN_RATIO:
        train.append(f[:-5])
    elif ratio < TRAIN_RATIO + VAL_RATIO:
        val.append(f[:-5])
    else:
        test.append(f[:-5])

split = {
    "schema": "ia_milk.dataset_split.v1",
    "created_at": __import__("datetime").datetime.now().isoformat(),
    "total": total,
    "train_count": len(train),
    "val_count": len(val),
    "test_count": len(test),
    "ratios": {"train": TRAIN_RATIO, "val": VAL_RATIO, "test": 1 - TRAIN_RATIO - VAL_RATIO},
    "train_hashes": train,
    "val_hashes": val,
    "test_hashes": test,
}

out = STATE / "dataset_split.json"
out.write_text(json.dumps(split, ensure_ascii=False), encoding="utf-8")
print(f"TRAIN: {len(train)} | VAL: {len(val)} | TEST: {len(test)}")
print(f"Saved: {out}")

# Verificar sem overlap
overlap_tv = set(train) & set(val)
overlap_tt = set(train) & set(test)
overlap_vt = set(val) & set(test)
print(f"Overlap train-val: {len(overlap_tv)}")
print(f"Overlap train-test: {len(overlap_tt)}")
print(f"Overlap val-test: {len(overlap_vt)}")
assert not overlap_tv and not overlap_tt and not overlap_vt, "LEAKAGE DETECTED"
print("NO LEAKAGE: OK")
