"""MILK Adaptive Learning Engine — contextual bandit for routing adaptation.

Integrates into the existing CapabilityRouter. Does NOT replace it — augments
base scores with learned adjustments using Thompson Sampling (Beta distribution
per capability). Policy is persistent, versioned, rollback-able.

No cloud dependency. No model-base training. No corpus modification.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_POLICY_PATH = _ROOT / "state" / "adaptive_policy.json"
_HISTORY_PATH = _ROOT / "state" / "adaptive_policy_history.jsonl"
_LEARNING_EVENTS_PATH = _ROOT / "state" / "operational_memory" / "adaptive_learning_events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return uuid.uuid4().hex


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Reward Model — explicit, auditable, configurable
# ---------------------------------------------------------------------------

DEFAULT_REWARD_WEIGHTS = {
    "evidence_quality": 0.20,
    "task_success": 0.15,
    "human_validation": 0.15,
    "sovereignty_locality": 0.10,
    "efficiency_latency": 0.10,
    "reversibility": 0.05,
    "confidence": 0.10,
    "failures": -0.15,
    "hallucination_evidence_gap": -0.10,
    "excessive_resources": -0.05,
}


@dataclass
class RewardConfig:
    weights: dict = field(default_factory=lambda: dict(DEFAULT_REWARD_WEIGHTS))
    version: str = "reward-v1"

    def to_dict(self) -> dict:
        return {"weights": self.weights, "version": self.version}


class RewardModel:
    """Explicit, non-neural reward model. Components and weights are configurable."""

    def __init__(self, config: RewardConfig | None = None):
        self.config = config or RewardConfig()

    def compute(self, *, evidence_quality: float = 0.0,
                task_success: bool = False,
                human_feedback: float | None = None,
                sovereignty: float = 0.5,
                latency_ms: float = 500,
                reversible: bool = True,
                confidence: float = 0.5,
                failures: int = 0,
                evidence_gap: bool = False,
                resource_usage: float = 0.5,
                **extra) -> tuple[float, dict]:
        """Compute reward and return (reward, components dict)."""
        w = self.config.weights
        components = {}

        components["evidence_quality"] = evidence_quality * w.get("evidence_quality", 0.20)
        components["task_success"] = (1.0 if task_success else 0.0) * w.get("task_success", 0.15)
        hv = human_feedback if human_feedback is not None else 0.5
        components["human_validation"] = hv * w.get("human_validation", 0.15)
        components["sovereignty_locality"] = sovereignty * w.get("sovereignty_locality", 0.10)
        lat_score = max(0, 1.0 - (latency_ms / 2000))
        components["efficiency_latency"] = lat_score * w.get("efficiency_latency", 0.10)
        components["reversibility"] = (1.0 if reversible else 0.0) * w.get("reversibility", 0.05)
        components["confidence"] = confidence * w.get("confidence", 0.10)
        components["failures"] = failures * w.get("failures", -0.15)
        components["hallucination_evidence_gap"] = (-1.0 if evidence_gap else 0.0) * abs(w.get("hallucination_evidence_gap", -0.10))
        components["excessive_resources"] = -(max(0, resource_usage - 0.8)) * abs(w.get("excessive_resources", -0.05))

        reward = sum(components.values())
        return round(reward, 4), components


# ---------------------------------------------------------------------------
# Adaptive Policy — Thompson Sampling with Beta distributions per capability
# ---------------------------------------------------------------------------

@dataclass
class CapabilityStats:
    """Beta distribution parameters for one capability in one context."""
    alpha: float = 1.0  # successes (pseudocount)
    beta: float = 1.0   # failures (pseudocount)
    selections: int = 0
    total_reward: float = 0.0

    def to_dict(self) -> dict:
        return {"alpha": self.alpha, "beta": self.beta,
                "selections": self.selections, "total_reward": self.total_reward}

    @staticmethod
    def from_dict(d: dict) -> "CapabilityStats":
        return CapabilityStats(
            alpha=d.get("alpha", 1.0), beta=d.get("beta", 1.0),
            selections=d.get("selections", 0), total_reward=d.get("total_reward", 0.0),
        )


class AdaptivePolicy:
    """Thompson Sampling policy for capability routing.

    Maintains Beta(alpha, beta) per (capability_id, capability_type) pair.
    Samples from each Beta to get an exploration-aware adjustment.
    Base score from CapabilityRouter is combined with adaptive adjustment.
    """

    def __init__(self, policy_path: Path | None = None):
        self.path = policy_path or _POLICY_PATH
        self.history_path = _HISTORY_PATH
        self.version = 0
        self.stats: dict[str, CapabilityStats] = {}  # key = capability_id
        self.exploration_rate = 0.15  # probability of exploration vs exploitation
        self.adjustment_weight = 0.30  # how much adaptive adjustment affects final score
        self.base_weight = 0.70  # how much base score affects final score
        self._snapshots: list[dict] = []
        self._load()

    def _key(self, capability_id: str) -> str:
        return capability_id

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.version = data.get("version", 0)
            self.exploration_rate = data.get("exploration_rate", 0.15)
            self.adjustment_weight = data.get("adjustment_weight", 0.30)
            self.base_weight = data.get("base_weight", 0.70)
            raw_stats = data.get("stats", {})
            self.stats = {k: CapabilityStats.from_dict(v) for k, v in raw_stats.items()}

    def save(self):
        data = {
            "schema": "ia_milk.adaptive_policy.v1",
            "version": self.version,
            "exploration_rate": self.exploration_rate,
            "adjustment_weight": self.adjustment_weight,
            "base_weight": self.base_weight,
            "updated_at": _now(),
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _sample(self, cap_id: str) -> float:
        """Sample from Beta(alpha, beta) for this capability. Returns value in [0, 1]."""
        stats = self.stats.get(cap_id)
        if stats is None:
            stats = CapabilityStats()
            self.stats[cap_id] = stats
        # Thompson Sampling: sample from Beta distribution
        sample = random.betavariate(max(stats.alpha, 0.01), max(stats.beta, 0.01))
        return sample

    def adjust_score(self, base_score: float, cap_id: str, explore: bool = True) -> tuple[float, dict]:
        """Adjust base score using adaptive policy. Returns (adjusted_score, explanation)."""
        adaptive_sample = self._sample(cap_id)

        if explore and random.random() < self.exploration_rate:
            # Exploration: rely more on the adaptive sample
            adjusted = base_score * self.base_weight + adaptive_sample * (1 - self.base_weight + 0.1)
            mode = "explore"
        else:
            # Exploitation: weighted combination
            adjusted = base_score * self.base_weight + adaptive_sample * self.adjustment_weight
            mode = "exploit"

        adjusted = round(min(1.0, max(0.0, adjusted)), 4)

        stats = self.stats.get(cap_id, CapabilityStats())
        explanation = {
            "base_score": base_score,
            "adaptive_sample": round(adaptive_sample, 4),
            "adjustment_weight": self.adjustment_weight,
            "base_weight": self.base_weight,
            "mode": mode,
            "stats": stats.to_dict(),
            "adjusted_score": adjusted,
        }
        return adjusted, explanation

    def update(self, cap_id: str, reward: float, success: bool):
        """Update policy after observing outcome. reward in [-1, 1]."""
        stats = self.stats.get(cap_id)
        if stats is None:
            stats = CapabilityStats()
            self.stats[cap_id] = stats

        stats.selections += 1
        stats.total_reward += reward

        # Convert reward [-1, 1] to success probability [0, 1]
        # reward > 0 = success, reward < 0 = failure
        # Scale: reward of 0.5 adds 0.5 to alpha, -0.5 adds 0.5 to beta
        if success:
            stats.alpha += max(0.1, reward + 0.5)
        else:
            stats.beta += max(0.1, abs(reward) + 0.5)

        # Also do a soft update: small alpha/beta increment proportional to reward
        if reward > 0:
            stats.alpha += reward * 0.1
        elif reward < 0:
            stats.beta += abs(reward) * 0.1

        self.version += 1
        self.save()

    def snapshot(self) -> dict:
        """Take a versioned snapshot of the current policy."""
        snap = {
            "snapshot_id": _uuid(),
            "version": self.version,
            "timestamp": _now(),
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
            "exploration_rate": self.exploration_rate,
        }
        self._snapshots.append(snap)
        # Append to history
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(snap, ensure_ascii=False) + "\n")
        return snap

    def rollback(self, to_version: int) -> bool:
        """Rollback policy to a previous version by loading from history."""
        if not self.history_path.exists():
            return False
        target = None
        with open(self.history_path, "r", encoding="utf-8") as f:
            for line in f:
                snap = json.loads(line)
                if snap.get("version") == to_version:
                    target = snap
        if target is None:
            return False
        self.version = target["version"]
        self.exploration_rate = target.get("exploration_rate", self.exploration_rate)
        self.stats = {k: CapabilityStats.from_dict(v) for k, v in target.get("stats", {}).items()}
        self.save()
        return True

    def explain(self, cap_id: str) -> dict:
        """Explain why a capability was chosen or not."""
        stats = self.stats.get(cap_id, CapabilityStats())
        avg_reward = stats.total_reward / max(1, stats.selections)
        return {
            "capability_id": cap_id,
            "selections": stats.selections,
            "total_reward": round(stats.total_reward, 4),
            "avg_reward": round(avg_reward, 4),
            "alpha": round(stats.alpha, 2),
            "beta": round(stats.beta, 2),
            "expected_value": round(stats.alpha / (stats.alpha + stats.beta), 4),
            "policy_version": self.version,
        }

    def stats_summary(self) -> dict:
        """Summary statistics for observability."""
        total_selections = sum(s.selections for s in self.stats.values())
        total_reward = sum(s.total_reward for s in self.stats.values())
        avg_reward = total_reward / max(1, total_selections)
        return {
            "policy_version": self.version,
            "total_capabilities_tracked": len(self.stats),
            "total_selections": total_selections,
            "total_reward": round(total_reward, 4),
            "avg_reward": round(avg_reward, 4),
            "exploration_rate": self.exploration_rate,
            "by_capability": {k: v.to_dict() for k, v in self.stats.items()},
        }


# ---------------------------------------------------------------------------
# Learning Event — immutable record of one learning interaction
# ---------------------------------------------------------------------------

def create_learning_event(*, task_id: str, trace_id: str, context: dict,
                          candidates: list[dict], scores_before: dict,
                          selected_capability: str, evidence_metrics: dict,
                          outcome: dict, reward_components: dict, reward_final: float,
                          human_feedback: str | None = None,
                          policy_version_before: int, policy_version_after: int,
                          bundle_hash: str = "",
                          environment: str = "production",
                          purpose: str = "routing_adaptation",
                          worker: str = "",
                          source_ids: list | None = None,
                          evidence_ids: list | None = None,
                          graph_paths: list | None = None,
                          human_validated: bool = False,
                          trust_state: str = "unverified",
                          rights_scope: str = "internal",
                          policy_mutated: bool = True) -> dict:
    """Create an immutable LearningEvent with full learning provenance.

    Every event declares its environment, purpose, worker, trust_state and
    rights_scope (learning provenance firewall, section 8). ``policy_mutated``
    records whether the canonical policy was actually changed — non-production
    environments record the event but must NOT mutate policy.
    """
    from .runtime_nomenclature import normalize_environment
    env = normalize_environment(environment)
    provenance = {
        "environment": env,
        "purpose": purpose,
        "worker": worker,
        "human_feedback": human_feedback,
        "human_validated": human_validated,
        "trust_state": trust_state,
        "rights_scope": rights_scope,
        "source_ids": source_ids or [],
        "evidence_ids": evidence_ids or [],
        "graph_paths": graph_paths or [],
        "policy_mutated": policy_mutated,
    }
    return {
        "event_id": _uuid(),
        "task_id": task_id,
        "trace_id": trace_id,
        "timestamp": _now(),
        "context": context,
        "candidates": candidates,
        "scores_before": scores_before,
        "selected_capability": selected_capability,
        "evidence_metrics": evidence_metrics,
        "outcome": outcome,
        "reward_components": reward_components,
        "reward_final": reward_final,
        "human_feedback": human_feedback,
        "policy_version_before": policy_version_before,
        "policy_version_after": policy_version_after,
        "bundle_hash": bundle_hash,
        "provenance": provenance,
        "event_hash": _sha256(json.dumps({
            "task_id": task_id, "trace_id": trace_id,
            "selected_capability": selected_capability,
            "reward_final": reward_final,
            "policy_version_after": policy_version_after,
            "environment": env,
        }, sort_keys=True)),
    }


def save_learning_event(event: dict, path: Path | None = None):
    """Append a learning event to the JSONL log."""
    p = path or _LEARNING_EVENTS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_learning_events(path: Path | None = None, limit: int = 100) -> list[dict]:
    """Load learning events from JSONL log."""
    p = path or _LEARNING_EVENTS_PATH
    if not p.exists():
        return []
    events = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            events.append(json.loads(line))
            if len(events) >= limit:
                break
    return events


# ---------------------------------------------------------------------------
# Experience Replay — offline evaluation and policy comparison
# ---------------------------------------------------------------------------

class ExperienceReplay:
    """Selects historical episodes for offline evaluation and comparison."""

    def __init__(self, events_path: Path | None = None):
        self.events_path = events_path or _LEARNING_EVENTS_PATH

    def load_episodes(self, limit: int = 50) -> list[dict]:
        return load_learning_events(self.events_path, limit)

    def evaluate_policy(self, policy: AdaptivePolicy, episodes: list[dict] | None = None) -> dict:
        """Evaluate current policy against historical episodes."""
        if episodes is None:
            episodes = self.load_episodes()
        if not episodes:
            return {"error": "no episodes available"}

        total_reward = 0.0
        correct_selections = 0
        for ep in episodes:
            total_reward += ep.get("reward_final", 0.0)
            # Check if policy would make the same selection
            selected = ep.get("selected_capability", "")
            stats = policy.stats.get(selected)
            if stats and stats.alpha > stats.beta:
                correct_selections += 1

        return {
            "episodes_evaluated": len(episodes),
            "avg_reward": round(total_reward / len(episodes), 4),
            "policy_consistency": round(correct_selections / len(episodes), 4),
            "policy_version": policy.version,
        }

    def compare_policies(self, current: AdaptivePolicy, previous_version: int) -> dict:
        """Compare current policy vs a previous version."""
        episodes = self.load_episodes()
        current_eval = self.evaluate_policy(current, episodes)

        # Create a temporary policy at the previous version
        old_policy = AdaptivePolicy()
        old_policy.rollback(previous_version)
        old_eval = self.evaluate_policy(old_policy, episodes)

        return {
            "current_version": current.version,
            "previous_version": previous_version,
            "current_avg_reward": current_eval.get("avg_reward", 0),
            "previous_avg_reward": old_eval.get("avg_reward", 0),
            "delta_reward": round(current_eval.get("avg_reward", 0) - old_eval.get("avg_reward", 0), 4),
            "episodes": len(episodes),
        }


# ---------------------------------------------------------------------------
# Adaptive Learning Engine — orchestrates the full learning loop
# ---------------------------------------------------------------------------

class AdaptiveLearningEngine:
    """Integrates adaptive policy into the Cognitive Control Plane.

    Flow:
    TaskEnvelope → candidates → base scores → adaptive policy → choice
    → execution → EvidenceBundle → OutcomeEvaluator → LearningEvent
    → policy update → OperationalMemory
    """

    def __init__(self, policy_path: Path | None = None):
        self.policy = AdaptivePolicy(policy_path)
        self.reward_model = RewardModel()
        self.experience_replay = ExperienceReplay()

    def adjust_candidates(self, candidates: list[dict], capability_needed: str,
                          task_risk: str = "normal") -> list[dict]:
        """Adjust candidate scores using adaptive policy. Returns sorted list."""
        # High-risk tasks use conservative policy (less exploration)
        explore = task_risk != "high"

        adjusted = []
        for cap in candidates:
            base_score = cap.get("score", 0.0)
            cap_id = cap.get("id", "unknown")
            adj_score, explanation = self.policy.adjust_score(base_score, cap_id, explore=explore)
            adjusted.append({
                **cap,
                "base_score": base_score,
                "adjusted_score": adj_score,
                "adaptive_explanation": explanation,
            })

        adjusted.sort(key=lambda c: c.get("adjusted_score", 0), reverse=True)
        return adjusted

    def record_outcome(self, *, task_id: str, trace_id: str,
                       selected_capability: str, candidates: list[dict],
                       scores_before: dict, outcome: dict,
                       evidence_metrics: dict, context: dict,
                       human_feedback: str | None = None,
                       bundle_hash: str = "",
                       environment: str = "production",
                       worker: str = "",
                       source_ids: list | None = None,
                       evidence_ids: list | None = None,
                       graph_paths: list | None = None) -> dict:
        """Record outcome, compute reward, update policy, create LearningEvent.

        The canonical AdaptivePolicy is mutated ONLY when the event environment
        is permitted (production or human-approved curatorial_experiment).
        validation / test / simulation events are still recorded but do NOT
        alter production learning (learning provenance firewall, section 8).
        """
        from .runtime_nomenclature import environment_can_mutate_policy

        policy_version_before = self.policy.version

        # Compute reward
        evidence_quality = evidence_metrics.get("evidence_count", 0) / 5.0  # normalize to ~[0,1]
        evidence_quality = min(1.0, evidence_quality)
        task_success = outcome.get("success", False)
        latency_ms = evidence_metrics.get("latency_ms", 500)
        sovereignty = evidence_metrics.get("sovereignty", 0.5)
        reversible = evidence_metrics.get("reversible", True)
        confidence = evidence_metrics.get("confidence", 0.5)
        failures = evidence_metrics.get("failures", 0)
        evidence_gap = evidence_metrics.get("evidence_gap", False)
        resource_usage = evidence_metrics.get("resource_usage", 0.5)

        human_val = None
        if human_feedback is not None:
            # Simple mapping: positive -> 1.0, negative -> 0.0, neutral -> 0.5
            human_val = 1.0 if "good" in human_feedback.lower() or "helpful" in human_feedback.lower() else 0.0

        reward, components = self.reward_model.compute(
            evidence_quality=evidence_quality,
            task_success=task_success,
            human_feedback=human_val,
            sovereignty=sovereignty,
            latency_ms=latency_ms,
            reversible=reversible,
            confidence=confidence,
            failures=failures,
            evidence_gap=evidence_gap,
            resource_usage=resource_usage,
        )

        # Update policy ONLY if environment is permitted (learning firewall).
        policy_mutated = environment_can_mutate_policy(environment)
        if policy_mutated:
            self.policy.update(selected_capability, reward, task_success)
        policy_version_after = self.policy.version

        # Create learning event
        event = create_learning_event(
            task_id=task_id, trace_id=trace_id, context=context,
            candidates=candidates, scores_before=scores_before,
            selected_capability=selected_capability, evidence_metrics=evidence_metrics,
            outcome=outcome, reward_components=components, reward_final=reward,
            human_feedback=human_feedback,
            policy_version_before=policy_version_before,
            policy_version_after=policy_version_after,
            bundle_hash=bundle_hash,
            environment=environment, worker=worker,
            source_ids=source_ids, evidence_ids=evidence_ids,
            graph_paths=graph_paths, policy_mutated=policy_mutated,
        )
        save_learning_event(event)

        return event

    def explain_selection(self, cap_id: str) -> dict:
        """Explain why a capability was chosen."""
        return self.policy.explain(cap_id)

    def observability(self) -> dict:
        """Auto-observability for the adaptive learning engine."""
        events = load_learning_events(limit=1000)
        total_events = len(events)
        recent_rewards = [e.get("reward_final", 0) for e in events[-20:]]
        avg_recent_reward = sum(recent_rewards) / max(1, len(recent_rewards))

        # Selections by capability
        selections_by_cap: dict[str, int] = {}
        for e in events:
            cap = e.get("selected_capability", "unknown")
            selections_by_cap[cap] = selections_by_cap.get(cap, 0) + 1

        # Success rate
        successes = sum(1 for e in events if e.get("outcome", {}).get("success", False))
        success_rate = successes / max(1, total_events)

        # Exploration rate (from policy)
        exploration_rate = self.policy.exploration_rate

        return {
            "policy_version": self.policy.version,
            "total_learning_events": total_events,
            "avg_recent_reward": round(avg_recent_reward, 4),
            "success_rate": round(success_rate, 4),
            "selections_by_capability": selections_by_cap,
            "exploration_rate": exploration_rate,
            "policy_stats": self.policy.stats_summary(),
            "reward_config": self.reward_model.config.to_dict(),
        }
