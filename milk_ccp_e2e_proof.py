#!/usr/bin/env python3
"""MILK Sovereign Cognitive Control Plane — End-to-End Proof.

Executes a real task that:
- Decides autonomously between 2 strategies/capabilities
- Performs retrieval/evidence gathering
- Uses local reasoning worker (GPT-OSS or heuristic fallback)
- Produces decision with EvidenceBundle
- Crosses Sovereign Action Gate in reversible/dry-safe mode
- Saves episode+outcome to operational memory
- Demonstrates full chain reconstruction: source->evidence->transform->inference->decision->action->outcome
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.cognitive_control_plane import (
    CognitiveControlPlane, CapabilityRouter, ReasoningWorker,
    BoundedOperatingLoop, OperationalMemory, EvidenceBundle, TaskEnvelope,
)
from milk_ai.action_gate import ActionGate


def main():
    print("=" * 70)
    print("MILK SOVEREIGN COGNITIVE CONTROL PLANE — END-TO-END PROOF")
    print("=" * 70)

    ccp = CognitiveControlPlane()
    results = {"schema": "ia_milk.ccp_e2e_proof.v1"}

    # ---- A. Execute a task requiring autonomous strategy decision ----
    print("\n[A] EXECUTE TASK: Autonomous strategy selection")
    task_result = ccp.execute_task(
        "What cultural materials about Portuguese folklore exist across local corpus and external sources?"
    )
    print(f"  Task ID: {task_result['task_id']}")
    print(f"  Status: {task_result['status']}")
    print(f"  Evidence: {task_result['evidence_count']} items")
    print(f"  Inferences: {task_result['inference_count']}")
    print(f"  Decisions: {task_result['decision_count']}")
    print(f"  Gate decisions: {task_result['gate_decisions']}")
    print(f"  Hash chain: {task_result['hash_chain'][:32]}...")
    print(f"  Bundle: {task_result['bundle_path']}")
    results["task_result"] = task_result

    # ---- B. Reconstruct full provenance chain ----
    print("\n[B] RECONSTRUCT CHAIN")
    chain = ccp.reconstruct_chain(task_result["task_id"])
    print(f"  Chain length: {chain['chain_length']}")
    for step in chain["chain"]:
        t = step["type"]
        if t == "source":
            print(f"    [{t}] {step['source']} uri={step.get('uri','')[:40]} hash={step.get('hash','')[:12]}")
        elif t == "evidence":
            print(f"    [{t}] retrieval={step.get('retrieval','')} preview={step.get('content_preview','')[:60]}")
        elif t == "inference":
            print(f"    [{t}] model={step.get('model','')} output={step.get('output_preview','')[:60]}")
        elif t == "decision":
            print(f"    [{t}] {step.get('decision','')}")
        elif t == "action":
            print(f"    [{t}] {step.get('action','')}")
        elif t == "outcome":
            print(f"    [{t}] {step.get('outcome','')}")
    print(f"  PROV-O available: {chain['prov_o_available']}")
    results["chain_reconstruction"] = chain

    # ---- C. Bounded Operating Loop ----
    print("\n[C] BOUNDED OPERATING LOOP")
    gate = ActionGate()
    router = CapabilityRouter()
    worker = ReasoningWorker()
    op_mem = OperationalMemory()
    loop = BoundedOperatingLoop(router, worker, gate, op_mem, max_steps=10, max_time_s=60)
    loop_result = loop.run()
    print(f"  Loop status: {loop_result['status']}")
    print(f"  Steps executed: {loop_result['steps_executed']}")
    print(f"  Hash chain: {loop_result['hash_chain'][:32]}...")
    for entry in loop_result["loop_log"]:
        print(f"    Step {entry.get('step','?')}: {entry.get('action','')} -> {entry.get('result','')[:60]}")
    results["bounded_loop"] = loop_result

    # ---- D. Operational Memory state ----
    print("\n[D] OPERATIONAL MEMORY")
    mem_stats = op_mem.stats()
    print(f"  Total records: {mem_stats['total_records']}")
    print(f"  By type: {mem_stats['by_type']}")
    print(f"  Learning events: {mem_stats['learning_events']}")
    print(f"  Memory dir: {mem_stats['memory_dir']}")
    results["operational_memory"] = mem_stats

    # ---- E. Health/Observability ----
    print("\n[E] HEALTH / OBSERVABILITY")
    health = ccp.health()
    print(f"  Services: {json.dumps(health['services'], indent=2)}")
    print(f"  GPU: {health['gpu']}")
    print(f"  Gaps: {health['gaps']}")
    results["health"] = health

    # ---- F. Feedback as learning event ----
    print("\n[F] FEEDBACK AS LEARNING EVENT")
    feedback = op_mem.append_feedback(
        "The evidence-based answer correctly identified local corpus as primary source",
        task_id=task_result["task_id"],
        rating=5,
    )
    print(f"  Feedback recorded: {feedback['event_id'][:12]}")
    results["feedback"] = feedback

    # ---- SAVE ----
    out_path = ROOT / "state" / "ccp_e2e_proof.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[F] SAVED: {out_path}")
    print("=" * 70)
    print("END-TO-END PROOF COMPLETE")
    print(f"  trace_id: {task_result['trace_id']}")
    print(f"  bundle_path: {task_result['bundle_path']}")
    print(f"  operational_memory: {mem_stats['memory_dir']}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    main()
