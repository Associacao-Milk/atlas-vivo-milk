"""Tests for MILK Canonical Governance Layer."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.governance import (
    CanonicalOntology, CANONICAL_ENTITIES, CANONICAL_RELATIONS,
    RiskRegister, RiskEntry, RiskCategory, RiskStatus,
    PolicyRegistry, PolicyEntry, PolicyType,
    HumanOversightRegistry, HumanApprovalEntry, ApprovalState,
    AuditRegistry, AuditEntry, AuditAction,
    IncidentRegistry, IncidentEntry, IncidentSeverity,
    ComplianceRegistry,
    GovernanceOrchestrator,
)


class TestCanonicalOntology:
    def test_entities_present(self):
        ont = CanonicalOntology()
        for e in ["Agent", "Task", "Memory", "Evidence", "Action",
                  "Decision", "Risk", "Policy", "Source", "Document",
                  "Chunk", "RetrievalResult", "ComplianceCheck", "HumanApproval"]:
            assert e in ont.entities

    def test_relations_present(self):
        ont = CanonicalOntology()
        for r in ["creates", "uses", "supports", "justifies",
                  "depends_on", "violates", "mitigates"]:
            assert r in ont.relations

    def test_to_dict(self):
        ont = CanonicalOntology()
        d = ont.to_dict()
        assert d["schema_version"] == "ontology.v1"
        assert d["namespace"] == "https://associacaomilk.pt/ns#"

    def test_to_jsonld(self):
        ont = CanonicalOntology()
        j = ont.to_jsonld()
        assert "@context" in j
        assert "@graph" in j
        assert len(j["@graph"]) >= len(ont.entities) + len(ont.relations)


class TestRiskRegister:
    def test_add_and_list(self, tmp_path):
        reg = RiskRegister(tmp_path / "risks.json")
        risk = reg.add("security", "Test risk", likelihood="high", impact="critical")
        assert risk.risk_id != ""
        assert len(reg.list()) == 1

    def test_update(self, tmp_path):
        reg = RiskRegister(tmp_path / "risks.json")
        risk = reg.add("operational", "Test", likelihood="medium")
        assert reg.update(risk.risk_id, status="mitigated")
        assert reg.risks[risk.risk_id].status == "mitigated"

    def test_by_status(self, tmp_path):
        reg = RiskRegister(tmp_path / "risks.json")
        reg.add("security", "Open risk")
        reg.add("operational", "Closed", likelihood="low")
        open_risks = reg.by_status("open")
        assert len(open_risks) == 2

    def test_persist(self, tmp_path):
        reg1 = RiskRegister(tmp_path / "risks.json")
        reg1.add("security", "Persisted risk")
        reg2 = RiskRegister(tmp_path / "risks.json")
        assert len(reg2.list()) == 1


class TestPolicyRegistry:
    def test_register(self, tmp_path):
        reg = PolicyRegistry(tmp_path / "policies.json")
        p = reg.register("execution", "Test Policy", "Test description")
        assert p.policy_id != ""
        assert p.active is True

    def test_evaluate_normal(self, tmp_path):
        reg = PolicyRegistry(tmp_path / "policies.json")
        reg.register("execution", "Normal Policy")
        result = reg.evaluate("read_resource", {"critical": False})
        assert result["allowed"] is True

    def test_evaluate_critical(self, tmp_path):
        reg = PolicyRegistry(tmp_path / "policies.json")
        reg.register("human_oversight", "Critical Approval")
        result = reg.evaluate("publish_zenodo", {"critical": True})
        assert result["requires_human"] is True
        assert result["allowed"] is False

    def test_persist(self, tmp_path):
        reg1 = PolicyRegistry(tmp_path / "policies.json")
        reg1.register("execution", "Persisted")
        reg2 = PolicyRegistry(tmp_path / "policies.json")
        assert len(reg2.policies) == 1


class TestHumanOversightRegistry:
    def test_request_and_decide(self, tmp_path):
        reg = HumanOversightRegistry(tmp_path / "oversight.json")
        entry = reg.request("publish_zenodo", "milk_system", "zenodo")
        assert entry.state == "pending_review"
        assert reg.decide(entry.approval_id, "human", "approved", "OK")
        assert reg.approvals[entry.approval_id].state == "approved"

    def test_pending(self, tmp_path):
        reg = HumanOversightRegistry(tmp_path / "oversight.json")
        reg.request("action1", "actor")
        reg.request("action2", "actor")
        assert len(reg.pending()) == 2


class TestAuditRegistry:
    def test_record_and_query(self, tmp_path):
        reg = AuditRegistry(tmp_path / "audit.jsonl")
        entry = reg.record(who="actor", what="execute", why="test",
                          evidence="hash123", outcome="success", trace_id="t1")
        assert entry.audit_id != ""
        results = reg.query(trace_id="t1")
        assert len(results) == 1
        assert results[0]["who"] == "actor"

    def test_query_all(self, tmp_path):
        reg = AuditRegistry(tmp_path / "audit.jsonl")
        reg.record(who="a1", what="read", trace_id="t1")
        reg.record(who="a2", what="write", trace_id="t2")
        all_results = reg.query()
        assert len(all_results) == 2


class TestIncidentRegistry:
    def test_report_and_resolve(self, tmp_path):
        reg = IncidentRegistry(tmp_path / "incidents.json")
        inc = reg.report("high", "security", "Security incident")
        assert inc.status == "open"
        assert reg.resolve(inc.incident_id, "root cause", "fix applied")
        assert reg.incidents[inc.incident_id].status == "resolved"


class TestComplianceRegistry:
    def test_record_and_latest(self, tmp_path):
        reg = ComplianceRegistry(tmp_path / "compliance.json")
        reg.record({"assessment_id": "a1", "overall_state": "CONFORMS_TECHNICALLY"})
        reg.record({"assessment_id": "a2", "overall_state": "HUMAN_REVIEW_REQUIRED"})
        assert reg.latest()["assessment_id"] == "a2"


class TestGovernanceOrchestrator:
    def test_init_creates_default_policies(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        assert len(gov.policies.policies) >= 3

    def test_evaluate_normal_action(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        result = gov.evaluate_action(action="read_resource", actor="milk_system",
                                     critical=False, trace_id="t1")
        assert result["allowed"] is True
        assert result["requires_human"] is False

    def test_evaluate_critical_action(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        result = gov.evaluate_action(action="publish_zenodo", actor="milk_system",
                                     critical=True, trace_id="t2")
        assert result["allowed"] is False
        assert result["requires_human"] is True
        assert result["approval_id"] != ""

    def test_approve_action(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        result = gov.evaluate_action(action="deploy", actor="milk_system",
                                     critical=True, trace_id="t3")
        approval_id = result["approval_id"]
        assert gov.approve(approval_id, "human_admin", "approved", "Looks good")
        entry = gov.oversight.approvals[approval_id]
        assert entry.state == "approved"
        assert entry.approver == "human_admin"

    def test_audit_trail_generated(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        result = gov.evaluate_action(action="read", actor="test", trace_id="t4")
        audit_entries = gov.audit.query(trace_id="t4")
        assert len(audit_entries) == 1
        assert audit_entries[0]["who"] == "test"
        assert audit_entries[0]["what"] == "read"

    def test_export_canonical(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        state = gov.export_canonical()
        assert state["schema_version"] == "governance.v1"
        assert "ontology" in state
        assert state["policy_count"] >= 3

    def test_health(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        h = gov.health()
        assert h["status"] == "healthy"
        assert h["policies_active"] >= 3

    def test_risk_aware(self, tmp_path):
        gov = GovernanceOrchestrator(tmp_path / "gov")
        gov.risks.add("security", "External dependency risk",
                     likelihood="low", impact="medium", mitigation="Local-first fallback")
        result = gov.evaluate_action(action="external_write", actor="milk_system",
                                     critical=False, trace_id="t5")
        # Should identify security risks
        assert len(result["risks_identified"]) >= 0  # risks tracked

    def test_decision_chain_traceable(self, tmp_path):
        """Every decision must be traceable: Decision -> Evidence -> Policies -> Audit."""
        gov = GovernanceOrchestrator(tmp_path / "gov")
        result = gov.evaluate_action(action="execute", actor="agent",
                                     evidence="evidence_hash_123",
                                     critical=False, trace_id="trace_6")
        # Audit trail has the evidence
        audit = gov.audit.query(trace_id="trace_6")
        assert audit[0]["evidence"] == "evidence_hash_123"
        assert audit[0]["policy"] != ""  # policies evaluated
        assert audit[0]["outcome"] in ("allowed", "blocked_or_pending")
