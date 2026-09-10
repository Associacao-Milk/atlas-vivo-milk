"""MILK Sovereign Cognitive Control Plane — vertical slice.

Pipeline: TaskEnvelope -> Planner -> Router -> Retrieval/Adapters ->
EvidenceBundle -> Reasoning Worker -> SovereignActionGate -> Executor ->
OutcomeEvaluator -> OperationalMemory.

Local-first, vendor-independent. GPT-OSS is a worker, never the orchestrator.
No learning alters source documents. Operational memory is separate from corpus.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Paths and helpers
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[2]
_OP_MEM_DIR = _ROOT / "state" / "operational_memory"
_EVIDENCE_DIR = _ROOT / "state" / "evidence_bundles"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _uuid() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# TaskEnvelope
# ---------------------------------------------------------------------------

@dataclass
class TaskEnvelope:
    """A unit of work entering the cognitive control plane."""
    task_id: str = field(default_factory=_uuid)
    trace_id: str = field(default_factory=_uuid)
    query: str = ""
    intent: str = "retrieve_and_decide"  # retrieve, decide, audit, gap_loop
    constraints: dict = field(default_factory=lambda: {
        "max_steps": 10,
        "max_time_s": 60,
        "max_retrieval_results": 10,
        "sovereignty_required": True,
        "local_preferred": True,
    })
    created_at: str = field(default_factory=_now)
    status: str = "pending"  # pending, planning, routing, executing, evaluating, done, failed

    def to_dict(self) -> dict:
        return {"task_id": self.task_id, "trace_id": self.trace_id,
                "query": self.query, "intent": self.intent,
                "constraints": self.constraints, "created_at": self.created_at,
                "status": self.status}


# ---------------------------------------------------------------------------
# Planner — decomposes task into steps
# ---------------------------------------------------------------------------

class Planner:
    """Decomposes a TaskEnvelope into a plan of steps."""

    def plan(self, task: TaskEnvelope) -> list[dict]:
        """Return ordered steps for the router to execute."""
        steps = []
        if task.intent == "retrieve_and_decide":
            steps = [
                {"step": 1, "action": "retrieve", "description": f"Retrieve evidence for: {task.query[:80]}",
                 "capability_needed": "retrieval", "fallback": "external_search"},
                {"step": 2, "action": "gather_external", "description": "Gather external evidence from adapters",
                 "capability_needed": "external_read", "fallback": "skip"},
                {"step": 3, "action": "reason", "description": "Synthesize evidence with local worker",
                 "capability_needed": "reasoning", "fallback": "heuristic"},
                {"step": 4, "action": "decide", "description": "Make decision with EvidenceBundle",
                 "capability_needed": "decision", "fallback": "defer"},
                {"step": 5, "action": "gate", "description": "Pass decision through Sovereign Action Gate",
                 "capability_needed": "action_gate", "fallback": "block"},
            ]
        elif task.intent == "gap_loop":
            steps = [
                {"step": 1, "action": "identify_gap", "description": "Identify a gap to address",
                 "capability_needed": "gap_engine", "fallback": "skip"},
                {"step": 2, "action": "research", "description": "Research and cross-reference evidence",
                 "capability_needed": "retrieval+external", "fallback": "local_only"},
                {"step": 3, "action": "hypothesize", "description": "Form hypothesis from evidence",
                 "capability_needed": "reasoning", "fallback": "heuristic"},
                {"step": 4, "action": "propose", "description": "Propose reversible action",
                 "capability_needed": "action_gate", "fallback": "block"},
                {"step": 5, "action": "measure", "description": "Measure outcome",
                 "capability_needed": "evaluation", "fallback": "skip"},
            ]
        else:
            steps = [
                {"step": 1, "action": "retrieve", "description": "Retrieve evidence",
                 "capability_needed": "retrieval", "fallback": "skip"},
                {"step": 2, "action": "reason", "description": "Reason with local worker",
                 "capability_needed": "reasoning", "fallback": "heuristic"},
            ]
        return steps


# ---------------------------------------------------------------------------
# Capability/Tool/Source Router
# ---------------------------------------------------------------------------

class CapabilityRouter:
    """Discovers capabilities from Resource Registry and selects dynamically.

    Scoring: capability_match (0-1), availability/health (0-1),
    sovereignty/locality (0-1), privacy (0-1), quality_expected (0-1),
    evidence_available (0-1), latency_ms (inverted).
    """

    def __init__(self, registry_path: Path | None = None, adaptive_engine=None):
        self.registry_path = registry_path or _ROOT / "state" / "MILK_RESOURCE_REGISTRY.json"
        self._registry = self._load_registry()
        self._adaptive_engine = adaptive_engine  # AdaptiveLearningEngine or None

    def _load_registry(self) -> dict:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        return {}

    def discover_capabilities(self) -> list[dict]:
        """Return all available capabilities with metadata."""
        caps = []
        # Local AI services
        local_ai = self._registry.get("local_ai", {})
        for name, info in local_ai.items():
            if isinstance(info, dict) and info.get("online"):
                caps.append({
                    "id": f"local_ai:{name}",
                    "type": "reasoning" if name in ("gpt_oss", "ollama") else "embedding",
                    "endpoint": info.get("endpoint", ""),
                    "online": True,
                    "sovereignty": 1.0,  # local
                    "privacy": 1.0,  # no external data transfer
                    "latency_ms": 500,  # estimated for local
                    "quality": 0.7,  # local model
                    "vendor": "local",
                })
        # Adapters (from external_adapters)
        caps.append({
            "id": "adapter:nextcloud", "type": "external_read",
            "online": True, "sovereignty": 0.8, "privacy": 0.9,
            "latency_ms": 100, "quality": 0.8, "vendor": "local_sync",
        })
        caps.append({
            "id": "adapter:github", "type": "external_read",
            "online": True, "sovereignty": 0.3, "privacy": 0.5,
            "latency_ms": 200, "quality": 0.9, "vendor": "github",
        })
        caps.append({
            "id": "adapter:orcid", "type": "external_read",
            "online": True, "sovereignty": 0.5, "privacy": 0.8,
            "latency_ms": 300, "quality": 0.7, "vendor": "orcid_public",
        })
        # Retrieval (local corpus)
        caps.append({
            "id": "retrieval:corpus", "type": "retrieval",
            "online": True, "sovereignty": 1.0, "privacy": 1.0,
            "latency_ms": 100, "quality": 0.8, "vendor": "local",
            "strategies": ["A_TFIDF_BGE_RRF", "D_HIERARCHICAL"],
            "canonical_status": "CANDIDATE_CANONICAL",
        })
        # Action gate
        caps.append({
            "id": "gate:sovereign", "type": "action_gate",
            "online": True, "sovereignty": 1.0, "privacy": 1.0,
            "latency_ms": 10, "quality": 1.0, "vendor": "local",
        })
        # Gap engine
        caps.append({
            "id": "engine:gap", "type": "gap_engine",
            "online": True, "sovereignty": 1.0, "privacy": 1.0,
            "latency_ms": 50, "quality": 0.8, "vendor": "local",
        })
        return caps

    def score(self, cap: dict, capability_needed: str) -> float:
        """Score a capability for a needed capability type. Higher is better."""
        # Capability match
        match = 1.0 if capability_needed in cap.get("type", "") else 0.0
        if capability_needed == "retrieval+external" and "external_read" in cap.get("type", ""):
            match = 0.8
        # No match = no score (hard filter)
        if match == 0.0:
            return 0.0
        if not cap.get("online", False):
            return 0.0
        # Sovereignty/locality
        sovereignty = cap.get("sovereignty", 0.5)
        # Privacy
        privacy = cap.get("privacy", 0.5)
        # Quality expected
        quality = cap.get("quality", 0.5)
        # Latency (inverted, normalized)
        latency = cap.get("latency_ms", 1000)
        latency_score = max(0, 1.0 - (latency / 2000))
        # Evidence available (placeholder: 1.0 if retrieval, 0.5 otherwise)
        evidence = 1.0 if cap.get("type") == "retrieval" else 0.5
        # Weighted sum
        score = (match * 0.30 + sovereignty * 0.20 + privacy * 0.15 +
                 quality * 0.15 + evidence * 0.10 + latency_score * 0.10)
        return round(score, 4)

    def select(self, capability_needed: str, top_k: int = 3, task_risk: str = "normal") -> list[dict]:
        """Select top-k capabilities for a needed capability, with fallback.

        When an adaptive engine is attached, base scores are adjusted by the
        learned policy (Thompson Sampling) before ranking.
        """
        caps = self.discover_capabilities()
        scored = []
        for cap in caps:
            s = self.score(cap, capability_needed)
            if s > 0:
                scored.append({**cap, "score": s, "base_score": s})
        # Apply adaptive adjustment if engine is available
        if self._adaptive_engine and scored:
            scored = self._adaptive_engine.adjust_candidates(scored, capability_needed, task_risk)
        else:
            scored.sort(key=lambda c: c.get("adjusted_score", c.get("score", 0)), reverse=True)
        return scored[:top_k]

    def route(self, steps: list[dict], task_risk: str = "normal") -> list[dict]:
        """Route each step to its best capability with fallback."""
        routed = []
        for step in steps:
            needed = step.get("capability_needed", "")
            selections = self.select(needed, top_k=3, task_risk=task_risk)
            primary = selections[0] if selections else None
            fallback = selections[1] if len(selections) > 1 else None
            routed.append({
                **step,
                "primary_capability": primary,
                "fallback_capability": fallback,
                "all_candidates": selections,
            })
        return routed


# ---------------------------------------------------------------------------
# Evidence Bundle — per-execution evidence with provenance
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """A single piece of evidence in a bundle."""
    source: str           # adapter/retrieval source
    source_uri: str = ""  # URI or path or PID
    content: str = ""
    content_hash: str = ""
    retrieval_method: str = ""  # e.g. "sparse_search", "adapter_read"
    reranking: str = ""
    transform: str = ""   # any transformation applied
    retrieved_at: str = field(default_factory=_now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class EvidenceBundle:
    """Evidence Fabric per execution with task_id/trace_id and hash chain."""

    def __init__(self, task_id: str, trace_id: str):
        self.task_id = task_id
        self.trace_id = trace_id
        self.items: list[EvidenceItem] = []
        self.inferences: list[dict] = []
        self.decisions: list[dict] = []
        self.gate_decisions: list[dict] = []
        self.actions: list[dict] = []
        self.outcomes: list[dict] = []
        self.created_at = _now()

    def add_evidence(self, **kwargs) -> EvidenceItem:
        item = EvidenceItem(**kwargs)
        if not item.content_hash and item.content:
            item.content_hash = _sha256(item.content)
        self.items.append(item)
        return item

    def add_inference(self, model: str, model_version: str, output: str, **meta) -> dict:
        inf = {
            "inference_id": _uuid(),
            "model": model,
            "model_version": model_version,
            "output": output,
            "output_hash": _sha256(output) if output else "",
            "timestamp": _now(),
            **meta,
        }
        self.inferences.append(inf)
        return inf

    def add_decision(self, decision: str, rationale: str, **meta) -> dict:
        dec = {
            "decision_id": _uuid(),
            "decision": decision,
            "rationale": rationale,
            "timestamp": _now(),
            **meta,
        }
        self.decisions.append(dec)
        return dec

    def add_gate_decision(self, receipt: dict) -> dict:
        self.gate_decisions.append(receipt)
        return receipt

    def add_action(self, action: str, **meta) -> dict:
        act = {"action_id": _uuid(), "action": action, "timestamp": _now(), **meta}
        self.actions.append(act)
        return act

    def add_outcome(self, outcome: str, **meta) -> dict:
        out = {"outcome_id": _uuid(), "outcome": outcome, "timestamp": _now(), **meta}
        self.outcomes.append(out)
        return out

    def hash_chain(self) -> str:
        """Compute a verifiable hash chain over all items in the bundle."""
        parts = [self.task_id, self.trace_id, self.created_at]
        for item in self.items:
            parts.append(item.content_hash or _sha256(item.source))
        for inf in self.inferences:
            parts.append(inf.get("output_hash", ""))
        for dec in self.decisions:
            parts.append(dec["decision"])
        for out in self.outcomes:
            parts.append(out["outcome"])
        return _sha256("|".join(parts))

    def to_dict(self) -> dict:
        return {
            "schema": "ia_milk.evidence_bundle.v1",
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "hash_chain": self.hash_chain(),
            "items": [i.to_dict() for i in self.items],
            "inferences": self.inferences,
            "decisions": self.decisions,
            "gate_decisions": self.gate_decisions,
            "actions": self.actions,
            "outcomes": self.outcomes,
        }

    def to_prov_o(self) -> dict:
        """Export to PROV-O compatible structure."""
        entities = []
        activities = []
        agents = []

        for item in self.items:
            entities.append({
                "@id": f"evidence:{item.source}:{item.content_hash[:12]}",
                "@type": "prov:Entity",
                "prov:value": item.content[:200],
                "prov:wasGeneratedBy": item.source,
            })
        for inf in self.inferences:
            activities.append({
                "@id": f"inference:{inf['inference_id'][:12]}",
                "@type": "prov:Activity",
                "prov:used": inf["model"],
                "prov:startedAtTime": inf["timestamp"],
            })
        agents.append({
            "@id": "milk:sovereign_core",
            "@type": "prov:Agent",
            "prov:actedOnBehalfOf": "milk:sovereign_core",
        })

        return {
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "entities": entities,
            "activities": activities,
            "agents": agents,
        }

    def save(self, path: Path | None = None) -> Path:
        out = path or _EVIDENCE_DIR / f"{self.task_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        d = self.to_dict()
        d["prov_o_export"] = self.to_prov_o()
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        return out


# ---------------------------------------------------------------------------
# Reasoning Worker — calls GPT-OSS or falls back to heuristic
# ---------------------------------------------------------------------------

class ReasoningWorker:
    """Calls local GPT-OSS or falls back to heuristic synthesis."""

    ENDPOINT = "http://127.0.0.1:8009"

    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint or self.ENDPOINT

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.endpoint}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.getcode() == 200
        except Exception:
            return False

    def reason(self, query: str, evidence_texts: list[str]) -> dict:
        """Synthesize evidence into a response. Uses GPT-OSS if available."""
        evidence_summary = "\n".join(e[:500] for e in evidence_texts[:5])
        if self.is_available():
            try:
                return self._call_gpt_oss(query, evidence_summary)
            except Exception as e:
                return self._heuristic(query, evidence_summary, error=str(e))
        return self._heuristic(query, evidence_summary)

    def _call_gpt_oss(self, query: str, evidence: str) -> dict:
        import urllib.request
        prompt = f"Query: {query}\n\nEvidence:\n{evidence}\n\nSynthesize a brief answer."
        body = json.dumps({
            "model": "gpt-oss-20b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 64,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "model": "gpt-oss-20b",
            "model_version": "local",
            "output": output,
            "method": "gpt_oss_api",
            "worker_role": "reasoning_worker",
        }

    def _heuristic(self, query: str, evidence: str, error: str = "") -> dict:
        output = f"Heuristic synthesis for '{query[:60]}': based on {len(evidence)} chars of evidence."
        if error:
            output += f" (GPT-OSS fallback: {error})"
        return {
            "model": "heuristic",
            "model_version": "local-v1",
            "output": output,
            "method": "heuristic_fallback",
            "worker_role": "reasoning_worker",
            "fallback_reason": error or "gpt_oss_unavailable",
        }


# ---------------------------------------------------------------------------
# Executor — executes reversible actions
# ---------------------------------------------------------------------------

class Executor:
    """Executes actions. Reversible actions only in this phase."""

    def __init__(self, gate):
        self.gate = gate  # ActionGate instance

    def execute(self, action: str, bundle: EvidenceBundle, **kwargs) -> dict:
        """Execute an action through the Sovereign Action Gate."""
        before = json.dumps(bundle.to_dict(), ensure_ascii=False)
        receipt = self.gate.execute_with_receipt(
            action=action,
            actor="cognitive_control_plane",
            source=bundle.task_id,
            target=kwargs.get("target", ""),
            before_state=before,
        )
        bundle.add_gate_decision(receipt)
        bundle.add_action(action, receipt_id=receipt["action_id"], **kwargs)
        return receipt


# ---------------------------------------------------------------------------
# Outcome Evaluator
# ---------------------------------------------------------------------------

class OutcomeEvaluator:
    """Evaluates the outcome of a task execution."""

    def evaluate(self, task: TaskEnvelope, bundle: EvidenceBundle) -> dict:
        evidence_count = len(bundle.items)
        inference_count = len(bundle.inferences)
        decision_count = len(bundle.decisions)
        gate_approved = sum(1 for g in bundle.gate_decisions if g.get("status") in ("approved", "executed"))
        gate_proposed = sum(1 for g in bundle.gate_decisions if g.get("status") == "proposed")

        quality = "high" if evidence_count >= 3 and inference_count >= 1 else "medium" if evidence_count >= 1 else "low"
        success = task.status == "done" and evidence_count > 0

        return {
            "task_id": task.task_id,
            "success": success,
            "quality": quality,
            "evidence_count": evidence_count,
            "inference_count": inference_count,
            "decision_count": decision_count,
            "gate_approved": gate_approved,
            "gate_proposed": gate_proposed,
            "hash_chain": bundle.hash_chain(),
            "evaluated_at": _now(),
        }


# ---------------------------------------------------------------------------
# Operational Memory — append-only, separate from corpus
# ---------------------------------------------------------------------------

class OperationalMemory:
    """Persistent append-only operational memory.

    Stores: task, episode, decision, evidence, failure, feedback, experiment, outcome.
    Never alters source documents. Separate from corpus.
    """

    def __init__(self, mem_dir: Path | None = None):
        self.mem_dir = mem_dir or _OP_MEM_DIR
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.mem_dir / "memory_index.jsonl"
        self.feedback_path = self.mem_dir / "learning_events.jsonl"

    def append(self, record_type: str, data: dict) -> dict:
        """Append a record to operational memory."""
        record = {
            "record_id": _uuid(),
            "type": record_type,  # task, episode, decision, evidence, failure, feedback, experiment, outcome
            "timestamp": _now(),
            **data,
        }
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def append_feedback(self, feedback: str, task_id: str = "", **meta) -> dict:
        """Record human feedback as a learning event."""
        event = {
            "event_id": _uuid(),
            "type": "learning_event",
            "feedback": feedback,
            "task_id": task_id,
            "timestamp": _now(),
            **meta,
        }
        with open(self.feedback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def query(self, record_type: str = "", limit: int = 20) -> list[dict]:
        """Query operational memory."""
        results = []
        if not self.index_path.exists():
            return results
        with open(self.index_path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                if not record_type or record.get("type") == record_type:
                    results.append(record)
                    if len(results) >= limit:
                        break
        return results

    def stats(self) -> dict:
        """Return memory statistics."""
        total = 0
        by_type: dict[str, int] = {}
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    total += 1
                    t = record.get("type", "unknown")
                    by_type[t] = by_type.get(t, 0) + 1
        feedback_count = 0
        if self.feedback_path.exists():
            with open(self.feedback_path, "r", encoding="utf-8") as f:
                feedback_count = sum(1 for _ in f)
        return {
            "total_records": total,
            "by_type": by_type,
            "learning_events": feedback_count,
            "memory_dir": str(self.mem_dir),
        }


# ---------------------------------------------------------------------------
# Self-Observability
# ---------------------------------------------------------------------------

class SelfObservability:
    """Local auto-observability for the Fabric. No cloud telemetry."""

    def __init__(self):
        self.root = _ROOT

    def collect(self) -> dict:
        """Collect health/capabilities/models/retrieval/sources/gaps/jobs/failures/latency/GPU/provenance."""
        import subprocess

        # Services
        services = {}
        for port, name in [(8009, "gpt_oss"), (8766, "fabric"), (11434, "ollama")]:
            try:
                import urllib.request
                req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    services[name] = {"healthy": True, "status": resp.getcode()}
            except Exception:
                services[name] = {"healthy": False}

        # GPU
        gpu = {}
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split(",")
                gpu = {"name": parts[0].strip(), "vram_used": parts[1].strip(), "vram_total": parts[2].strip()}
        except Exception:
            gpu = {"available": False}

        # Gaps
        gap_path = self.root / "state" / "atlas_gap_graph.json"
        gaps = {}
        if gap_path.exists():
            g = json.loads(gap_path.read_text(encoding="utf-8"))
            gaps = {"total": g.get("total_gaps", 0), "by_severity": g.get("by_severity", {})}

        # Operational memory stats
        op_mem = OperationalMemory()
        mem_stats = op_mem.stats()

        return {
            "schema": "ia_milk.observability.v1",
            "timestamp": _now(),
            "services": services,
            "gpu": gpu,
            "gaps": gaps,
            "operational_memory": mem_stats,
            "capabilities": {
                "adapters": 13,
                "retrieval_strategies": ["A_TFIDF_BGE_RRF", "D_HIERARCHICAL"],
                "canonical_status": "CANDIDATE_CANONICAL",
            },
        }


# ---------------------------------------------------------------------------
# Bounded Operating Loop — gap->research->cross-evidence->hypothesis->proposal->gate->action->measure->learn
# ---------------------------------------------------------------------------

class BoundedOperatingLoop:
    """Gap-driven bounded loop with step/time/resource limits."""

    def __init__(self, router: CapabilityRouter, worker: ReasoningWorker,
                 gate, op_mem: OperationalMemory, max_steps: int = 10, max_time_s: int = 60):
        self.router = router
        self.worker = worker
        self.gate = gate
        self.op_mem = op_mem
        self.max_steps = max_steps
        self.max_time_s = max_time_s

    def run(self, gap: dict | None = None) -> dict:
        """Run one bounded loop iteration for a specific gap."""
        start_time = time.time()
        task = TaskEnvelope(intent="gap_loop")
        bundle = EvidenceBundle(task.task_id, task.trace_id)
        steps_executed = 0
        loop_log = []

        try:
            # Step 1: Identify gap
            if gap is None:
                # Load gaps and pick the first open one
                gap_path = _ROOT / "state" / "atlas_gap_graph.json"
                if gap_path.exists():
                    g = json.loads(gap_path.read_text(encoding="utf-8"))
                    for gg in g.get("gaps", []):
                        if gg.get("status") == "open" and gg.get("human_gate", False):
                            gap = gg
                            break
                    if not gap:
                        for gg in g.get("gaps", []):
                            if gg.get("status") == "open":
                                gap = gg
                                break

            if gap:
                bundle.add_evidence(
                    source="gap_engine",
                    source_uri=f"gap:{gap.get('gap_id', '')}",
                    content=json.dumps(gap, ensure_ascii=False),
                    retrieval_method="gap_engine",
                )
                loop_log.append({"step": 1, "action": "identify_gap",
                                 "result": f"Gap {gap.get('gap_id', '?')}: {gap.get('gap_type', '')}"})
            else:
                bundle.add_evidence(source="gap_engine", content="No open gaps found",
                                    retrieval_method="gap_engine")
                loop_log.append({"step": 1, "action": "identify_gap", "result": "no gaps"})

            steps_executed += 1
            if time.time() - start_time > self.max_time_s:
                raise TimeoutError("max_time_s exceeded")

            # Step 2: Research — gather evidence from adapters
            # Try local FS and nextcloud
            try:
                from .external_adapters import get_all_adapters
                adapters = get_all_adapters()
                for name in ("localfs", "nextcloud"):
                    adapter = adapters.get(name)
                    if adapter and adapter.health().get("healthy"):
                        auth = adapter.auth_status()
                        if auth.get("authenticated") or auth.get("public_read_available"):
                            resources = adapter.list_resources()
                            items = resources.get("resources", resources.get("containers", []))
                            if isinstance(items, list) and items:
                                sample = items[0]
                                read = adapter.read_resource(sample.get("id", sample.get("name", "")))
                                if "content_hash" in read:
                                    bundle.add_evidence(
                                        source=name,
                                        source_uri=str(sample),
                                        content=read.get("content", "")[:500],
                                        content_hash=read.get("content_hash", ""),
                                        retrieval_method="adapter_read",
                                    )
                                    loop_log.append({"step": 2, "action": "research",
                                                     "result": f"evidence from {name}"})
                                    break
            except Exception as e:
                loop_log.append({"step": 2, "action": "research", "result": f"error: {e}"})

            steps_executed += 1

            # Step 3: Hypothesize — reason with worker
            evidence_texts = [i.content for i in bundle.items]
            result = self.worker.reason(
                f"Gap: {gap.get('evidence', 'no gap')[:100] if gap else 'no gap'}",
                evidence_texts,
            )
            inf = bundle.add_inference(
                model=result["model"], model_version=result["model_version"],
                output=result["output"], method=result["method"],
            )
            loop_log.append({"step": 3, "action": "hypothesize",
                             "result": f"inference via {result['model']}"})

            steps_executed += 1

            # Step 4: Propose — form a decision
            decision = bundle.add_decision(
                decision="propose_reversible_action",
                rationale=f"Based on {len(bundle.items)} evidence items and inference",
                gap_id=gap.get("gap_id", "") if gap else "",
            )
            loop_log.append({"step": 4, "action": "propose", "result": "decision made"})

            # Step 5: Gate — pass through Sovereign Action Gate (reversible)
            executor = Executor(self.gate)
            receipt = executor.execute("create_proposal", bundle,
                                       target=gap.get("gap_id", "") if gap else "unknown")
            loop_log.append({"step": 5, "action": "gate",
                             "result": f"gate status={receipt['status']}"})

            # Step 6: Measure outcome
            evaluator = OutcomeEvaluator()
            outcome = evaluator.evaluate(task, bundle)
            bundle.add_outcome("bounded_loop_complete", **outcome)
            loop_log.append({"step": 6, "action": "measure", "result": outcome["quality"]})

            # Step 7: Learn — record in operational memory
            self.op_mem.append("experiment", {
                "task_id": task.task_id,
                "trace_id": task.trace_id,
                "gap_id": gap.get("gap_id", "") if gap else "",
                "loop_log": loop_log,
                "outcome": outcome,
                "steps_executed": steps_executed,
            })
            loop_log.append({"step": 7, "action": "learn", "result": "recorded"})

            task.status = "done"

        except TimeoutError as e:
            task.status = "failed"
            loop_log.append({"step": steps_executed, "action": "timeout", "result": str(e)})
        except Exception as e:
            task.status = "failed"
            loop_log.append({"step": steps_executed, "action": "error", "result": str(e)})

        # Save evidence bundle
        bundle_path = bundle.save()
        # Record episode in operational memory
        self.op_mem.append("episode", {
            "task_id": task.task_id,
            "trace_id": task.trace_id,
            "intent": "gap_loop",
            "status": task.status,
            "steps_executed": steps_executed,
            "loop_log": loop_log,
            "bundle_path": str(bundle_path),
            "hash_chain": bundle.hash_chain(),
        })

        return {
            "task_id": task.task_id,
            "trace_id": task.trace_id,
            "status": task.status,
            "steps_executed": steps_executed,
            "loop_log": loop_log,
            "bundle_path": str(bundle_path),
            "hash_chain": bundle.hash_chain(),
        }


# ---------------------------------------------------------------------------
# Cognitive Control Plane — orchestrates the full pipeline
# ---------------------------------------------------------------------------

class CognitiveControlPlane:
    """The main orchestrator. GPT-OSS is a worker, never the orchestrator."""

    def __init__(self, op_mem_dir: Path | None = None, adaptive_engine=None):
        self.planner = Planner()
        # Adaptive learning engine (create if not provided)
        if adaptive_engine is None:
            try:
                from .adaptive_engine import AdaptiveLearningEngine
                adaptive_engine = AdaptiveLearningEngine()
            except Exception:
                adaptive_engine = None
        self.adaptive_engine = adaptive_engine
        self.router = CapabilityRouter(adaptive_engine=adaptive_engine)
        self.worker = ReasoningWorker()
        self.op_mem = OperationalMemory(op_mem_dir)
        self.evaluator = OutcomeEvaluator()
        self.observability = SelfObservability()

        # Action gate (import from existing module)
        try:
            from .action_gate import ActionGate
            self.gate = ActionGate()
        except Exception:
            self.gate = None
        self.executor = Executor(self.gate) if self.gate else None

    def execute_task(self, query: str, intent: str = "retrieve_and_decide") -> dict:
        """Execute a full task through the cognitive control plane."""
        task = TaskEnvelope(query=query, intent=intent)
        task.status = "planning"
        self.op_mem.append("task", task.to_dict())

        # Plan
        steps = self.planner.plan(task)
        task.status = "routing"

        # Route
        routed_steps = self.router.route(steps)

        # Execute
        task.status = "executing"
        bundle = EvidenceBundle(task.task_id, task.trace_id)
        execution_log = []

        for step in routed_steps:
            step_action = step.get("action")
            cap = step.get("primary_capability") or {}
            cap_id = cap.get("id", "none")

            if step_action == "retrieve":
                # Use local corpus retrieval (simulated — would call retrieval pipeline)
                bundle.add_evidence(
                    source="retrieval:corpus",
                    source_uri="local:corpus",
                    content=f"Retrieved for: {query[:200]}",
                    retrieval_method="candidate_canonical",
                    reranking="bge-reranker-v2-m3",
                    metadata={"strategy": "A_TFIDF_BGE_RRF"},
                )
                execution_log.append({"step": step["step"], "action": step_action,
                                      "capability": cap_id, "result": "evidence_added"})

            elif step_action == "gather_external":
                # Use adapters for external evidence
                try:
                    from .external_adapters import get_all_adapters
                    adapters = get_all_adapters()
                    for name in ("localfs", "nextcloud"):
                        adapter = adapters.get(name)
                        if adapter and adapter.health().get("healthy"):
                            auth = adapter.auth_status()
                            if auth.get("authenticated"):
                                resources = adapter.list_resources()
                                items = resources.get("resources", [])
                                if isinstance(items, list) and items:
                                    read = adapter.read_resource(items[0].get("id", ""))
                                    if "content_hash" in read:
                                        bundle.add_evidence(
                                            source=name,
                                            source_uri=str(items[0]),
                                            content=read.get("content", "")[:500],
                                            content_hash=read.get("content_hash", ""),
                                            retrieval_method="adapter_read",
                                        )
                                        break
                except Exception as e:
                    execution_log.append({"step": step["step"], "action": step_action,
                                          "error": str(e)})
                    continue
                execution_log.append({"step": step["step"], "action": step_action,
                                      "capability": cap_id, "result": "external_evidence"})

            elif step_action == "reason":
                # Use reasoning worker (GPT-OSS or heuristic)
                evidence_texts = [i.content for i in bundle.items]
                result = self.worker.reason(query, evidence_texts)
                bundle.add_inference(
                    model=result["model"], model_version=result["model_version"],
                    output=result["output"], method=result["method"],
                )
                execution_log.append({"step": step["step"], "action": step_action,
                                      "capability": cap_id, "result": f"model={result['model']}"})

            elif step_action == "decide":
                # Make decision
                bundle.add_decision(
                    decision="evidence_based_answer",
                    rationale=f"Based on {len(bundle.items)} evidence items and {len(bundle.inferences)} inferences",
                )
                execution_log.append({"step": step["step"], "action": step_action,
                                      "result": "decision_made"})

            elif step_action == "gate":
                # Pass through Sovereign Action Gate (reversible/dry-safe)
                if self.executor:
                    receipt = self.executor.execute("stage_derived", bundle,
                                                    target=f"task:{task.task_id}")
                    execution_log.append({"step": step["step"], "action": step_action,
                                          "result": f"gate:{receipt['status']}"})
                else:
                    execution_log.append({"step": step["step"], "action": step_action,
                                          "result": "gate_not_available"})

            if len(execution_log) >= task.constraints.get("max_steps", 10):
                break

        # Evaluate
        task.status = "evaluating"
        outcome = self.evaluator.evaluate(task, bundle)
        bundle.add_outcome("task_complete", **outcome)

        # Save evidence bundle
        bundle_path = bundle.save()

        # Record learning event for adaptive policy
        learning_event = None
        if self.adaptive_engine:
            # Collect evidence metrics from the execution
            evidence_metrics = {
                "evidence_count": len(bundle.items),
                "inference_count": len(bundle.inferences),
                "latency_ms": 500,  # estimated
                "sovereignty": 1.0,  # all local
                "reversible": True,
                "confidence": 0.7,
                "failures": 0 if outcome.get("success") else 1,
                "evidence_gap": len(bundle.items) == 0,
                "resource_usage": 0.5,
            }
            # Collect scores_before from routed steps
            scores_before = {}
            selected_capabilities = set()
            for step in routed_steps:
                cap = step.get("primary_capability")
                if cap and isinstance(cap, dict):
                    cap_id = cap.get("id", "unknown")
                    scores_before[cap_id] = cap.get("base_score", cap.get("score", 0))
                    selected_capabilities.add(cap_id)

            # Record outcome for each selected capability
            for cap_id in selected_capabilities:
                learning_event = self.adaptive_engine.record_outcome(
                    task_id=task.task_id,
                    trace_id=task.trace_id,
                    selected_capability=cap_id,
                    candidates=scores_before,
                    scores_before=scores_before,
                    outcome=outcome,
                    evidence_metrics=evidence_metrics,
                    context={"query": query, "intent": intent},
                    bundle_hash=bundle.hash_chain(),
                )

        # Record in operational memory
        self.op_mem.append("episode", {
            "task_id": task.task_id,
            "trace_id": task.trace_id,
            "query": query,
            "intent": intent,
            "status": "done",
            "execution_log": execution_log,
            "bundle_path": str(bundle_path),
            "hash_chain": bundle.hash_chain(),
            "outcome": outcome,
            "learning_event": learning_event["event_id"] if learning_event else None,
        })

        task.status = "done"

        return {
            "task_id": task.task_id,
            "trace_id": task.trace_id,
            "status": task.status,
            "query": query,
            "intent": intent,
            "execution_log": execution_log,
            "evidence_count": len(bundle.items),
            "inference_count": len(bundle.inferences),
            "decision_count": len(bundle.decisions),
            "gate_decisions": len(bundle.gate_decisions),
            "outcome": outcome,
            "bundle_path": str(bundle_path),
            "hash_chain": bundle.hash_chain(),
            "provenance_chain_reconstructable": True,
        }

    def reconstruct_chain(self, task_id: str) -> dict:
        """Reconstruct the full source->evidence->transform->inference->decision->action->outcome chain."""
        bundle_path = _EVIDENCE_DIR / f"{task_id}.json"
        if not bundle_path.exists():
            return {"error": "bundle not found", "task_id": task_id}
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        chain = []
        for item in bundle.get("items", []):
            chain.append({"type": "source", "source": item["source"], "uri": item.get("source_uri", ""),
                         "hash": item.get("content_hash", "")[:16]})
            chain.append({"type": "evidence", "content_preview": item.get("content", "")[:100],
                         "retrieval": item.get("retrieval_method", ""), "reranking": item.get("reranking", "")})
        for inf in bundle.get("inferences", []):
            chain.append({"type": "inference", "model": inf.get("model", ""),
                         "output_preview": inf.get("output", "")[:100]})
        for dec in bundle.get("decisions", []):
            chain.append({"type": "decision", "decision": dec.get("decision", "")})
        for act in bundle.get("actions", []):
            chain.append({"type": "action", "action": act.get("action", "")})
        for out in bundle.get("outcomes", []):
            chain.append({"type": "outcome", "outcome": out.get("outcome", "")})
        return {
            "task_id": task_id,
            "trace_id": bundle.get("trace_id", ""),
            "hash_chain": bundle.get("hash_chain", ""),
            "chain": chain,
            "chain_length": len(chain),
            "prov_o_available": "prov_o_export" in bundle,
        }

    def health(self) -> dict:
        """Return self-observability health snapshot."""
        return self.observability.collect()

    def explain_selection(self, cap_id: str) -> dict:
        """Explain why a capability was chosen, including adaptive policy info."""
        if self.adaptive_engine:
            return self.adaptive_engine.explain_selection(cap_id)
        return {"error": "no adaptive engine available", "capability_id": cap_id}

    def adaptive_observability(self) -> dict:
        """Return adaptive learning engine observability."""
        if self.adaptive_engine:
            return self.adaptive_engine.observability()
        return {"error": "no adaptive engine available"}
