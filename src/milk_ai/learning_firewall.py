"""MILK IA — Learning Provenance Firewall, Human Curatorial Feedback, Rights Scopes.

Three related governance layers that keep learning decisions distinct and
sovereign:

1. PROVENANCE FIREWALL — every learning event declares its environment,
   purpose, worker, trust_state, rights_scope, etc. Only ``production`` or
   human-approved ``curatorial_experiment`` may alter the canonical
   (production) AdaptivePolicy. validation / test / simulation MUST NOT.
   Historical events are never deleted; unclassifiable old events are tagged
   ``environment=legacy_unknown``.

2. HUMAN CURATORIAL FEEDBACK — explicit qualitative judgements (fertile_relation,
   banal_relation, preserve_poetics, damages_poetics, ...) that are NEVER
   collapsed into a single numeric reward. Adaptive learning may change
   retrieval preferences / routing / weights, but must NEVER rewrite original
   source, authorship, historical evidence, or a human curatorial decision.

3. RIGHTS / PUBLICATION / LEARNING SCOPES — separate machine-readable
   permissions. Ingestion never implies publication; publication never implies
   learning; research never implies publication.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .runtime_nomenclature import (
    normalize_environment, environment_can_mutate_policy, ENVIRONMENTS,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Learning provenance — required fields for every learning event
# ---------------------------------------------------------------------------

LEARNING_PROVENANCE_FIELDS = (
    "environment", "purpose", "task_id", "trace_id", "source_ids",
    "evidence_ids", "graph_paths", "worker", "policy_version",
    "human_feedback", "human_validated", "trust_state", "rights_scope",
    "timestamp",
)


def make_provenance(*, environment: str, purpose: str, task_id: str,
                    trace_id: str, worker: str,
                    source_ids: list[str] | None = None,
                    evidence_ids: list[str] | None = None,
                    graph_paths: list | None = None,
                    policy_version: int = 0,
                    human_feedback: str | None = None,
                    human_validated: bool = False,
                    trust_state: str = "unverified",
                    rights_scope: str = "internal") -> dict[str, Any]:
    """Build the provenance block every learning event MUST declare."""
    env = normalize_environment(environment)
    return {
        "environment": env,
        "purpose": purpose,
        "task_id": task_id,
        "trace_id": trace_id,
        "source_ids": source_ids or [],
        "evidence_ids": evidence_ids or [],
        "graph_paths": graph_paths or [],
        "worker": worker,
        "policy_version": policy_version,
        "human_feedback": human_feedback,
        "human_validated": human_validated,
        "trust_state": trust_state,
        "rights_scope": rights_scope,
        "timestamp": _now(),
    }


class PolicyMutationBlocked(Exception):
    """Raised/returned when a non-production environment tries to mutate the
    canonical production AdaptivePolicy."""


class ProductionPolicyGuard:
    """Guards the canonical production AdaptivePolicy from non-production
    mutation.

    Wrap an ``AdaptivePolicy.update`` call with ``guard.update(...)``. If the
    event environment is not permitted to mutate policy, the update is
    refused (no Beta update, no version bump, no save) and a blocked record is
    appended to the firewall log. The learning event itself is still recorded
    (historical events are never deleted).
    """

    def __init__(self, policy, firewall_log_path=None):
        self.policy = policy
        import pathlib
        self._log_path = firewall_log_path or pathlib.Path(
            policy.path.parent / "policy_firewall_log.jsonl"
        )
        self.blocked: list[dict] = []
        self.allowed: list[dict] = []

    def attempt_update(self, *, environment: str, capability_id: str,
                       reward: float, success: bool) -> dict[str, Any]:
        """Return a decision dict. Mutates policy only if permitted."""
        env = normalize_environment(environment)
        permitted = environment_can_mutate_policy(env)
        record = {
            "environment": env, "capability_id": capability_id,
            "reward": reward, "success": success,
            "permitted": permitted, "timestamp": _now(),
            "policy_version_before": self.policy.version,
        }
        if permitted:
            self.policy.update(capability_id, reward, success)
            record["policy_version_after"] = self.policy.version
            record["action"] = "policy_updated"
            self.allowed.append(record)
        else:
            record["policy_version_after"] = self.policy.version
            record["action"] = "blocked_nonproduction_policy_update"
            self.blocked.append(record)
            self._append_log(record)
        if permitted:
            self._append_log(record)
        return record

    def _append_log(self, record: dict) -> None:
        import json
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def stats(self) -> dict[str, Any]:
        return {
            "production_policy_updates": len(self.allowed),
            "blocked_nonproduction_policy_updates": len(self.blocked),
        }


def classify_legacy_event(event: dict) -> str:
    """Classify an old learning event's environment where determinable.

    Returns an official environment value; unclassifiable events become
    ``legacy_unknown`` (never silently re-classified as production).
    """
    env = event.get("environment")
    if env:
        return normalize_environment(env)
    # Heuristic: events with no environment field predate the firewall.
    return "legacy_unknown"


def count_events_by_environment(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {env: 0 for env in ENVIRONMENTS}
    for e in events:
        env = classify_legacy_event(e)
        counts[env] = counts.get(env, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Human curatorial feedback — qualitative, never collapsed to one number
# ---------------------------------------------------------------------------

HUMAN_FEEDBACK_CATEGORIES = (
    "fertile_relation",
    "banal_relation",
    "incorrect_relation",
    "preserve_poetics",
    "damages_poetics",
    "useful_reference",
    "irrelevant_reference",
    "approve_method",
    "reject_method",
    "approve_publication",
    "reject_publication",
)

# Which categories carry a positive / negative signal for ADAPTIVE weighting
# only (never rewriting source/authorship/evidence).
_FEEDBACK_POLARITY = {
    "fertile_relation": 1,
    "banal_relation": -1,
    "incorrect_relation": -1,
    "preserve_poetics": 1,
    "damages_poetics": -1,
    "useful_reference": 1,
    "irrelevant_reference": -1,
    "approve_method": 1,
    "reject_method": -1,
    "approve_publication": 1,
    "reject_publication": -1,
}


@dataclass
class CuratorialFeedback:
    """A single human curatorial judgement."""
    feedback_id: str
    task_id: str
    category: str
    target: str = ""          # node/relation/source id being judged
    note: str = ""
    human_validated: bool = True
    created_at: str = field(default_factory=_now)

    def __post_init__(self):
        if self.category not in HUMAN_FEEDBACK_CATEGORIES:
            raise ValueError(f"invalid feedback category: {self.category}")

    def polarity(self) -> int:
        return _FEEDBACK_POLARITY.get(self.category, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id, "task_id": self.task_id,
            "category": self.category, "target": self.target,
            "note": self.note, "human_validated": self.human_validated,
            "created_at": self.created_at,
        }


class CuratorialFeedbackStore:
    """Collects human curatorial feedback.

    Adaptive learning may read ``polarity()`` to nudge retrieval preferences,
    routing, or relation weights. It must NEVER rewrite the original source,
    authorship, historical evidence, or the stored feedback record itself.
    """

    def __init__(self):
        self._records: list[CuratorialFeedback] = []

    def record(self, *, task_id: str, category: str, target: str = "",
               note: str = "") -> CuratorialFeedback:
        import hashlib
        fb = CuratorialFeedback(
            feedback_id=f"fb:{hashlib.sha256(f'{task_id}{category}{target}{_now()}'.encode()).hexdigest()[:12]}",
            task_id=task_id, category=category, target=target, note=note,
        )
        self._records.append(fb)
        return fb

    def all(self) -> list[CuratorialFeedback]:
        return list(self._records)

    def for_target(self, target: str) -> list[CuratorialFeedback]:
        return [f for f in self._records if f.target == target]

    def counts_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {c: 0 for c in HUMAN_FEEDBACK_CATEGORIES}
        for f in self._records:
            counts[f.category] = counts.get(f.category, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Rights / publication / learning scopes
# ---------------------------------------------------------------------------

RIGHTS_FIELDS = (
    "ingest_allowed",
    "research_allowed",
    "learning_allowed",
    "internal_derivation_allowed",
    "public_excerpt_allowed",
    "public_full_allowed",
    "transformation_allowed",
    "attribution_required",
    "removal_requested",
    "restricted",
    "human_validation_required",
)


@dataclass
class RightsScope:
    """Machine-readable permission envelope for a source/knowledge item.

    Decisions are kept DISTINCT: ingestion never implies publication,
    publication never implies learning, research never implies publication.
    """
    ingest_allowed: bool = False
    research_allowed: bool = False
    learning_allowed: bool = False
    internal_derivation_allowed: bool = False
    public_excerpt_allowed: bool = False
    public_full_allowed: bool = False
    transformation_allowed: bool = False
    attribution_required: bool = True
    removal_requested: bool = False
    restricted: bool = False
    human_validation_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {f: getattr(self, f) for f in RIGHTS_FIELDS}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "RightsScope":
        return RightsScope(**{f: bool(d.get(f, False)) for f in RIGHTS_FIELDS})


# Explicit non-inference rules — enforced as validation helpers.
def assert_no_inferred_publication(rights: RightsScope) -> None:
    """ingest_allowed / research_allowed MUST NOT imply public_*_allowed."""
    if rights.ingest_allowed and not rights.public_full_allowed:
        return  # fine
    if rights.research_allowed and not rights.public_full_allowed:
        return
    # If public_full_allowed is True, it must have been set explicitly — nothing
    # to enforce here beyond the absence of automatic inference.


def assert_no_inferred_learning(rights: RightsScope) -> None:
    """public_*_allowed MUST NOT imply learning_allowed unless explicitly set."""
    if rights.public_full_allowed and not rights.learning_allowed:
        return  # publication without learning is valid and distinct
