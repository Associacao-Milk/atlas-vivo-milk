"""Tests for Execution Graph Router, Evidence Reconciliation, Compliance Kernel,
Contextual Adaptive Policy, and Semantic Projection."""
import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.execution_graph_and_compliance import (
    ExecutionGraph, ExecutionGraphRouter,
    EvidenceReconciliation, ReconciledEvidence,
    ComplianceKernel, ComplianceAssessment, COMPLIANCE_PROFILES,
    ContextualAdaptivePolicy, ContextualBanditStats,
    SemanticProjection, SEMANTIC_ENTITIES,
    SovereignCore,
)
from milk_ai.adaptive_engine import AdaptivePolicy, AdaptiveLearningEngine


# ---- ExecutionGraph tests ----

class TestExecutionGraph:
    def test_single_mode(self):
        g = ExecutionGraph(mode="SINGLE", capabilities=[{"id": "cap:a"}])
        assert g.mode == "SINGLE"
        assert len(g.capabilities) == 1

    def test_to_dict(self):
        g = ExecutionGraph(mode="PARALLEL", capabilities=[{"id": "a"}, {"id": "b"}])
        d = g.to_dict()
        assert "graph_id" in d and "mode" in d


class TestExecutionGraphRouter:
    def test_select_single(self):
        r = ExecutionGraphRouter()
        candidates = [{"id": "cap:a", "score": 0.8}, {"id": "cap:b", "score": 0.5}]
        g = r.select_graph("reasoning", candidates, {"risk_class": "normal"})
        assert g.mode == "SINGLE"
        assert len(g.capabilities) == 1

    def test_select_parallel_for_high_evidence(self):
        r = ExecutionGraphRouter()
        candidates = [{"id": "cap:a", "score": 0.8}, {"id": "cap:b", "score": 0.7}, {"id": "cap:c", "score": 0.6}]
        g = r.select_graph("retrieval", candidates, {"evidence_level": "high"})
        assert g.mode == "PARALLEL"
        assert len(g.capabilities) >= 2

    def test_select_verify(self):
        r = ExecutionGraphRouter()
        candidates = [{"id": "cap:a", "score": 0.8}, {"id": "cap:b", "score": 0.7}]
        g = r.select_graph("reasoning", candidates, {"needs_verification": True})
        assert g.mode == "VERIFY"
        assert len(g.capabilities) == 2

    def test_select_fallback_high_risk(self):
        r = ExecutionGraphRouter()
        candidates = [{"id": "cap:a", "score": 0.8}, {"id": "cap:b", "score": 0.5}]
        g = r.select_graph("reasoning", candidates, {"risk_class": "high"})
        assert g.mode == "FALLBACK"

    def test_select_consensus(self):
        r = ExecutionGraphRouter()
        candidates = [{"id": "a", "score": 0.8}, {"id": "b", "score": 0.7}, {"id": "c", "score": 0.6}]
        g = r.select_graph("reasoning", candidates, {"needs_consensus": True})
        assert g.mode == "CONSENSUS"

    def test_no_candidates(self):
        r = ExecutionGraphRouter()
        g = r.select_graph("reasoning", [])
        assert g.mode == "SINGLE"
        assert len(g.capabilities) == 0


# ---- Evidence Reconciliation tests ----

class TestEvidenceReconciliation:
    def test_deduplication(self):
        recon = EvidenceReconciliation()
        items = [
            {"source": "a", "content": "same", "content_hash": "h1"},
            {"source": "b", "content": "same", "content_hash": "h1"},  # dup
            {"source": "c", "content": "different", "content_hash": "h2"},
        ]
        result = recon.reconcile(items)
        assert result.deduped_count == 1
        assert len(result.items) == 2

    def test_conflict_detection(self):
        recon = EvidenceReconciliation()
        items = [
            {"source": "source:a", "content": "Portuguese folklore is rich", "content_hash": "h1"},
            {"source": "source:b", "content": "Portuguese folklore is diverse", "content_hash": "h2"},
        ]
        result = recon.reconcile(items)
        # First 50 chars overlap ("Portuguese folklore is ") but hashes differ
        assert len(result.conflicts) >= 1

    def test_independent_sources(self):
        recon = EvidenceReconciliation()
        items = [
            {"source": "retrieval:corpus", "content": "a", "content_hash": "h1"},
            {"source": "adapter:nextcloud", "content": "b", "content_hash": "h2"},
        ]
        result = recon.reconcile(items)
        assert result.independent_sources >= 2

    def test_quality_score(self):
        recon = EvidenceReconciliation()
        items = [
            {"source": "retrieval:corpus", "content": "a", "content_hash": "h1"},
            {"source": "adapter:nextcloud", "content": "b", "content_hash": "h2"},
            {"source": "adapter:github", "content": "c", "content_hash": "h3"},
        ]
        result = recon.reconcile(items)
        assert result.quality_score > 0.5

    def test_empty(self):
        recon = EvidenceReconciliation()
        result = recon.reconcile([])
        assert result.quality_score == 0.0


