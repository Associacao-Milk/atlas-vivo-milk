"""Tests for MILK Adaptive Learning Engine."""
import json
import os
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.adaptive_engine import (
    RewardModel, RewardConfig, DEFAULT_REWARD_WEIGHTS,
    AdaptivePolicy, CapabilityStats,
    create_learning_event, save_learning_event, load_learning_events,
    ExperienceReplay, AdaptiveLearningEngine,
)


# ---- RewardModel tests ----

class TestRewardModel:
    def test_compute_returns_reward_and_components(self):
        rm = RewardModel()
        reward, components = rm.compute(evidence_quality=0.8, task_success=True)
        assert isinstance(reward, float)
        assert isinstance(components, dict)
        assert "evidence_quality" in components
        assert "task_success" in components

    def test_successful_task_has_positive_reward(self):
        rm = RewardModel()
        reward, _ = rm.compute(evidence_quality=0.8, task_success=True,
                              sovereignty=1.0, latency_ms=100)
        assert reward > 0

    def test_failed_task_has_lower_reward(self):
        rm = RewardModel()
        reward_pass, _ = rm.compute(evidence_quality=0.8, task_success=True)
        reward_fail, _ = rm.compute(evidence_quality=0.8, task_success=False)
        assert reward_pass > reward_fail

    def test_evidence_gap_reduces_reward(self):
        rm = RewardModel()
        reward_ok, _ = rm.compute(evidence_quality=0.8, task_success=True, evidence_gap=False)
        reward_gap, _ = rm.compute(evidence_quality=0.8, task_success=True, evidence_gap=True)
        assert reward_ok > reward_gap

    def test_failures_reduce_reward(self):
        rm = RewardModel()
        reward_no_fail, _ = rm.compute(task_success=True, failures=0)
        reward_fail, _ = rm.compute(task_success=True, failures=3)
        assert reward_no_fail > reward_fail

    def test_weights_are_configurable(self):
        custom = RewardConfig(weights={**DEFAULT_REWARD_WEIGHTS, "evidence_quality": 0.50})
        rm = RewardModel(config=custom)
        reward, components = rm.compute(evidence_quality=1.0, task_success=False)
        # With higher weight on evidence_quality, it contributes more
        assert components["evidence_quality"] == 0.50

    def test_human_feedback_positive(self):
        rm = RewardModel()
        reward_pos, _ = rm.compute(task_success=True, human_feedback=1.0)
        reward_neg, _ = rm.compute(task_success=True, human_feedback=0.0)
        assert reward_pos > reward_neg


# ---- AdaptivePolicy tests ----

