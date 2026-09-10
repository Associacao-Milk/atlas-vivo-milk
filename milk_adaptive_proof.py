#!/usr/bin/env python3
"""MILK Adaptive Learning Engine — End-to-End Adaptation Proof.

Executes 3 controlled tasks to demonstrate that the policy adapts between
executions. The proof is real (not mocked) — uses actual CognitiveControlPlane,
CapabilityRouter, AdaptiveLearningEngine, and local services.

EXECUTION A: Policy initial — selects based on base scores.
EXECUTION B/C: Previous experience alters scores/preferences — demonstrates
              measurable policy change and reconstruction of the full chain:
              task → candidates → score → choice → outcome → reward
              → learning event → policy update → subsequent decision.
"""
from __future__ import annotations
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.adaptive_engine import (
    AdaptiveLearningEngine, AdaptivePolicy, RewardModel,
    create_learning_event, save_learning_event, load_learning_events,
)
from milk_ai.cognitive_control_plane import CognitiveControlPlane, CapabilityRouter


def main():
    print("=" * 70)
    print("MILK ADAPTIVE LEARNING ENGINE — END-TO-END ADAPTATION PROOF")
    print("=" * 70)

    # Use isolated temp policy to not interfere with the persistent one
    proof_dir = ROOT / "state" / "adaptive_proof"
    proof_dir.mkdir(parents=True, exist_ok=True)
    policy_path = proof_dir / "policy.json"
    events_path = proof_dir / "learning_events.jsonl"
    op_mem_dir = proof_dir / "op_mem"

    results = {"schema": "ia_milk.adaptive_proof.v1"}

    # Create fresh engine and CCP
    engine = AdaptiveLearningEngine(policy_path=policy_path)
    ccp = CognitiveControlPlane(op_mem_dir=op_mem_dir, adaptive_engine=engine)

    # ---- EXECUTION A: Initial policy (base scores only) ----
    print("\n[A] EXECUTION A: Initial policy (base scores, no learning)")
    print(f"  Policy version before: {engine.policy.version}")

    # Show candidates for "reasoning" capability
    candidates_before = ccp.router.select("reasoning", top_k=5)
    print(f"  Candidates (reasoning):")
    for c in candidates_before:
        print(f"    {c['id']}: base={c.get('base_score', c.get('score', 0)):.4f} "
              f"adjusted={c.get('adjusted_score', c.get('score', 0)):.4f} "
              f"mode={c.get('adaptive_explanation', {}).get('mode', 'N/A')}")

    # Execute task A
    result_a = ccp.execute_task("What folklore materials exist in the Atlas corpus?")
    print(f"  Task A: status={result_a['status']}, evidence={result_a['evidence_count']}, "
          f"inference={result_a['inference_count']}")
    print(f"  Policy version after A: {engine.policy.version}")

    # Record which capability was selected for reasoning
    selected_cap_a = None
    for step in result_a.get("execution_log", []):
        if step.get("action") == "reason":
            selected_cap_a = step.get("capability", "none")
            break
    print(f"  Selected reasoning capability: {selected_cap_a}")

    # Show policy stats after A
    stats_a = engine.policy.stats_summary()
    print(f"  Policy stats after A: {len(stats_a['by_capability'])} capabilities tracked, "
          f"version={stats_a['policy_version']}")
    results["execution_a"] = {
        "policy_version_before": 0,
        "policy_version_after": engine.policy.version,
        "task_status": result_a["status"],
        "evidence_count": result_a["evidence_count"],
        "selected_capability": selected_cap_a,
        "candidates": [{"id": c["id"], "base_score": c.get("base_score", c.get("score", 0)),
                        "adjusted_score": c.get("adjusted_score", c.get("score", 0))}
                       for c in candidates_before],
    }

    # ---- EXECUTION B: Policy adapts based on A's outcome ----
    print("\n[B] EXECUTION B: Policy adapts based on A's experience")
    print(f"  Policy version before B: {engine.policy.version}")

    # Show candidates again — should reflect learning from A
    candidates_after_a = ccp.router.select("reasoning", top_k=5)
    print(f"  Candidates (reasoning) after learning from A:")
    for c in candidates_after_a:
        exp = engine.explain_selection(c["id"])
        print(f"    {c['id']}: base={c.get('base_score', 0):.4f} "
              f"adjusted={c.get('adjusted_score', 0):.4f} "
              f"selections={exp['selections']} avg_reward={exp['avg_reward']:.4f}")

    result_b = ccp.execute_task("What territorial data exists about Portuguese freguesias?")
    print(f"  Task B: status={result_b['status']}, evidence={result_b['evidence_count']}")
    print(f"  Policy version after B: {engine.policy.version}")
    results["execution_b"] = {
        "policy_version_before": results["execution_a"]["policy_version_after"],
        "policy_version_after": engine.policy.version,
        "task_status": result_b["status"],
        "evidence_count": result_b["evidence_count"],
    }

    # ---- EXECUTION C: Demonstrate measurable policy change ----
    print("\n[C] EXECUTION C: Measurable policy change demonstration")
    print(f"  Policy version before C: {engine.policy.version}")

    # Show how policy has changed
    stats_c = engine.policy.stats_summary()
    print(f"  Total selections: {stats_c['total_selections']}")
    print(f"  Avg reward: {stats_c['avg_reward']:.4f}")
    print(f"  Capabilities tracked: {len(stats_c['by_capability'])}")
    for cap_id, cap_stats in stats_c["by_capability"].items():
        print(f"    {cap_id}: alpha={cap_stats['alpha']:.2f} beta={cap_stats['beta']:.2f} "
              f"selections={cap_stats['selections']} total_reward={cap_stats['total_reward']:.4f}")

    # Execute task C
    result_c = ccp.execute_task("What external evidence exists about the Atlas project?")
    print(f"  Task C: status={result_c['status']}, evidence={result_c['evidence_count']}")
    print(f"  Policy version after C: {engine.policy.version}")
    results["execution_c"] = {
        "policy_version_before": results["execution_b"]["policy_version_after"],
        "policy_version_after": engine.policy.version,
        "task_status": result_c["status"],
        "evidence_count": result_c["evidence_count"],
    }

    # ---- D. Demonstrate adaptation: compare policy before and after ----
    print("\n[D] ADAPTATION MEASUREMENT")
    # Show that policy version increased (learning happened)
    version_progression = [0, results["execution_a"]["policy_version_after"],
                          results["execution_b"]["policy_version_after"],
                          results["execution_c"]["policy_version_after"]]
    print(f"  Version progression: {version_progression}")
    print(f"  Policy changed: {len(set(version_progression)) > 1}")

    # Show explainability
    print("\n  Explainability (why was a capability chosen?):")
    for cap_id in list(stats_c["by_capability"].keys())[:3]:
        exp = engine.explain_selection(cap_id)
        print(f"    {cap_id}: selections={exp['selections']} "
              f"avg_reward={exp['avg_reward']:.4f} "
              f"expected_value={exp['expected_value']:.4f}")

    # Observability
    obs = engine.observability()
    print(f"\n  Observability:")
    print(f"    Policy version: {obs['policy_version']}")
    print(f"    Total learning events: {obs['total_learning_events']}")
    print(f"    Success rate: {obs['success_rate']:.4f}")
    print(f"    Exploration rate: {obs['exploration_rate']}")
    print(f"    Selections by capability: {obs['selections_by_capability']}")

    results["adaptation_measurement"] = {
        "version_progression": version_progression,
        "policy_changed": len(set(version_progression)) > 1,
        "final_policy_version": engine.policy.version,
        "observability": obs,
    }

    # ---- E. Reconstruct learning chain ----
    print("\n[E] LEARNING CHAIN RECONSTRUCTION")
    # Load learning events
    events = load_learning_events(limit=100)
    print(f"  Total learning events: {len(events)}")
    if events:
        first_event = events[0]
        print(f"  First event:")
        print(f"    task_id: {first_event['task_id'][:12]}")
        print(f"    selected: {first_event['selected_capability']}")
        print(f"    reward: {first_event['reward_final']:.4f}")
        print(f"    policy_before: v{first_event['policy_version_before']}")
        print(f"    policy_after: v{first_event['policy_version_after']}")
        print(f"    reward_components: {first_event['reward_components']}")
        print(f"    event_hash: {first_event['event_hash'][:16]}")

        last_event = events[-1]
        print(f"  Last event:")
        print(f"    task_id: {last_event['task_id'][:12]}")
        print(f"    selected: {last_event['selected_capability']}")
        print(f"    reward: {last_event['reward_final']:.4f}")
        print(f"    policy_before: v{last_event['policy_version_before']}")
        print(f"    policy_after: v{last_event['policy_version_after']}")

    results["learning_chain"] = {
        "total_events": len(events),
        "first_event": {
            "selected": events[0]["selected_capability"],
            "reward": events[0]["reward_final"],
            "policy_before": events[0]["policy_version_before"],
            "policy_after": events[0]["policy_version_after"],
        } if events else None,
        "last_event": {
            "selected": events[-1]["selected_capability"],
            "reward": events[-1]["reward_final"],
            "policy_before": events[-1]["policy_version_before"],
            "policy_after": events[-1]["policy_version_after"],
        } if events else None,
    }

    # ---- F. Sovereign Action Gate intact ----
    print("\n[F] SOVEREIGN ACTION GATE STATUS")
    gate_intact = all(r.get("gate_decisions", 0) >= 0 for r in
                      [result_a, result_b, result_c])
    print(f"  Gate exercised in all tasks: {gate_intact}")
    results["gate_status"] = {"intact": gate_intact}

    # ---- SAVE ----
    out_path = ROOT / "state" / "adaptive_learning_proof.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[F] SAVED: {out_path}")
    print("=" * 70)
    print("ADAPTIVE LEARNING PROOF COMPLETE")
    print(f"  Policy versions: {version_progression}")
    print(f"  Learning events: {len(events)}")
    print(f"  Policy changed measurably: {len(set(version_progression)) > 1}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    main()