# ---- Compliance Kernel tests ----

class TestComplianceKernel:
    def test_assess_ai_act(self):
        kernel = ComplianceKernel()
        assessment = kernel.assess(ai_components=True, use_case="cultural_heritage_retrieval")
        assert assessment.overall_state in ("CONFORMS_TECHNICALLY", "HUMAN_REVIEW_REQUIRED")
        # Find AI Act profile
        ai_act = [p for p in assessment.profiles if p["profile"] == "eu_ai_act"]
        assert len(ai_act) == 1
        assert ai_act[0]["applicability"] != "NOT_APPLICABLE"

    def test_not_high_risk(self):
        kernel = ComplianceKernel()
        assessment = kernel.assess(ai_components=True, use_case="cultural_heritage")
        # Should NOT classify as high-risk
        assert assessment.overall_state != "BLOCKED"

    def test_prohibited_blocked(self):
        kernel = ComplianceKernel()
        assessment = kernel.assess(ai_components=True, use_case="prohibited_social_scoring")
        assert assessment.overall_state == "BLOCKED"

    def test_iap_not_applicable_for_private(self):
        kernel = ComplianceKernel()
        assessment = kernel.assess(public_service=False)
        iap = [p for p in assessment.profiles if p["profile"] == "iap_rnid"]
        assert iap[0]["applicability"] == "NOT_APPLICABLE"

    def test_rgpd_always_assessed(self):
        kernel = ComplianceKernel()
        assessment = kernel.assess(personal_data=False)
        rgpd = [p for p in assessment.profiles if p["profile"] == "rgpd"]
        assert rgpd[0]["applicability"] != "NOT_APPLICABLE"

    def test_arpgu_review_2026_unconfirmed(self):
        kernel = ComplianceKernel()
        arpgu = kernel.profiles["arpgu"]
        assert "unconfirmed" in arpgu["version"] or "review" in arpgu["version"].lower()

    def test_fiware_is_technical_not_law(self):
        kernel = ComplianceKernel()
        fiware = kernel.profiles["fiware_ngsi_ld"]
        assert "technical_standard" in fiware["role"]

    def test_export_schema(self):
        kernel = ComplianceKernel()
        schema = kernel.export_schema()
        assert "schema_version" in schema
        assert "eu_ai_act" in schema["profiles"]

    def test_all_profiles_present(self):
        kernel = ComplianceKernel()
        expected = ["eu_ai_act", "rgpd", "interoperable_europe_act", "eif",
                   "arpgu", "iap_rnid", "fiware_ngsi_ld", "inspire", "wcag_2_2"]
        for p in expected:
            assert p in kernel.profiles


# ---- Contextual Adaptive Policy tests ----

