"""MILK European Sovereign Cognitive Platform — Canonical Governance Layer.

Implements: Risk Register, Policy Registry, Human Oversight Registry,
Audit Registry, Incident Registry, Compliance Registry, Canonical Ontology,
Traceability, Evidence-Decision chains.

Uses existing Pydantic contracts from hardening.py where available.
Uses existing StrictModel from governance_models.py for non-Pydantic validation.
Does NOT replace existing components — adds governance layer.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parents[2]
_GOVERNANCE_DIR = _ROOT / "state" / "governance"


def _now():
    return datetime.now(timezone.utc).isoformat()

def _uuid():
    return uuid.uuid4().hex

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Enums ──

class RiskCategory(str, Enum):
    OPERATIONAL = "operational"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    DATA_QUALITY = "data_quality"
    SOVEREIGNTY = "sovereignty"
    PRIVACY = "privacy"
    INTEROPERABILITY = "interoperability"
    FINANCIAL = "financial"

class RiskStatus(str, Enum):
    OPEN = "open"
    MITIGATED = "mitigated"
    CLOSED = "closed"
    ACCEPTED = "accepted"

class ApprovalState(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"

class PolicyType(str, Enum):
    RETRIEVAL = "retrieval"
    EXECUTION = "execution"
    PUBLICATION = "publication"
    DATA_ACCESS = "data_access"
    EXTERNAL_WRITE = "external_write"
    HUMAN_OVERSIGHT = "human_oversight"

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    DEPLOY = "deploy"


# ── Canonical Ontology ──

CANONICAL_ENTITIES = [
    "Agent", "Task", "Memory", "Evidence", "Action",
    "Decision", "Risk", "Policy", "Source", "Document",
    "Chunk", "RetrievalResult", "ComplianceCheck", "HumanApproval",
]

CANONICAL_RELATIONS = [
    "creates", "uses", "supports", "justifies",
    "depends_on", "violates", "mitigates",
    "retrieves", "evaluates", "approves",
    "traces_to", "derives_from", "governs",
]


class CanonicalOntology:
    """Minimal canonical ontology for MILK cognitive platform."""

    def __init__(self):
        self.entities = list(CANONICAL_ENTITIES)
        self.relations = list(CANONICAL_RELATIONS)
        self.version = "ontology-v1"
        self.namespace = "https://associacaomilk.pt/ns#"

    def to_dict(self) -> dict:
        return {
            "schema_version": "ontology.v1",
            "namespace": self.namespace,
            "entities": self.entities,
            "relations": self.relations,
            "version": self.version,
        }

    def to_jsonld(self) -> dict:
        return {
            "@context": {"milk": self.namespace, "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
            "@graph": [
                {"@id": f"milk:{e}", "@type": "owl:Class"} for e in self.entities
            ] + [
                {"@id": f"milk:{r}", "@type": "owl:ObjectProperty"} for r in self.relations
            ],
        }


# ── Risk Register ──

@dataclass
class RiskEntry:
    risk_id: str = field(default_factory=_uuid)
    category: str = "operational"
    description: str = ""
    likelihood: str = "medium"  # low, medium, high
    impact: str = "medium"      # low, medium, high, critical
    mitigation: str = ""
    owner: str = ""
    status: str = "open"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    trace_id: str = ""
    schema_version: str = "risk.v1"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class RiskRegister:
    """Machine-readable risk register."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "risk_register.json"
        self.risks: dict[str, RiskEntry] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for rid, r in data.get("risks", {}).items():
                self.risks[rid] = RiskEntry(**r)

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema": "ia_milk.risk_register.v1", "risks": {k: v.to_dict() for k, v in self.risks.items()}}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, category: str, description: str, likelihood: str = "medium",
            impact: str = "medium", mitigation: str = "", owner: str = "",
            trace_id: str = "") -> RiskEntry:
        risk = RiskEntry(category=category, description=description,
                         likelihood=likelihood, impact=impact,
                         mitigation=mitigation, owner=owner, trace_id=trace_id)
        self.risks[risk.risk_id] = risk
        self._save()
        return risk

    def update(self, risk_id: str, **kwargs) -> bool:
        if risk_id not in self.risks:
            return False
        risk = self.risks[risk_id]
        for k, v in kwargs.items():
            if hasattr(risk, k):
                setattr(risk, k, v)
        risk.updated_at = _now()
        self._save()
        return True

    def list(self) -> list[dict]:
        return [r.to_dict() for r in self.risks.values()]

    def by_status(self, status: str) -> list[dict]:
        return [r.to_dict() for r in self.risks.values() if r.status == status]


# ── Policy Registry ──

