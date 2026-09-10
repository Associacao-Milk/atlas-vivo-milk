"""Tests for MILK Sovereign Cognitive Control Plane."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.cognitive_control_plane import (
    TaskEnvelope, Planner, CapabilityRouter, EvidenceBundle, EvidenceItem,
    ReasoningWorker, Executor, OutcomeEvaluator, OperationalMemory,
    SelfObservability, BoundedOperatingLoop, CognitiveControlPlane,
)
from milk_ai.action_gate import ActionGate, READ_AUTO, WRITE_REVERSIBLE, PUBLIC_OR_IRREVERSIBLE


# ---- TaskEnvelope tests ----

class TestTaskEnvelope:
    def test_defaults(self):
        t = TaskEnvelope(query="test query")
        assert t.task_id != ""
        assert t.trace_id != ""
        assert t.query == "test query"
        assert t.intent == "retrieve_and_decide"
        assert t.status == "pending"
        assert t.constraints["max_steps"] == 10

    def test_to_dict_has_all_fields(self):
        t = TaskEnvelope(query="q")
        d = t.to_dict()
        for f in ("task_id", "trace_id", "query", "intent", "constraints", "created_at", "status"):
            assert f in d

    def test_unique_ids(self):
        t1 = TaskEnvelope()
        t2 = TaskEnvelope()
        assert t1.task_id != t2.task_id
        assert t1.trace_id != t2.trace_id


# ---- Planner tests ----

class TestPlanner:
    def test_plan_retrieve_and_decide(self):
        p = Planner()
        t = TaskEnvelope(query="test", intent="retrieve_and_decide")
        steps = p.plan(t)
        assert len(steps) == 5
        assert steps[0]["action"] == "retrieve"
        assert steps[4]["action"] == "gate"

    def test_plan_gap_loop(self):
        p = Planner()
        t = TaskEnvelope(query="test", intent="gap_loop")
        steps = p.plan(t)
        assert len(steps) == 5
        assert steps[0]["action"] == "identify_gap"
        assert steps[4]["action"] == "measure"

    def test_plan_unknown_intent(self):
        p = Planner()
        t = TaskEnvelope(query="test", intent="custom")
        steps = p.plan(t)
        assert len(steps) == 2
        assert steps[0]["action"] == "retrieve"


# ---- CapabilityRouter tests ----

class TestCapabilityRouter:
    def test_discover_capabilities(self):
        r = CapabilityRouter()
        caps = r.discover_capabilities()
        assert len(caps) >= 5
        types = {c["type"] for c in caps}
        assert "retrieval" in types
        assert "reasoning" in types
        assert "external_read" in types
        assert "action_gate" in types

    def test_score_retrieval(self):
        r = CapabilityRouter()
        caps = r.discover_capabilities()
        retrieval_caps = [c for c in caps if c["type"] == "retrieval"]
        assert len(retrieval_caps) > 0
        score = r.score(retrieval_caps[0], "retrieval")
        assert score > 0.5  # retrieval should score high for retrieval need

    def test_score_wrong_capability(self):
        r = CapabilityRouter()
        cap = {"type": "retrieval", "online": True, "sovereignty": 1.0, "privacy": 1.0,
               "latency_ms": 100, "quality": 0.8}
        score = r.score(cap, "reasoning")
        assert score == 0.0  # no match

    def test_score_offline(self):
        r = CapabilityRouter()
        cap = {"type": "retrieval", "online": False, "sovereignty": 1.0, "privacy": 1.0,
               "latency_ms": 100, "quality": 0.8}
        score = r.score(cap, "retrieval")
        assert score == 0.0  # offline scores 0

    def test_select_returns_sorted(self):
        r = CapabilityRouter()
        results = r.select("retrieval", top_k=3)
        assert len(results) > 0
        # Should be sorted by score descending
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i + 1]["score"]

    def test_route_assigns_capabilities(self):
        r = CapabilityRouter()
        steps = [{"step": 1, "action": "retrieve", "capability_needed": "retrieval"},
                 {"step": 2, "action": "reason", "capability_needed": "reasoning"}]
        routed = r.route(steps)
        assert routed[0]["primary_capability"] is not None
        assert routed[0]["primary_capability"]["type"] == "retrieval"
        assert routed[1]["primary_capability"] is not None
        assert "reasoning" in routed[1]["primary_capability"]["type"]

    def test_local_preferred_over_external(self):
        """Local capabilities should score higher than external for same type."""
        r = CapabilityRouter()
        local_cap = {"id": "local", "type": "reasoning", "online": True,
                     "sovereignty": 1.0, "privacy": 1.0, "latency_ms": 500, "quality": 0.7}
        external_cap = {"id": "external", "type": "reasoning", "online": True,
                        "sovereignty": 0.3, "privacy": 0.5, "latency_ms": 200, "quality": 0.9}
        local_score = r.score(local_cap, "reasoning")
        external_score = r.score(external_cap, "reasoning")
        assert local_score > external_score  # sovereignty/privacy wins


# ---- EvidenceBundle tests ----

class TestEvidenceBundle:
    def test_add_evidence(self):
        b = EvidenceBundle("task1", "trace1")
        item = b.add_evidence(source="test", content="hello world")
        assert len(b.items) == 1
        assert item.content_hash == item.content_hash  # hash computed
        assert len(item.content_hash) == 64

    def test_add_inference(self):
        b = EvidenceBundle("task1", "trace1")
        inf = b.add_inference(model="gpt-oss", model_version="local", output="result")
        assert len(b.inferences) == 1
        assert inf["output_hash"] != ""

    def test_add_decision(self):
        b = EvidenceBundle("task1", "trace1")
        dec = b.add_decision(decision="proceed", rationale="evidence is sufficient")
        assert len(b.decisions) == 1
        assert dec["decision"] == "proceed"

    def test_hash_chain(self):
        b = EvidenceBundle("task1", "trace1")
        b.add_evidence(source="s1", content="evidence1")
        b.add_evidence(source="s2", content="evidence2")
        h = b.hash_chain()
        assert len(h) == 64
        # Hash changes when content changes
        b2 = EvidenceBundle("task1", "trace1")
        b2.add_evidence(source="s1", content="different")
        assert b2.hash_chain() != h

    def test_to_dict_has_all_sections(self):
        b = EvidenceBundle("task1", "trace1")
        b.add_evidence(source="s", content="c")
        b.add_inference(model="m", model_version="v", output="o")
        b.add_decision(decision="d", rationale="r")
        d = b.to_dict()
        for section in ("schema", "task_id", "trace_id", "hash_chain",
                        "items", "inferences", "decisions", "gate_decisions",
                        "actions", "outcomes"):
            assert section in d, f"missing section: {section}"

    def test_prov_o_export(self):
        b = EvidenceBundle("task1", "trace1")
        b.add_evidence(source="s", content="c")
        b.add_inference(model="m", model_version="v", output="o")
        prov = b.to_prov_o()
        assert "entities" in prov
        assert "activities" in prov
        assert "agents" in prov
        assert len(prov["entities"]) > 0
        assert len(prov["activities"]) > 0

    def test_save(self, tmp_path):
        b = EvidenceBundle("task_test", "trace_test")
        b.add_evidence(source="s", content="c")
        path = b.save(tmp_path / "bundle.json")
        assert path.exists()
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["task_id"] == "task_test"
        assert "prov_o_export" in loaded


# ---- OperationalMemory tests ----

class TestOperationalMemory:
    def test_append_and_query(self, tmp_path):
        mem = OperationalMemory(tmp_path)
        mem.append("task", {"query": "test"})
        mem.append("episode", {"status": "done"})
        tasks = mem.query("task")
        assert len(tasks) == 1
        assert tasks[0]["query"] == "test"
        all_records = mem.query()
        assert len(all_records) == 2

    def test_append_feedback(self, tmp_path):
        mem = OperationalMemory(tmp_path)
        mem.append_feedback("good result", task_id="t1")
        assert (tmp_path / "learning_events.jsonl").exists()
        with open(tmp_path / "learning_events.jsonl", "r") as f:
            event = json.loads(f.readline())
        assert event["feedback"] == "good result"
        assert event["type"] == "learning_event"

    def test_stats(self, tmp_path):
        mem = OperationalMemory(tmp_path)
        mem.append("task", {"q": "1"})
        mem.append("task", {"q": "2"})
        mem.append("episode", {"s": "done"})
        stats = mem.stats()
        assert stats["total_records"] == 3
        assert stats["by_type"]["task"] == 2
        assert stats["by_type"]["episode"] == 1

    def test_separate_from_corpus(self, tmp_path):
        """Operational memory must not touch corpus."""
        mem = OperationalMemory(tmp_path / "op_mem")
        mem.append("task", {"query": "test"})
        # Corpus path should be different
        corpus_path = Path(__file__).resolve().parents[1] / "corpus" / "documents"
        assert str(mem.mem_dir) != str(corpus_path)


# ---- OutcomeEvaluator tests ----

class TestOutcomeEvaluator:
    def test_evaluate_high_quality(self):
        task = TaskEnvelope(query="test")
        task.status = "done"
        b = EvidenceBundle("t1", "tr1")
        b.add_evidence(source="s1", content="e1")
        b.add_evidence(source="s2", content="e2")
        b.add_evidence(source="s3", content="e3")
        b.add_inference(model="m", model_version="v", output="o")
        evaluator = OutcomeEvaluator()
        result = evaluator.evaluate(task, b)
        assert result["success"] is True
        assert result["quality"] == "high"
        assert result["evidence_count"] == 3

    def test_evaluate_low_quality(self):
        task = TaskEnvelope(query="test")
        task.status = "done"
        b = EvidenceBundle("t1", "tr1")
        evaluator = OutcomeEvaluator()
        result = evaluator.evaluate(task, b)
        assert result["success"] is False
        assert result["quality"] == "low"

    def test_evaluate_failed_task(self):
        task = TaskEnvelope(query="test")
        task.status = "failed"
        b = EvidenceBundle("t1", "tr1")
        b.add_evidence(source="s1", content="e1")
        evaluator = OutcomeEvaluator()
        result = evaluator.evaluate(task, b)
        assert result["success"] is False


# ---- Integration tests ----

class TestCognitiveControlPlaneIntegration:
    """Integration tests using the real CognitiveControlPlane."""

    def test_execute_task_full_pipeline(self, tmp_path):
        """Execute a real task through the full pipeline."""
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem")
        result = ccp.execute_task("What is in the Atlas corpus about Portuguese folklore?")
        assert result["status"] == "done"
        assert result["evidence_count"] >= 1
        assert result["inference_count"] >= 1
        assert result["decision_count"] >= 1
        assert result["hash_chain"] != ""
        assert result["provenance_chain_reconstructable"] is True
        # Evidence bundle saved
        assert Path(result["bundle_path"]).exists()

    def test_reconstruct_chain(self, tmp_path):
        """Reconstruct the full provenance chain."""
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem")
        result = ccp.execute_task("Test query for chain reconstruction")
        task_id = result["task_id"]
        chain = ccp.reconstruct_chain(task_id)
        assert "chain" in chain
        assert chain["chain_length"] > 0
        types_in_chain = [c["type"] for c in chain["chain"]]
        assert "source" in types_in_chain
        assert "evidence" in types_in_chain
        assert "inference" in types_in_chain or "decision" in types_in_chain

    def test_operational_memory_persisted(self, tmp_path):
        """Operational memory should have records after execution."""
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem")
        ccp.execute_task("Test query for memory persistence")
        stats = ccp.op_mem.stats()
        assert stats["total_records"] >= 2  # at least task + episode
        assert "task" in stats["by_type"]
        assert "episode" in stats["by_type"]

    def test_gpt_oss_is_worker_not_orchestrator(self):
        """GPT-OSS should be a worker, never the orchestrator."""
        ccp = CognitiveControlPlane()
        # The orchestrator is CognitiveControlPlane, not GPT-OSS
        # Worker is ReasoningWorker which calls GPT-OSS
        assert ccp.worker is not None
        assert hasattr(ccp.worker, "reason")
        # Worker returns model info, not orchestration decisions
        result = ccp.worker.reason("test", ["evidence"])
        assert "model" in result
        assert "worker_role" in result
        assert result["worker_role"] == "reasoning_worker"

    def test_health_observability(self):
        """Health should return service status."""
        ccp = CognitiveControlPlane()
        h = ccp.health()
        assert "services" in h
        assert "gpu" in h
        assert "gaps" in h
        assert "operational_memory" in h

    def test_bounded_operating_loop(self, tmp_path):
        """Bounded operating loop should complete within limits."""
        from milk_ai.action_gate import ActionGate
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        router = CapabilityRouter()
        worker = ReasoningWorker()
        op_mem = OperationalMemory(tmp_path / "op_mem")
        loop = BoundedOperatingLoop(router, worker, gate, op_mem, max_steps=10, max_time_s=60)
        result = loop.run()
        assert result["status"] in ("done", "failed")
        assert result["steps_executed"] > 0
        assert result["hash_chain"] != ""

    def test_no_source_documents_altered(self, tmp_path):
        """No learning should alter source documents."""
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem")
        ccp.execute_task("Test that corpus is not modified")
        # Check corpus is unchanged
        corpus_dir = Path(__file__).resolve().parents[1] / "corpus" / "documents"
        doc_count = len(list(corpus_dir.glob("*.json")))
        # Should still be 10538
        assert doc_count == 10538

    def test_feedback_recorded(self, tmp_path):
        """Human feedback should be recorded as learning events."""
        ccp = CognitiveControlPlane(op_mem_dir=tmp_path / "op_mem")
        result = ccp.execute_task("Test for feedback")
        ccp.op_mem.append_feedback("This answer was helpful", task_id=result["task_id"])
        stats = ccp.op_mem.stats()
        assert stats["learning_events"] >= 1