class TestContextualAdaptivePolicy:
    def test_context_band(self, tmp_path):
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        band = cap._context_band({"task_family": "retrieval", "risk_class": "normal"})
        assert "task_family=retrieval" in band
        assert "risk_class=normal" in band

    def test_default_band(self, tmp_path):
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        assert cap._context_band({}) == "default"

    def test_adjust_with_context(self, tmp_path):
        random.seed(42)
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        adjusted, exp = cap.adjust_score_with_context(0.7, "cap:test",
                                                      {"task_family": "retrieval"})
        assert 0 <= adjusted <= 1
        assert "context_band" in exp

    def test_update_with_context(self, tmp_path):
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        cap.update_with_context("cap:test", reward=0.5, success=True,
                               context={"task_family": "retrieval"})
        key = "cap:test:task_family=retrieval|risk_class=any|modality=any|evidence_level=any"
        assert key in cap.contextual_stats
        assert cap.contextual_stats[key].selections == 1

    def test_reward_normalization(self, tmp_path):
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        # Reward -1 (worst) should increase beta more than alpha
        cap.update_with_context("cap:bad", reward=-1.0, success=False,
                               context={"task_family": "test"})
        # Reward +1 (best) should increase alpha
        cap.update_with_context("cap:good", reward=1.0, success=True,
                               context={"task_family": "test"})
        bad_key = [k for k in cap.contextual_stats if "cap:bad" in k][0]
        good_key = [k for k in cap.contextual_stats if "cap:good" in k][0]
        assert cap.contextual_stats[bad_key].beta > 1.0
        assert cap.contextual_stats[good_key].alpha > 1.0

    def test_contextual_differs_from_base(self, tmp_path):
        random.seed(42)
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        # Train base with some experience
        for _ in range(5):
            base.update("cap:test", reward=0.8, success=True)
        # Contextual should initialize from base
        adjusted, exp = cap.adjust_score_with_context(0.5, "cap:test",
                                                      {"task_family": "retrieval"})
        assert exp["alpha"] > 1.0  # initialized from base

    def test_explain_contextual(self, tmp_path):
        base = AdaptivePolicy(policy_path=tmp_path / "p.json")
        cap = ContextualAdaptivePolicy(base)
        cap.update_with_context("cap:test", reward=0.5, success=True,
                               context={"task_family": "retrieval"})
        exp = cap.explain_contextual("cap:test", {"task_family": "retrieval"})
        assert "context_band" in exp
        assert exp["contextual_selections"] == 1


# ---- Semantic Projection tests ----

class TestSemanticProjection:
    def test_project_entity(self):
        sp = SemanticProjection()
        entity = sp.project_entity("territory", "freguesia_123", {"name": "São Mamede"})
        assert entity["id"] == "urn:milk:territory:freguesia_123"
        assert entity["type"] == "territory"
        assert "@context" in entity
        assert "ngsi-ld:type" in entity

    def test_fiware_mapping(self):
        sp = SemanticProjection()
        entity = sp.project_entity("municipality", "lisboa")
        assert "smartdatamodels.org" in entity["ngsi-ld:type"]

    def test_project_provenance(self):
        sp = SemanticProjection()
        bundle = {
            "items": [{"content_hash": "abc123", "source": "corpus", "retrieval_method": "sparse"}],
            "inferences": [{"inference_id": "inf1", "model": "gpt-oss", "timestamp": "2026"}],
        }
        prov = sp.project_provenance(bundle)
        assert "@context" in prov
        assert "prov" in prov["@context"]
        assert len(prov["@graph"]) >= 3  # entities + activities + agent

    def test_export_schema(self):
        sp = SemanticProjection()
        schema = sp.export_schema()
        assert "territory" in schema["entities"]
        assert schema["fiware_required"] is False

    def test_all_entities_present(self):
        sp = SemanticProjection()
        expected = ["territory", "parish", "municipality", "person", "organisation",
                   "source", "evidence", "cultural_asset", "event", "curatorial_device",
                   "intervention", "observation", "outcome"]
        for e in expected:
            assert e in sp.entities


# ---- Sovereign Core tests ----

class TestSovereignCore:
    def test_core_components(self):
        sc = SovereignCore()
        assert "task_intake" in sc.CORE_COMPONENTS
        assert "action_gate" in sc.CORE_COMPONENTS

    def test_no_external_deps_for_core(self):
        sc = SovereignCore()
        result = sc.verify_core()
        assert result["external_dependencies_required_for_core"] == []
        assert result["sovereignty_verified"] is True

    def test_fallback_mode(self):
        sc = SovereignCore()
        result = sc.verify_core()
        assert "fallback_mode" in result


# ---- Integration tests ----

class TestIntegration:
    def test_execution_graph_with_adaptive(self, tmp_path):
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "p.json")
        router = ExecutionGraphRouter(adaptive_engine=engine)
        candidates = [{"id": "cap:a", "score": 0.8}, {"id": "cap:b", "score": 0.6}]
        g = router.select_graph("reasoning", candidates, {"evidence_level": "high"})
        assert g.mode == "PARALLEL"
        assert "base_score" in g.capabilities[0]

    def test_compliance_before_gate(self):
        """Compliance should be assessed before Action Gate."""
        kernel = ComplianceKernel()
        assessment = kernel.assess(use_case="cultural_heritage_retrieval")
        assert assessment.decision_effect in ("proceed", "proceed_with_review", "block")
        # If blocked, gate would block; otherwise gate allows
        if assessment.overall_state == "BLOCKED":
            assert assessment.decision_effect == "block"
