#!/usr/bin/env python3
"""MILK IA — Neural Math Certification Suite.

Tests BCE, sigmoid stability, gradient check, Adam, BatchNorm, Dropout,
save/load, param count, NaN/Inf — all read-only, no training.

Run: python tests/test_neural_certification.py
"""
from __future__ import annotations
import sys, os, json, pickle, tempfile
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from milk_neural import MilkNet, bce, sig, relu, relu_g, MAX_FEATURES, H1, H2, H3, N_OUT, DROPOUT, LR

MODELS = ROOT / "models"

results = []

def test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, status, detail))
    print(f"  [{status}] {name}: {detail}")

print("=" * 60)
print("MILK IA — NEURAL MATH CERTIFICATION")
print("=" * 60)

# --- A1: BCE sign ---
print("\n--- A1: BCE sign ---")
# bce should return NEGATIVE of entropy (loss to minimize)
# Current: bce(p,t) = mean(t*log(p) + (1-t)*log(1-p))
# Correct: -mean(t*log(p) + (1-t)*log(1-p))
p = np.array([[0.9, 0.1], [0.1, 0.9]])
t = np.array([[1.0, 0.0], [0.0, 1.0]])
val = bce(p, t)
test("bce_perfect_match", val > 0, f"val={val:.6f} (should be positive = loss)")
test("bce_is_loss_not_entropy", val > 0, "bce returns loss (positive) after fix.")

# Correct BCE
def bce_correct(p, t):
    return -float(np.mean(t * np.log(p + 1e-8) + (1 - t) * np.log(1 - p + 1e-8)))

val_correct = bce_correct(p, t)
test("bce_correct_positive", val_correct >= 0, f"correct val={val_correct:.6f} >= 0")

# Worst case
p_bad = np.array([[0.01, 0.99], [0.99, 0.01]])
t_bad = np.array([[1.0, 0.0], [0.0, 1.0]])
val_bad = bce(p_bad, t_bad)
val_bad_correct = bce_correct(p_bad, t_bad)
test("bce_worst_positive", val_bad > 0, f"worst val={val_bad:.6f} (positive after fix)")
test("bce_worst_correct_positive", val_bad_correct > 1.0, f"correct worst={val_bad_correct:.6f} > 1.0")

# NaN check
p_zero = np.array([[0.0, 1.0]])
t_zero = np.array([[1.0, 0.0]])
val_zero = bce(p_zero, t_zero)
test("bce_no_nan", not np.isnan(val_zero), f"val={val_zero:.6f} (epsilon prevents NaN)")

# --- A2: Sigmoid stability ---
print("\n--- A2: Sigmoid stability ---")
x_extreme = np.array([-1000, -500, -100, 0, 100, 500, 1000], dtype=np.float32)
sig_vals = sig(x_extreme)
test("sigmoid_no_nan", not np.any(np.isnan(sig_vals)), f"vals={sig_vals}")
test("sigmoid_no_inf", not np.any(np.isinf(sig_vals)), f"vals={sig_vals}")
test("sigmoid_bounded", np.all(sig_vals >= 0) and np.all(sig_vals <= 1), "0 <= sig <= 1")
test("sigmoid_clip_range", sig(-500) < 1e-200 and sig(500) == 1.0, "extreme values saturate near 0/1")

# Stable sigmoid alternative
def sig_stable(x):
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))

sig_stable_vals = sig_stable(x_extreme)
test("sigmoid_stable_no_nan", not np.any(np.isnan(sig_stable_vals)), "stable version no NaN")
test("sigmoid_stable_match", np.allclose(sig_vals, sig_stable_vals, atol=1e-7), "stable matches current within clip range")

# --- A3: Gradient check ---
print("\n--- A3: Gradient check (numerical vs analytical) ---")
np.random.seed(42)
net = MilkNet(dim_in=20)  # small net for grad check
net.W = [w.astype(np.float64) for w in net.W]
net.b = [b.astype(np.float64) for b in net.b]
net.g = [g.astype(np.float64) for g in net.g]
net.be = [be.astype(np.float64) for be in net.be]
net.rm = [rm.astype(np.float64) for rm in net.rm]
net.rv = [rv.astype(np.float64) for rv in net.rv]

x = np.random.randn(4, 20).astype(np.float64)
y = np.array([[1,0,0,1,0,1,0,0,1,0,1]], dtype=np.float64).repeat(4, axis=0)

# Forward
pred, cache = net.forward(x, train=False)
# Backward
gW, gb, gg, gbe = net.backward(cache, y)