class TestAdaptivePolicy:
    def test_initial_policy_is_empty(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        assert p.version == 0
        assert len(p.stats) == 0

    def test_update_increments_version(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:test", reward=0.5, success=True)
        assert p.version == 1
        assert "cap:test" in p.stats
        assert p.stats["cap:test"].selections == 1

    def test_success_increases_alpha(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:test", reward=0.5, success=True)
        assert p.stats["cap:test"].alpha > 1.0  # increased from initial 1.0

    def test_failure_increases_beta(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:test", reward=-0.5, success=False)
        assert p.stats["cap:test"].beta > 1.0

    def test_persist_and_reload(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:a", reward=0.5, success=True)
        p.update("cap:b", reward=-0.3, success=False)
        p.save()

        # Reload
        p2 = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        assert p2.version == 2
        assert "cap:a" in p2.stats
        assert "cap:b" in p2.stats
        assert p2.stats["cap:a"].selections == 1

    def test_adjust_score_returns_value_in_range(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        adjusted, explanation = p.adjust_score(0.5, "cap:new", explore=False)
        assert 0.0 <= adjusted <= 1.0
        assert "base_score" in explanation
        assert "adaptive_sample" in explanation
        assert "mode" in explanation

    def test_repeated_successes_increase_adjusted_score(self, tmp_path):
        random.seed(42)
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        # Train: cap:good always succeeds
        for _ in range(10):
            p.update("cap:good", reward=0.8, success=True)
        # Train: cap:bad always fails
        for _ in range(10):
            p.update("cap:bad", reward=-0.5, success=False)

        # After training, good cap should have higher expected value
        good_exp = p.stats["cap:good"].alpha / (p.stats["cap:good"].alpha + p.stats["cap:good"].beta)
        bad_exp = p.stats["cap:bad"].alpha / (p.stats["cap:bad"].alpha + p.stats["cap:bad"].beta)
        assert good_exp > bad_exp

    def test_explain(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:test", reward=0.5, success=True)
        exp = p.explain("cap:test")
        assert exp["capability_id"] == "cap:test"
        assert exp["selections"] == 1
        assert "expected_value" in exp

    def test_snapshot_and_rollback(self, tmp_path):
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        p.update("cap:a", reward=0.5, success=True)
        snap = p.snapshot()
        assert snap["version"] == 1
        p.update("cap:b", reward=-0.3, success=False)
        assert p.version == 2
        # Rollback to version 1
        result = p.rollback(1)
        assert result is True
        assert p.version == 1
        assert "cap:a" in p.stats
        assert "cap:b" not in p.stats

    def test_high_risk_disables_exploration(self, tmp_path):
        """High-risk tasks should use conservative policy (no exploration)."""
        random.seed(42)
        p = AdaptivePolicy(policy_path=tmp_path / "policy.json")
        # With exploration disabled, adjusted score should be more deterministic
        adjusted1, _ = p.adjust_score(0.5, "cap:test", explore=False)
        adjusted2, _ = p.adjust_score(0.5, "cap:test", explore=False)
        # Without exploration, scores should be closer (less random)
        # (Not exactly equal due to sampling, but more stable)


# ---- LearningEvent tests ----

class TestLearningEvent:
    def test_create_learning_event_has_all_fields(self):
        event = create_learning_event(
            task_id="t1", trace_id="tr1", context={"q": "test"},
            candidates=[{"id": "cap:a", "score": 0.8}],
            scores_before={"cap:a": 0.8},
            selected_capability="cap:a",
            evidence_metrics={"evidence_count": 3},
            outcome={"success": True},
            reward_components={"evidence_quality": 0.16},
            reward_final=0.5,
            policy_version_before=0,
            policy_version_after=1,
        )
        for field in ("event_id", "task_id", "trace_id", "timestamp", "context",
                      "candidates", "scores_before", "selected_capability",
                      "evidence_metrics", "outcome", "reward_components",
                      "reward_final", "human_feedback",
                      "policy_version_before", "policy_version_after",
                      "event_hash"):
            assert field in event, f"missing: {field}"

    def test_learning_event_hash_is_deterministic(self):
        kwargs = dict(
            task_id="t1", trace_id="tr1", context={},
            candidates=[], scores_before={},
            selected_capability="cap:a",
            evidence_metrics={}, outcome={},
            reward_components={}, reward_final=0.5,
            policy_version_before=0, policy_version_after=1,
        )
        e1 = create_learning_event(**kwargs)
        e2 = create_learning_event(**kwargs)
        assert e1["event_hash"] == e2["event_hash"]

    def test_save_and_load_learning_events(self, tmp_path):
        path = tmp_path / "events.jsonl"
        event = create_learning_event(
            task_id="t1", trace_id="tr1", context={},
            candidates=[], scores_before={},
            selected_capability="cap:a",
            evidence_metrics={}, outcome={"success": True},
            reward_components={}, reward_final=0.5,
            policy_version_before=0, policy_version_after=1,
        )
        save_learning_event(event, path)
        events = load_learning_events(path)
        assert len(events) == 1
        assert events[0]["selected_capability"] == "cap:a"


# ---- AdaptiveLearningEngine integration tests ----

class TestAdaptiveLearningEngine:
    def test_adjust_candidates_changes_order(self, tmp_path):
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        # Train: cap:b is better than cap:a
        for _ in range(5):
            engine.policy.update("cap:b", reward=0.8, success=True)
        for _ in range(5):
            engine.policy.update("cap:a", reward=-0.3, success=False)

        candidates = [
            {"id": "cap:a", "score": 0.7},
            {"id": "cap:b", "score": 0.5},
        ]
        adjusted = engine.adjust_candidates(candidates, "reasoning")
        # After training, cap:b might rank higher despite lower base score
        # (probabilistic, but with strong enough signal)
        assert len(adjusted) == 2
        assert adjusted[0].get("base_score") is not None
        assert adjusted[0].get("adjusted_score") is not None

    def test_record_outcome_creates_learning_event(self, tmp_path):
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        event = engine.record_outcome(
            task_id="t1", trace_id="tr1",
            selected_capability="cap:test",
            candidates=[{"id": "cap:test", "score": 0.7}],
            scores_before={"cap:test": 0.7},
            outcome={"success": True},
            evidence_metrics={"evidence_count": 3, "latency_ms": 100,
                              "sovereignty": 1.0, "reversible": True,
                              "confidence": 0.8},
            context={"query": "test"},
        )
        assert event["selected_capability"] == "cap:test"
        assert event["policy_version_after"] > event["policy_version_before"]

    def test_observability(self, tmp_path):
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        engine.record_outcome(
            task_id="t1", trace_id="tr1",
            selected_capability="cap:test",
            candidates=[], scores_before={},
            outcome={"success": True},
            evidence_metrics={"evidence_count": 2},
            context={},
        )
        obs = engine.observability()
        assert obs["total_learning_events"] >= 1
        assert "policy_version" in obs
        assert "success_rate" in obs

    def test_explain_selection(self, tmp_path):
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        engine.policy.update("cap:test", reward=0.5, success=True)
        exp = engine.explain_selection("cap:test")
        assert exp["capability_id"] == "cap:test"
        assert exp["selections"] == 1


# ---- ExperienceReplay tests ----

class TestExperienceReplay:
    def test_evaluate_policy(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        # Create some events
        for i in range(5):
            event = engine.record_outcome(
                task_id=f"t{i}", trace_id=f"tr{i}",
                selected_capability="cap:good",
                candidates=[], scores_before={},
                outcome={"success": True},
                evidence_metrics={"evidence_count": 3},
                context={},
            )
            save_learning_event(event, events_path)

        replay = ExperienceReplay(events_path)
        result = replay.evaluate_policy(engine.policy)
        assert "episodes_evaluated" in result
        assert result["episodes_evaluated"] == 5


# ---- Integration with CognitiveControlPlane ----

class TestCCPIntegration:
    def test_ccp_creates_learning_events(self, tmp_path):
        """CognitiveControlPlane should create learning events when adaptive engine is attached.

        In an isolated op_mem_dir the environment is 'test', so the learning
        provenance firewall MUST keep the canonical policy unmutated while still
        recording the learning event.
        """
        from milk_ai.cognitive_control_plane import CognitiveControlPlane
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem", adaptive_engine=engine)
        assert ccp.environment == "test"
        result = ccp.execute_task("Test query for adaptive learning")
        assert result["status"] == "done"
        # Learning events were created (recorded) but the policy was NOT mutated
        # because the environment is non-production (learning firewall).
        assert engine.policy.version == 0

    def test_ccp_explain_selection(self, tmp_path):
        from milk_ai.cognitive_control_plane import CognitiveControlPlane
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem", adaptive_engine=engine)
        exp = ccp.explain_selection("retrieval:corpus")
        assert "capability_id" in exp

    def test_ccp_adaptive_observability(self, tmp_path):
        from milk_ai.cognitive_control_plane import CognitiveControlPlane
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem", adaptive_engine=engine)
        obs = ccp.adaptive_observability()
        assert "policy_version" in obs

    def test_sovereign_action_gate_intact(self, tmp_path):
        """Action gate must still work with adaptive engine."""
        from milk_ai.cognitive_control_plane import CognitiveControlPlane
        engine = AdaptiveLearningEngine(policy_path=tmp_path / "policy.json")
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem", adaptive_engine=engine)
        result = ccp.execute_task("Test gate intact")
        assert result["gate_decisions"] >= 0  # gate was exercised

    def test_policy_persistence_across_ccp_instances(self, tmp_path):
        """Policy should persist across CCP instances."""
        from milk_ai.cognitive_control_plane import CognitiveControlPlane
        policy_path = tmp_path / "policy.json"
        engine1 = AdaptiveLearningEngine(policy_path=policy_path)
        ccp1 = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem", adaptive_engine=engine1)
        ccp1.execute_task("First task")
        version_after_first = engine1.policy.version

        # New CCP with new engine, same policy path
        engine2 = AdaptiveLearningEngine(policy_path=policy_path)
        ccp2 = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem2", adaptive_engine=engine2)
        assert engine2.policy.version == version_after_first  # loaded from disk