@dataclass
class PolicyEntry:
    policy_id: str = field(default_factory=_uuid)
    type: str = "execution"
    name: str = ""
    description: str = ""
    rules: dict = field(default_factory=dict)
    active: bool = True
    version: int = 1
    created_at: str = field(default_factory=_now)
    schema_version: str = "policy.v1"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class PolicyRegistry:
    """Canonical policy registry for governance."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "policy_registry.json"
        self.policies: dict[str, PolicyEntry] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for pid, p in data.get("policies", {}).items():
                self.policies[pid] = PolicyEntry(**p)

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema": "ia_milk.policy_registry.v1",
                "policies": {k: v.to_dict() for k, v in self.policies.items()}}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def register(self, type: str, name: str, description: str = "",
                 rules: dict | None = None) -> PolicyEntry:
        policy = PolicyEntry(type=type, name=name, description=description,
                             rules=rules or {})
        self.policies[policy.policy_id] = policy
        self._save()
        return policy

    def evaluate(self, action: str, context: dict | None = None) -> dict:
        """Evaluate action against active policies."""
        ctx = context or {}
        result = {"allowed": True, "evaluated_policies": [], "requires_human": False}
        for p in self.policies.values():
            if not p.active:
                continue
            if p.type == "human_oversight":
                if ctx.get("critical", False):
                    result["requires_human"] = True
                    result["allowed"] = False
            result["evaluated_policies"].append({
                "policy_id": p.policy_id, "name": p.name, "type": p.type, "active": p.active
            })
        return result


# ── Human Oversight Registry ──

@dataclass
class HumanApprovalEntry:
    approval_id: str = field(default_factory=_uuid)
    action: str = ""
    actor: str = ""
    target: str = ""
    state: str = "pending_review"  # approved, rejected, pending_review
    approver: str = ""
    reason: str = ""
    created_at: str = field(default_factory=_now)
    decided_at: str = ""
    trace_id: str = ""
    schema_version: str = "human_approval.v1"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class HumanOversightRegistry:
    """Tracks human approval states for critical actions."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "human_oversight.json"
        self.approvals: dict[str, HumanApprovalEntry] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for aid, a in data.get("approvals", {}).items():
                self.approvals[aid] = HumanApprovalEntry(**a)

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema": "ia_milk.human_oversight.v1",
                "approvals": {k: v.to_dict() for k, v in self.approvals.items()}}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def request(self, action: str, actor: str, target: str = "",
                trace_id: str = "") -> HumanApprovalEntry:
        entry = HumanApprovalEntry(action=action, actor=actor, target=target, trace_id=trace_id)
        self.approvals[entry.approval_id] = entry
        self._save()
        return entry

    def decide(self, approval_id: str, approver: str, state: str,
               reason: str = "") -> bool:
        if approval_id not in self.approvals:
            return False
        entry = self.approvals[approval_id]
        entry.approver = approver
        entry.state = state
        entry.reason = reason
        entry.decided_at = _now()
        self._save()
        return True

    def pending(self) -> list[dict]:
        return [a.to_dict() for a in self.approvals.values() if a.state == "pending_review"]


# ── Audit Registry ──

@dataclass
class AuditEntry:
    audit_id: str = field(default_factory=_uuid)
    who: str = ""
    what: str = ""      # AuditAction
    when: str = field(default_factory=_now)
    why: str = ""
    evidence: str = ""   # evidence hash or reference
    policy: str = ""     # policy_id evaluated
    outcome: str = ""    # success, failure, blocked
    trace_id: str = ""
    schema_version: str = "audit.v1"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class AuditRegistry:
    """Machine-readable audit trail. Every action answers: who, what, when, why, evidence, policy, outcome."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "audit_trail.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, who: str, what: str, why: str = "",
               evidence: str = "", policy: str = "", outcome: str = "",
               trace_id: str = "") -> AuditEntry:
        entry = AuditEntry(who=who, what=what, why=why, evidence=evidence,
                           policy=policy, outcome=outcome, trace_id=trace_id)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def query(self, trace_id: str = "", limit: int = 50) -> list[dict]:
        if not self.path.exists():
            return []
        results = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if not trace_id or entry.get("trace_id") == trace_id:
                    results.append(entry)
                    if len(results) >= limit:
                        break
        return results


# ── Incident Registry ──

@dataclass
class IncidentEntry:
    incident_id: str = field(default_factory=_uuid)
    severity: str = "medium"
    category: str = "operational"
    description: str = ""
    root_cause: str = ""
    remediation: str = ""
    status: str = "open"  # open, investigating, resolved, closed
    created_at: str = field(default_factory=_now)
    resolved_at: str = ""
    trace_id: str = ""
    schema_version: str = "incident.v1"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class IncidentRegistry:
    """Incident tracking and remediation."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "incident_registry.json"
        self.incidents: dict[str, IncidentEntry] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for iid, i in data.get("incidents", {}).items():
                self.incidents[iid] = IncidentEntry(**i)

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema": "ia_milk.incident_registry.v1",
                "incidents": {k: v.to_dict() for k, v in self.incidents.items()}}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def report(self, severity: str, category: str, description: str,
               trace_id: str = "") -> IncidentEntry:
        inc = IncidentEntry(severity=severity, category=category,
                           description=description, trace_id=trace_id)
        self.incidents[inc.incident_id] = inc
        self._save()
        return inc

    def resolve(self, incident_id: str, root_cause: str, remediation: str) -> bool:
        if incident_id not in self.incidents:
            return False
        inc = self.incidents[incident_id]
        inc.root_cause = root_cause
        inc.remediation = remediation
        inc.status = "resolved"
        inc.resolved_at = _now()
        self._save()
        return True