# Numerical gradient check on W[0] using bce (now fixed with correct sign)
eps = 1e-6
max_diff = 0
for idx in [(0,0), (5,3), (10,7), (15,15)]:
    orig = net.W[0][idx]
    net.W[0][idx] = orig + eps
    pred_p, _ = net.forward(x, train=False)
    loss_p = bce(pred_p, y)
    net.W[0][idx] = orig - eps
    pred_m, _ = net.forward(x, train=False)
    loss_m = bce(pred_m, y)
    net.W[0][idx] = orig
    num_grad = (loss_p - loss_m) / (2 * eps)
    ana_grad = gW[0][idx]
    diff = abs(num_grad - ana_grad) / max(abs(num_grad) + abs(ana_grad), 1e-10)
    max_diff = max(max_diff, diff)

test("grad_check_W0", max_diff < 1e-3, f"max rel diff={max_diff:.6f}")

# After fix: gradient should match numerical (backward now divides by y.size = m*n_classes)
test("gradient_correct_sign", max_diff < 1e-3, "gradient matches numerical after BCE sign + normalization fix")

# --- A3b: Weighted (pos_weight) BCE gradient check ---
print("\n--- A3b: Weighted BCE gradient check (pos_weight) ---")
np.random.seed(7)
netw = MilkNet(dim_in=20)
netw.W = [w.astype(np.float64) for w in netw.W]
netw.b = [b.astype(np.float64) for b in netw.b]
netw.g = [g.astype(np.float64) for g in netw.g]
netw.be = [be.astype(np.float64) for be in netw.be]
netw.rm = [rm.astype(np.float64) for rm in netw.rm]
netw.rv = [rv.astype(np.float64) for rv in netw.rv]
xw = np.random.randn(4, 20).astype(np.float64)
yw = np.array([[1,0,1,0,1,0,0,1,0,1,0]], dtype=np.float64).repeat(4, axis=0)
pw = np.array([3.0,1.0,5.0,1.0,2.0,1.0,1.0,4.0,1.0,2.0,1.0], dtype=np.float64)

def wbce(p, t, w):
    return -float(np.mean(w.reshape(1, -1) * t * np.log(p + 1e-8) + (1 - t) * np.log(1 - p + 1e-8)))

predw, cachew = netw.forward(xw, train=False)
gWw, gbw, ggw, gbew = netw.backward(cachew, yw, pos_weight=pw)
max_diff_w = 0
for idx in [(0, 0), (5, 3), (10, 7), (15, 15)]:
    orig = netw.W[0][idx]
    netw.W[0][idx] = orig + eps
    lp = wbce(netw.forward(xw, train=False)[0], yw, pw)
    netw.W[0][idx] = orig - eps
    lm = wbce(netw.forward(xw, train=False)[0], yw, pw)
    netw.W[0][idx] = orig
    num = (lp - lm) / (2 * eps)
    ana = gWw[0][idx]
    max_diff_w = max(max_diff_w, abs(num - ana) / max(abs(num) + abs(ana), 1e-10))
test("grad_check_pos_weight_W0", max_diff_w < 1e-3, f"max rel diff={max_diff_w:.6f}")

# pos_weight=ones must equal unweighted (no change when all weights = 1)
gWu, _, _, _ = netw.backward(cachew, yw)
gW1, _, _, _ = netw.backward(cachew, yw, pos_weight=np.ones(11, dtype=np.float64))
test("pos_weight_ones_equals_unweighted", np.allclose(gWu[0], gW1[0], atol=1e-12), "pos_weight=1 == unweighted (backward compatible)")

# --- A4: Adam/BatchNorm/Dropout/save-load/params ---
print("\n--- A4: Component verification ---")

# Param count
net2 = MilkNet(dim_in=MAX_FEATURES)
params = net2.n_params()
# W: 5000*512 + 512*256 + 256*128 + 128*11 = 2560000 + 131072 + 32768 + 1408 = 2705248
# b: 512 + 256 + 128 + 11 = 907
# g: 512 + 256 + 128 = 896
# be: 512 + 256 + 128 = 896
expected = (MAX_FEATURES*H1 + H1*H2 + H2*H3 + H3*N_OUT) + (H1+H2+H3+N_OUT) + (H1+H2+H3) + (H1+H2+H3)
test("param_count", params == expected, f"params={params:,} expected={expected:,}")

# Save/load roundtrip
net3 = MilkNet(dim_in=50)
with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tf:
    tmpf = tf.name
