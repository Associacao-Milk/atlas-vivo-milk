#!/usr/bin/env python3
"""MILK Maximum Capability Proof — E2E demonstration of all new capabilities."""
from __future__ import annotations
import json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.execution_graph_and_compliance import (
    ExecutionGraphRouter, EvidenceReconciliation, ComplianceKernel,
    ContextualAdaptivePolicy, SemanticProjection, SovereignCore,
)
from milk_ai.adaptive_engine import AdaptiveLearningEngine, load_learning_events
from milk_ai.cognitive_control_plane import CognitiveControlPlane

def main():
    print("=" * 70)
    print("MILK MAXIMUM CAPABILITY PROOF")
    print("=" * 70)
    random.seed(42)  # deterministic proof

    proof_dir = ROOT / "state" / "maxcap_proof"
    proof_dir.mkdir(parents=True, exist_ok=True)
    engine = AdaptiveLearningEngine(policy_path=proof_dir / "policy.json")
    ccp = CognitiveControlPlane(op_mem_dir=proof_dir / "op_mem", adaptive_engine=engine)
    results = {"schema": "ia_milk.maxcap_proof.v1", "seed": 42}

    # A. Capability mesh
    mesh = json.loads((ROOT / "state" / "capability_mesh.json").read_text(encoding="utf-8"))
    print(f"\n[A] CAPABILITY MESH: {mesh['summary']['total_capabilities']} capabilities, {mesh['summary']['by_status']}")
    results["capability_mesh"] = mesh["summary"]

    # B. Compliance assessment
    print("\n[B] COMPLIANCE ASSESSMENT")
    kernel = ComplianceKernel()
    assessment = kernel.assess(use_case="cultural_heritage_retrieval", ai_components=True, personal_data=False)
    print(f"  Overall: {assessment.overall_state}, decision: {assessment.decision_effect}")
    print(f"  Profiles assessed: {len(assessment.profiles)}")
    results["compliance"] = assessment.to_dict()

    # C. Execution graph with multiple capabilities
    print("\n[C] EXECUTION GRAPH (>=2 capabilities)")
    graph_router = ExecutionGraphRouter(adaptive_engine=engine)
    candidates = ccp.router.select("external_read", top_k=5, task_risk="normal")
    graph = graph_router.select_graph("external_read", candidates, {"evidence_level": "high"})
    print(f"  Mode: {graph.mode}, capabilities: {len(graph.capabilities)}")
    print(f"  Description: {graph.description}")
    results["execution_graph"] = graph.to_dict()

    # D. Multi-source evidence reconciliation
    print("\n[D] EVIDENCE RECONCILIATION (>=2 sources)")
    recon = EvidenceReconciliation()
    evidence_items = [
        {"source": "retrieval:corpus", "content": "Folklore data from local corpus about Portuguese traditions", "content_hash": "h1"},
        {"source": "adapter:localfs", "content": "Filesystem evidence from local Atlas directory", "content_hash": "h2"},
        {"source": "retrieval:corpus", "content": "Folklore data from local corpus about Portuguese traditions", "content_hash": "h1"},  # dup
    ]
    reconciled = recon.reconcile(evidence_items)
    print(f"  Sources: {reconciled.sources}, deduped: {reconciled.deduped_count}, independent: {reconciled.independent_sources}")
    print(f"  Quality: {reconciled.quality_score}, conflicts: {len(reconciled.conflicts)}")
    results["evidence_reconciliation"] = reconciled.to_dict()

    # E. Execute real task with CCP
    print("\n[E] REAL TASK EXECUTION")
    result = ccp.execute_task("What folklore materials exist in the Atlas corpus about Portuguese traditions?")
    print(f"  Status: {result['status']}, evidence: {result['evidence_count']}, trace: {result['trace_id'][:12]}")
    results["task_execution"] = {"status": result["status"], "trace_id": result["trace_id"],
                                  "evidence_count": result["evidence_count"]}

    # F. Learning events + policy update
    print("\n[F] LEARNING EVENTS + POLICY UPDATE")
    events = load_learning_events(limit=100)
    print(f"  Total learning events: {len(events)}")
    print(f"  Policy version: {engine.policy.version}")
    # Show deterministic policy change (expected value, not random sample)
    if engine.policy.stats:
        for cap_id, stats in list(engine.policy.stats.items())[:3]:
            ev = stats.alpha / (stats.alpha + stats.beta)
            print(f"  {cap_id}: alpha={stats.alpha:.2f} beta={stats.beta:.2f} expected_value={ev:.4f}")
    results["learning"] = {"total_events": len(events), "policy_version": engine.policy.version}

    # G. Contextual adaptive policy
    print("\n[G] CONTEXTUAL ADAPTIVE POLICY")
    cap_policy = ContextualAdaptivePolicy(engine.policy)
    # Train with context
    for _ in range(3):
        cap_policy.update_with_context("retrieval:corpus", reward=0.7, success=True,
                                       context={"task_family": "retrieval", "risk_class": "normal"})
    exp = cap_policy.explain_contextual("retrieval:corpus", {"task_family": "retrieval", "risk_class": "normal"})
    print(f"  Context band: {exp['context_band']}")
    print(f"  Contextual selections: {exp['contextual_selections']}")
    print(f"  Expected value: {exp['expected_value']}")
    results["contextual_policy"] = exp

    # H. Semantic projection
    print("\n[H] SEMANTIC PROJECTION")
    sp = SemanticProjection()
    entity = sp.project_entity("cultural_asset", "folclore_001", {"name": "Trava-línguas", "region": "Norte"})
    print(f"  Entity: {entity['id']}, type: {entity['type']}, NGSI-LD: {entity['ngsi-ld:type'][:40]}")
    results["semantic"] = {"entity_id": entity["id"], "ngsi_ld_type": entity["ngsi-ld:type"]}

    # I. Sovereign core verification
    print("\n[I] SOVEREIGN CORE VERIFICATION")
    sc = SovereignCore()
    core_result = sc.verify_core()
    print(f"  All present: {core_result['all_present']}")
    print(f"  External deps required: {core_result['external_dependencies_required_for_core']}")
    print(f"  Sovereignty verified: {core_result['sovereignty_verified']}")
    results["sovereign_core"] = core_result

    # J. Explain selection
    print("\n[J] EXPLAIN SELECTION")
    exp = ccp.explain_selection("retrieval:corpus")
    print(f"  Capability: {exp['capability_id']}")
    print(f"  Selections: {exp['selections']}, avg_reward: {exp['avg_reward']:.4f}")
    results["explain_selection"] = exp

    # Save
    out = ROOT / "state" / "maximum_capability_proof.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSAVED: {out}")
    print("=" * 70)
    print(f"PROOF COMPLETE | trace={result['trace_id'][:16]}")
    print("=" * 70)

if __name__ == "__main__":
    main()