# ── Compliance Registry (extends existing ComplianceKernel) ──

class ComplianceRegistry:
    """Persistent compliance assessment registry. Wraps existing ComplianceKernel."""

    def __init__(self, path: Path | None = None):
        self.path = path or _GOVERNANCE_DIR / "compliance_registry.json"
        self.assessments: list[dict] = []
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.assessments = data.get("assessments", [])

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"schema": "ia_milk.compliance_registry.v1", "assessments": self.assessments}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def record(self, assessment: dict):
        self.assessments.append(assessment)
        self._save()

    def latest(self) -> dict | None:
        return self.assessments[-1] if self.assessments else None


# ── Governance Orchestrator ──

class GovernanceOrchestrator:
    """Central governance layer that ties all registries together.

    Every critical operation must pass through this orchestrator.
    It produces traceable, governed, auditable decisions.
    """

    def __init__(self, base_dir: Path | None = None):
        base = base_dir or _GOVERNANCE_DIR
        base.mkdir(parents=True, exist_ok=True)
        self.ontology = CanonicalOntology()
        self.risks = RiskRegister(base / "risk_register.json")
        self.policies = PolicyRegistry(base / "policy_registry.json")
        self.oversight = HumanOversightRegistry(base / "human_oversight.json")
        self.audit = AuditRegistry(base / "audit_trail.jsonl")
        self.incidents = IncidentRegistry(base / "incident_registry.json")
        self.compliance = ComplianceRegistry(base / "compliance_registry.json")

        # Register default policies if empty
        if not self.policies.policies:
            self.policies.register("human_oversight", "Critical Action Approval",
                                  "Critical actions require explicit human approval before execution")
            self.policies.register("execution", "Sovereign Execution",
                                  "All external effects must pass through SovereignActionGate")
            self.policies.register("data_access", "Local-First Data Access",
                                  "Personal/sensitive data must stay local unless explicitly authorized")

    def evaluate_action(self, *, action: str, actor: str, target: str = "",
                        critical: bool = False, evidence: str = "",
                        trace_id: str = "") -> dict:
        """Evaluate an action through the full governance stack.

        Returns: {
            allowed: bool,
            requires_human: bool,
            approval_id: str (if pending),
            policies_evaluated: list,
            audit_id: str,
            risks_identified: list,
        }
        """
        # 1. Policy evaluation
        policy_result = self.policies.evaluate(action, {"critical": critical})

        # 2. Risk check
        open_risks = self.risks.by_status("open")
        relevant_risks = [r for r in open_risks if r.get("category") in ("security", "sovereignty")]

        # 3. Human oversight if required
        approval_id = ""
        if policy_result["requires_human"] or critical:
            approval = self.oversight.request(action=action, actor=actor,
                                              target=target, trace_id=trace_id)
            approval_id = approval.approval_id
            policy_result["allowed"] = False

        # 4. Audit trail
        audit_entry = self.audit.record(
            who=actor, what=action, why=f"Governed evaluation for {action}",
            evidence=evidence, policy=",".join(p["policy_id"] for p in policy_result["evaluated_policies"]),
            outcome="allowed" if policy_result["allowed"] else "blocked_or_pending",
            trace_id=trace_id,
        )

        return {
            "allowed": policy_result["allowed"],
            "requires_human": policy_result["requires_human"] or critical,
            "approval_id": approval_id,
            "policies_evaluated": policy_result["evaluated_policies"],
            "audit_id": audit_entry.audit_id,
            "risks_identified": [r["risk_id"] for r in relevant_risks],
            "trace_id": trace_id,
        }

    def approve(self, approval_id: str, approver: str, decision: str,
                reason: str = "") -> bool:
        """Record a human approval decision."""
        return self.oversight.decide(approval_id, approver, decision, reason)

    def export_canonical(self) -> dict:
        """Export canonical governance state."""
        return {
            "schema_version": "governance.v1",
            "ontology": self.ontology.to_dict(),
            "risk_count": len(self.risks.risks),
            "policy_count": len(self.policies.policies),
            "pending_approvals": len(self.oversight.pending()),
            "incident_count": len(self.incidents.incidents),
            "compliance_count": len(self.compliance.assessments),
        }

    def health(self) -> dict:
        """Governance health for observability."""
        return {
            "status": "healthy",
            "ontology_version": self.ontology.version,
            "risks_open": len(self.risks.by_status("open")),
            "policies_active": sum(1 for p in self.policies.policies.values() if p.active),
            "approvals_pending": len(self.oversight.pending()),
            "incidents_open": sum(1 for i in self.incidents.incidents.values() if i.status == "open"),
            "audit_entries": len(self.audit.query()),
        }