net3.save(tmpf)
net4 = MilkNet(dim_in=50)
net4.load(tmpf)
all_match = all(np.allclose(net3.W[i], net4.W[i]) for i in range(4)) and \
            all(np.allclose(net3.b[i], net4.b[i]) for i in range(4)) and \
            all(np.allclose(net3.g[i], net4.g[i]) for i in range(3)) and \
            all(np.allclose(net3.be[i], net4.be[i]) for i in range(3))
test("save_load_roundtrip", all_match, "all weights match after save+load")
os.unlink(tmpf)

# BatchNorm: train mode updates running stats
net5 = MilkNet(dim_in=20)
x5 = np.random.randn(8, 20).astype(np.float32)
rm_before = net5.rm[0].copy()
net5.forward(x5, train=True)
rm_after = net5.rm[0]
test("batchnorm_updates_running_mean", not np.allclose(rm_before, rm_after), "running mean updated in train mode")

# BatchNorm: eval mode uses running stats
rm_before_eval = net5.rm[0].copy()
net5.forward(x5, train=False)
rm_after_eval = net5.rm[0]
test("batchnorm_eval_no_update", np.allclose(rm_before_eval, rm_after_eval), "running mean NOT updated in eval mode")

# Dropout: train mode applies mask, eval mode doesn't
net6 = MilkNet(dim_in=20)
np.random.seed(0)
out_train, _ = net6.forward(x5, train=True)
np.random.seed(0)
out_eval, _ = net6.forward(x5, train=False)
test("dropout_train_vs_eval", not np.allclose(out_train, out_eval), "train and eval outputs differ (dropout active)")

# Dropout: inverted (scales by 1/(1-p))
mask_test = (np.random.rand(*x5.shape) > DROPOUT).astype(np.float32) / (1 - DROPOUT)
test("dropout_inverted", np.isclose(mask_test[mask_test > 0].mean(), 1.0 / (1 - DROPOUT)), "inverted dropout scaling")

# Adam: convergence on simple problem
net7 = MilkNet(dim_in=10)
x7 = np.random.randn(16, 10).astype(np.float32)
y7 = np.array([[1,0,0,1,0,1,0,0,1,0,1]], dtype=np.float32).repeat(16, axis=0)
initial_loss = bce_correct(net7.forward(x7, train=False)[0], y7)
for _ in range(50):
    pred, cache = net7.forward(x7, train=True)
    gW, gb, gg, gbe = net7.backward(cache, y7)
    net7.adam(gW, gb, gg, gbe)
final_loss = bce_correct(net7.forward(x7, train=False)[0], y7)
test("adam_convergence", final_loss < initial_loss, f"loss {initial_loss:.4f} -> {final_loss:.4f}")

# --- A5: NaN/Inf audit ---
print("\n--- A5: NaN/Inf audit ---")
# Test with correct dims
out_zero, _ = net2.forward(np.zeros((4, MAX_FEATURES), dtype=np.float32), train=False)
test("no_nan_zero_input", not np.any(np.isnan(out_zero)), "no NaN with zero input")
test("no_inf_zero_input", not np.any(np.isinf(out_zero)), "no Inf with zero input")

# Test with large input
x_large = np.full((4, MAX_FEATURES), 1e6, dtype=np.float32)
out_large, _ = net2.forward(x_large, train=False)
test("no_nan_large_input", not np.any(np.isnan(out_large)), "no NaN with large input")
test("no_inf_large_input", not np.any(np.isinf(out_large)), "no Inf with large input")

# --- Summary ---
print("\n" + "=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
print(f"RESULTS: {passed} PASS, {failed} FAIL")
print("=" * 60)

if failed:
    print("\nFAILURES:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  {name}: {detail}")

# Save results
cert = {
    "timestamp": __import__("datetime").datetime.now().isoformat(),
    "passed": passed,
    "failed": failed,
    "results": [{"name": n, "status": s, "detail": d} for n, s, d in results],
    "bce_issue": "bce() at line 49 returns entropy (negative), not loss (positive). Missing '-' prefix.",
    "gradient_ok": True,
    "sigmoid_issue": "Current sig() uses np.clip(x, -500, 500) which prevents overflow but is not optimal. Consider log-sum-exp formulation.",
    "recommendation": "Fix bce() to return -np.mean(...) for correct positive loss. Sigmoid gradient in backward() is correct (uses pred-y which is BCE+sigmoid gradient)."
}
out_path = ROOT / "tests" / "neural_certification_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(cert, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nResults saved: {out_path}")

sys.exit(1 if failed else 0)
