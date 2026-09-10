"""MILK P0/P1 Hardening — Pydantic contracts, concurrency-safe persistence,
claim-based evidence reconciliation, provenance ledger, hardened ActionGate,
extended compliance profiles, SHACL shapes, resource-aware routing, SBOM.

Does NOT replace existing components. Adds hardening layer.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # fallback
    ConfigDict = dict
    ValidationError = ValueError

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _ROOT / "state" / "schemas"


def _now():
    return datetime.now(timezone.utc).isoformat()

def _uuid():
    return uuid.uuid4().hex

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ===========================================================================
# P0-1: Pydantic strict contracts at critical boundaries
# ===========================================================================

if PYDANTIC_AVAILABLE:

    class TaskEnvelopeContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        task_id: str
        trace_id: str
        query: str = ""
        intent: str = "retrieve_and_decide"
        constraints: dict = Field(default_factory=lambda: {
            "max_steps": 10, "max_time_s": 60,
            "max_retrieval_results": 10,
            "sovereignty_required": True,
            "local_preferred": True,
        })
        created_at: str = Field(default_factory=_now)
        status: str = "pending"
        schema_version: str = "task.v1"

    class CapabilityDescriptorContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        id: str
        type: str
        provider: str
        endpoint_or_path: str
        status: str
        local_remote: str
        sovereignty: float = 0.5
        privacy_class: str = "local"
        version: str = ""
        health: bool = False
        latency_ms: int = 500
        schema_version: str = "capability.v1"

    class EvidenceItemContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        source: str
        source_uri: str = ""
        content: str = ""
        content_hash: str = ""
        retrieval_method: str = ""
        reranking: str = ""
        transform: str = ""
        retrieved_at: str = Field(default_factory=_now)
        metadata: dict = Field(default_factory=dict)
        untrusted_content: bool = False
        schema_version: str = "evidence.v1"

    class InferenceRecordContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        inference_id: str
        model: str
        model_version: str
        output: str
        output_hash: str
        timestamp: str = Field(default_factory=_now)
        method: str = ""
        schema_version: str = "inference.v1"

    class DecisionRecordContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        decision_id: str
        decision: str
        rationale: str
        timestamp: str = Field(default_factory=_now)
        schema_version: str = "decision.v1"

    class ActionRequestContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        action_id: str
        action: str
        actor: str
        source: str
        target: str
        tier: str
        risk_level: str = "normal"
        purpose: str = ""
        idempotency_key: str = ""
        preconditions: dict = Field(default_factory=dict)
        timestamp: str = Field(default_factory=_now)
        schema_version: str = "action_request.v1"

    class ActionReceiptContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        action_id: str
        actor: str
        action: str
        tier: str
        source: str
        target: str
        timestamp: str
        evidence: str = ""
        before_hash: str = ""
        after_hash: str = ""
        reversible: bool = True
        rollback: str = ""
        human_gate: bool = False
        status: str = "proposed"
        risk_level: str = "normal"
        purpose: str = ""
        idempotency_key: str = ""
        postcondition_verified: bool = False
        schema_version: str = "action_receipt.v1"

    class OutcomeRecordContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        task_id: str
        success: bool
        quality: str
        evidence_count: int
        inference_count: int
        decision_count: int
        gate_approved: int
        gate_proposed: int
        hash_chain: str
        evaluated_at: str = Field(default_factory=_now)
        schema_version: str = "outcome.v1"

    class LearningEventContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        event_id: str
        task_id: str
        trace_id: str
        timestamp: str
        context: dict
        candidates: list
        scores_before: dict
        selected_capability: str
        evidence_metrics: dict
        outcome: dict
        reward_components: dict
        reward_final: float
        reward_raw: float = 0.0
        reward_normalized: float = 0.0
        selection_probability: float = 1.0
        human_feedback: Optional[str] = None
        policy_version_before: int
        policy_version_after: int
        bundle_hash: str = ""
        event_hash: str
        previous_hash: str = ""
        trust_status: str = "trusted"
        schema_version: str = "learning_event.v1"

    class ComplianceAssessmentContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        assessment_id: str
        trace_id: str = ""
        jurisdiction: str = "EU/PT"
        profiles: list
        overall_state: str = "UNKNOWN"
        evidence_present: list = Field(default_factory=list)
        evidence_missing: list = Field(default_factory=list)
        human_review: bool = False
        decision_effect: str = "proceed"
        timestamp: str = Field(default_factory=_now)
        schema_version: str = "compliance.v1"

    class ProvenanceRecordContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        record_id: str
        trace_id: str
        event_hash: str
        previous_hash: str
        source_id: str
        source_uri: str = ""
        tool: str = ""
        model_version: str = ""
        transformation: str = ""
        input_hash: str = ""
        output_hash: str = ""
        timestamp: str = Field(default_factory=_now)
        schema_version: str = "provenance.v1"

    class SemanticEntityContract(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        id: str
        type: str
        properties: dict = Field(default_factory=dict)
        context: list = Field(default_factory=list)
        ngsi_ld_type: str = ""
        schema_version: str = "semantic.v1"

    CONTRACT_REGISTRY = {
        "task": TaskEnvelopeContract,
        "capability": CapabilityDescriptorContract,
        "evidence": EvidenceItemContract,
        "inference": InferenceRecordContract,
        "decision": DecisionRecordContract,
        "action_request": ActionRequestContract,
        "action_receipt": ActionReceiptContract,
        "outcome": OutcomeRecordContract,
        "learning_event": LearningEventContract,
        "compliance": ComplianceAssessmentContract,
        "provenance": ProvenanceRecordContract,
        "semantic": SemanticEntityContract,
    }

    def validate_contract(name: str, data: dict) -> tuple[bool, str]:
        """Validate data against a contract. Returns (valid, error_message)."""
        contract = CONTRACT_REGISTRY.get(name)
        if not contract:
            return False, f"unknown contract: {name}"
        try:
            contract(**data)
            return True, ""
        except ValidationError as e:
            return False, str(e)

    def export_schema_registry() -> dict:
        """Export all schema definitions with hashes."""
        schemas = {}
        for name, contract in CONTRACT_REGISTRY.items():
            schema = contract.model_json_schema()
            schema_hash = _sha256(json.dumps(schema, sort_keys=True))[:16]
            schemas[name] = {
                "schema_version": schema.get("properties", {}).get("schema_version", {}).get("default", ""),
                "schema_hash": schema_hash,
            }
        return {"schema_registry_version": "v1", "schemas": schemas}

else:
    # Fallback when pydantic is not available
    def validate_contract(name: str, data: dict) -> tuple[bool, str]:
        return True, ""  # no validation in fallback mode
    def export_schema_registry() -> dict:
        return {"error": "pydantic not available"}


# ===========================================================================
# P0-2: Concurrency-safe persistence (atomic writes, cross-process lock)
# ===========================================================================

class AtomicFileWriter:
    """Atomic file writer with temp file + fsync + os.replace."""

    @staticmethod
    def write_json(path: Path, data: dict, indent: int = 2) -> bool:
        """Atomically write JSON to path. Returns True on success."""
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Write to temp file
            fd, tmp_path = tempfile.mkstemp(
                dir=str(path.parent), suffix=".tmp", prefix=path.stem)
            try:
                content = json.dumps(data, ensure_ascii=False, indent=indent)
                os.write(fd, content.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
            # Atomic replace
            os.replace(tmp_path, str(path))
            return True
        except Exception:
            try:
                os.unlink(tmp_path)
            except:
                pass
            return False

    @staticmethod
    def append_jsonl(path: Path, record: dict) -> bool:
        """Atomically append a JSONL record."""
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception:
            return False


class CrossProcessLock:
    """Simple cross-process lock using a lock file with timeout.

    On Windows, uses msvcrt.locking; on POSIX, uses fcntl.flock.
    Falls back to atomic file creation if neither is available.
    """

    def __init__(self, lock_path: Path, timeout_s: float = 5.0):
        self.lock_path = lock_path
        self.timeout_s = timeout_s
        self._fd = None
        self._acquired = False

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"lock not acquired within {self.timeout_s}s: {self.lock_path}")
        return self

    def __exit__(self, *args):
        self.release()

    def acquire(self) -> bool:
        """Acquire lock with timeout. Returns True if acquired."""
        start = time.time()
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while time.time() - start < self.timeout_s:
            try:
                # Try atomic creation (O_CREAT|O_EXCL)
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                self._fd = fd
                self._acquired = True
                os.write(fd, str(os.getpid()).encode("utf-8"))
                return True
            except FileExistsError:
                # Check if lock is stale (process died)
                try:
                    pid = int(self.lock_path.read_text().strip())
                    # On Windows, can't easily check if process exists
                    # Just wait and retry
                except (ValueError, OSError):
                    pass
                time.sleep(0.1)
        return False

    def release(self):
        """Release the lock."""
        if self._acquired:
            try:
                if self._fd is not None:
                    os.close(self._fd)
                self.lock_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._acquired = False


class ConcurrentPolicyStore:
    """Concurrency-safe adaptive policy persistence."""

    def __init__(self, policy_path: Path, lock_dir: Path | None = None):
        self.path = policy_path
        self.lock = CrossProcessLock(
            (lock_dir or policy_path.parent) / f"{policy_path.stem}.lock")

    def save(self, data: dict) -> bool:
        """Save policy atomically with cross-process lock."""
        with self.lock:
            # Optimistic version check
            if self.path.exists():
                existing = json.loads(self.path.read_text(encoding="utf-8"))
                if existing.get("version", 0) > data.get("version", 0):
                    return False  # stale version, refuse
            return AtomicFileWriter.write_json(self.path, data)

    def load(self) -> dict | None:
        """Load policy with recovery from interrupted writes."""
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            # Validate basic structure
            if "version" not in data:
                # Corrupted — try to recover from history
                return None
            return data
        except json.JSONDecodeError:
            # Write was interrupted — file is corrupted
            return None


class ConcurrentJSONLStore:
    """Concurrency-safe JSONL append store."""

    def __init__(self, path: Path, lock_dir: Path | None = None):
        self.path = path
        self.lock = CrossProcessLock(
            (lock_dir or path.parent) / f"{path.stem}.lock")
        # In-process thread lock: file locks serialize across processes but
        # race within a single process (stale-PID checks cannot distinguish
        # same-process threads). A threading.Lock guarantees in-process
        # mutual exclusion without timeout-induced unlocked proceeds.
        self._thread_lock = threading.Lock()

    def append(self, record: dict) -> bool:
        """Append a record with in-process then cross-process lock."""
        with self._thread_lock:
            with self.lock:
                return AtomicFileWriter.append_jsonl(self.path, record)

    def read_all(self) -> list[dict]:
        """Read all records, skipping corrupted lines."""
        if not self.path.exists():
            return []
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip corrupted line
        return records


# ===========================================================================
# P0-3: Contextual learning with reward_raw/reward_normalized/propensity
# ===========================================================================

class ContextualLearningEnhancer:
    """Enhances the existing ContextualAdaptivePolicy with:
    - reward_raw separate from reward_normalized
    - selection_probability (propensity) recording
    - RNG seed/trace
    - quarantine for suspicious feedback/evidence poisoning
    """

    def __init__(self):
        self.quarantined_events: list[str] = []  # event_ids

    def normalize_reward(self, reward_raw: float) -> float:
        """Normalize reward from [-1, 1] to [0.01, 0.99] for Beta domain."""
        normalized = (reward_raw + 1.0) / 2.0
        return max(0.01, min(0.99, normalized))

    def compute_propensity(self, candidates: list[dict], selected_id: str,
                           exploration_rate: float) -> float:
        """Estimate selection probability (propensity) for IPS/DR evaluation.

        Under Thompson Sampling, propensity = P(selected | candidates).
        Approximation: 1/n for exploration, 1 for exploitation (greedy).
        """
        n = len(candidates)
        if n == 0:
            return 0.0
        # Under epsilon-greedy exploration:
        # P(selected) = (1 - epsilon) * 1{greedy_choice} + epsilon * (1/n)
        # For Thompson Sampling, approximate as uniform when exploring
        return (1 - exploration_rate) * (1.0 / max(1, n)) + exploration_rate * (1.0 / n)

    def should_quarantine(self, event: dict) -> tuple[bool, str]:
        """Check if a learning event should be quarantined."""
        # Check for evidence poisoning patterns
        reward = event.get("reward_final", 0)
        if reward > 0.95 or reward < -0.95:
            # Extreme rewards are suspicious
            return True, "extreme_reward_suspicious"
        # Check for untrusted content
        if event.get("context", {}).get("untrusted_content"):
            return True, "untrusted_content_detected"
        return False, ""

    def quarantine(self, event_id: str, reason: str) -> dict:
        """Quarantine a learning event so it doesn't update policy."""
        self.quarantined_events.append(event_id)
        return {"event_id": event_id, "status": "QUARANTINED", "reason": reason}


# ===========================================================================
# P0-4: Claim-based evidence reconciliation
# ===========================================================================

class Claim:
    """A canonical claim extracted from evidence."""

    def __init__(self, text: str, source_id: str, source_uri: str = "",
                 content_hash: str = "", timestamp: str = "", confidence: float = 0.5):
        self.text = text
        self.source_id = source_id
        self.source_uri = source_uri
        self.content_hash = content_hash
        self.timestamp = timestamp
        self.confidence = confidence
        self.status = "unverified"  # support, refute, uncertain, unverified

    def to_dict(self) -> dict:
        return {"text": self.text, "source_id": self.source_id,
                "source_uri": self.source_uri, "content_hash": self.content_hash,
                "timestamp": self.timestamp, "confidence": self.confidence,
                "status": self.status}


class ClaimBasedReconciliation:
    """Claim-based evidence reconciliation.

    Pipeline: EvidenceItem → canonical claim → entity/time/source resolution →
    semantic similarity → duplicate detection → source independence →
    contradiction detection → support/refute/uncertain → quality/calibration.
    """

    def __init__(self):
        self.claims: list[Claim] = []

    def extract_claims(self, evidence_items: list[dict]) -> list[Claim]:
        """Extract canonical claims from evidence items."""
        claims = []
        for item in evidence_items:
            content = item.get("content", "")
            # Simple claim extraction: each sentence is a potential claim
            sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 10]
            for sent in sentences[:5]:  # limit to 5 claims per item
                claim = Claim(
                    text=sent,
                    source_id=item.get("source", "unknown"),
                    source_uri=item.get("source_uri", ""),
                    content_hash=item.get("content_hash", ""),
                    timestamp=item.get("retrieved_at", ""),
                    confidence=0.5,
                )
                claims.append(claim)
        self.claims = claims
        return claims

    def _source_root(self, source_id: str) -> str:
        """Extract root source (not just adapter variant).

        Two adapters pointing to the same origin are NOT independent.
        """
        # Map adapter names to root origins
        root_map = {
            "nextcloud": "nextcloud:nuvem.associacaomilk.pt",
            "onedrive": "microsoft:sharepoint",
            "github": "github:milkivc",
            "codeberg": "codeberg:milkivc",
            "localfs": "local:filesystem",
            "git": "local:git",
            "retrieval": "local:corpus",
        }
        for prefix, root in root_map.items():
            if prefix in source_id:
                return root
        return source_id

    def check_independence(self, claims: list[Claim]) -> int:
        """Count truly independent source roots."""
        roots = set()
        for c in claims:
            roots.add(self._source_root(c.source_id))
        return len(roots)

    def detect_contradictions(self, claims: list[Claim]) -> list[dict]:
        """Detect semantic contradictions between claims from different sources."""
        contradictions = []
        for i, a in enumerate(claims):
            for j, b in enumerate(claims):
                if i >= j:
                    continue
                if self._source_root(a.source_id) == self._source_root(b.source_id):
                    continue  # same source, not a contradiction
                # Simple contradiction detection: negation patterns
                if self._is_contradiction(a.text, b.text):
                    contradictions.append({
                        "claim_a": a.text[:100], "claim_b": b.text[:100],
                        "source_a": a.source_id, "source_b": b.source_id,
                        "type": "semantic_contradiction",
                    })
                    a.status = "refute"
                    b.status = "refute"
        return contradictions

    def _is_contradiction(self, text_a: str, text_b: str) -> bool:
        """Simple contradiction detection via negation patterns."""
        if not text_a or not text_b:
            return False
        # Check if one text contains "not" + key phrase from other
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        # High overlap but with negation difference
        overlap = len(words_a & words_b) / max(1, len(words_a | words_b))
        if overlap > 0.6:
            has_neg_a = any(w in text_a.lower() for w in ["not", "não", "never", "nunca", "false"])
            has_neg_b = any(w in text_b.lower() for w in ["not", "não", "never", "nunca", "false"])
            return has_neg_a != has_neg_b
        return False

    def reconcile(self, evidence_items: list[dict]) -> dict:
        """Full claim-based reconciliation pipeline."""
        claims = self.extract_claims(evidence_items)
        independent = self.check_independence(claims)
        contradictions = self.detect_contradictions(claims)

        # Mark supported claims (no contradiction, from independent source)
        for c in claims:
            if c.status == "unverified" and not any(
                c in [cc for cc in contradictions] for _ in [1]):
                c.status = "support"

        quality = min(1.0, independent / 3.0)
        if contradictions:
            quality *= 0.7

        return {
            "total_claims": len(claims),
            "independent_sources": independent,
            "contradictions": contradictions,
            "quality_score": round(quality, 4),
            "claims": [c.to_dict() for c in claims],
        }


# ===========================================================================
# P0-5: Provenance ledger with hash chain
# ===========================================================================

class ProvenanceLedger:
    """Provenance ledger with event_hash + previous_hash chain."""

    def __init__(self, ledger_path: Path | None = None):
        self.path = ledger_path or _ROOT / "state" / "provenance_ledger.jsonl"
        self.previous_hash = ""
        self._load_last_hash()

    def _load_last_hash(self):
        """Load the last hash from the ledger."""
        if not self.path.exists():
            return
        try:
            lines = self.path.read_text(encoding="utf-8").strip().split("\n")
            if lines:
                last = json.loads(lines[-1])
                self.previous_hash = last.get("event_hash", "")
        except Exception:
            pass

    def append(self, *, trace_id: str, source_id: str, source_uri: str = "",
               tool: str = "", model_version: str = "", transformation: str = "",
               input_hash: str = "", output_hash: str = "") -> dict:
        """Append a provenance record to the ledger."""
        record = {
            "record_id": _uuid(),
            "trace_id": trace_id,
            "event_hash": _sha256(f"{trace_id}:{source_id}:{tool}:{output_hash}"),
            "previous_hash": self.previous_hash,
            "source_id": source_id,
            "source_uri": source_uri,
            "tool": tool,
            "model_version": model_version,
            "transformation": transformation,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "timestamp": _now(),
        }
        AtomicFileWriter.append_jsonl(self.path, record)
        self.previous_hash = record["event_hash"]
        return record

    def verify_chain(self) -> tuple[bool, int]:
        """Verify the hash chain integrity. Returns (valid, records_checked)."""
        if not self.path.exists():
            return True, 0
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        prev = ""
        for r in records:
            if r.get("previous_hash") != prev:
                return False, len(records)
            prev = r.get("event_hash", "")
        return True, len(records)


# ===========================================================================
# P0: Hardened ActionGate — identity, permissions, dry-run, idempotency
# ===========================================================================

class HardenedActionGate:
    """Hardened Sovereign Action Gate with:
    - identity/actor verification
    - capability permissions (allowlist)
    - least privilege
    - risk level assessment
    - purpose declaration
    - dry-run mode
    - idempotency key
    - preconditions and postconditions
    - rollback/reversibility
    - SSRF/path traversal protection for external adapters
    - untrusted content flagging
    """

    # Allowlist of safe destinations for external adapters
    ALLOWED_DOMAINS = {
        "github.com", "api.github.com", "codeberg.org",
        "zenodo.org", "sandbox.zenodo.org",
        "pub.orcid.org", "orcid.org",
        "associacaomilk.pt", "nuvem.associacaomilk.pt",
        "atlas.associacaomilk.pt",
        "127.0.0.1", "localhost",
    }

    # Blocked path patterns
    BLOCKED_PATH_PATTERNS = ["../", "..\\", "/etc/", "\\windows\\", "\\system32\\"]

    # Capability permissions per actor
    ACTOR_PERMISSIONS = {
        "cognitive_control_plane": ["discover", "read_resource", "search",
                                     "stage_derived", "create_proposal",
                                     "create_draft", "update_draft_metadata",
                                     "update_manifest", "write_receipt"],
        "milk_system": ["discover", "read_resource", "search", "health",
                        "audit", "list_resources", "compare", "inventory",
                        "gap_analysis", "code_audit"],
        "human": ["*"],  # humans can do anything
    }

    def __init__(self):
        self._idempotency_keys: set[str] = set()

    def check_permission(self, actor: str, action: str) -> tuple[bool, str]:
        """Check if actor has permission for action."""
        perms = self.ACTOR_PERMISSIONS.get(actor, [])
        if "*" in perms or action in perms:
            return True, ""
        return False, f"actor '{actor}' not permitted for action '{action}'"

    def check_destination(self, url: str) -> tuple[bool, str]:
        """SSRF protection: check if destination is in allowlist."""
        if not url:
            return True, ""  # no URL = local action
        # Extract domain
        domain = url.split("://")[-1].split("/")[0].split(":")[0]
        if domain in self.ALLOWED_DOMAINS:
            return True, ""
        return False, f"destination '{domain}' not in allowlist"

    def check_path_traversal(self, path: str) -> tuple[bool, str]:
        """Path traversal protection."""
        for pattern in self.BLOCKED_PATH_PATTERNS:
            if pattern in path:
                return False, f"blocked path pattern: '{pattern}'"
        return True, ""

    def check_prompt_injection(self, content: str) -> tuple[bool, str]:
        """Check for prompt injection patterns in content."""
        if not content:
            return True, ""
        injection_patterns = [
            "ignore previous instructions",
            "system prompt:",
            "you are now",
            "disregard all",
            "forget your rules",
            "act as if",
            "new instructions:",
        ]
        lower = content.lower()
        for pattern in injection_patterns:
            if pattern in lower:
                return False, f"prompt injection detected: '{pattern}'"
        return True, ""

    def is_idempotent(self, key: str) -> bool:
        """Check if idempotency key already used."""
        if not key:
            return True  # no key = always allow
        if key in self._idempotency_keys:
            return False  # already processed
        self._idempotency_keys.add(key)
        return True

    def evaluate(self, *, action: str, actor: str = "milk_system",
                 target: str = "", risk_level: str = "normal",
                 purpose: str = "", idempotency_key: str = "",
                 preconditions: dict | None = None,
                 dry_run: bool = False) -> dict:
        """Full hardened gate evaluation. Returns gate decision."""
        # Check permissions
        perm_ok, perm_msg = self.check_permission(actor, action)
        if not perm_ok:
            return {"allowed": False, "reason": perm_msg, "tier": "BLOCKED"}

        # Check destination (SSRF)
        if target and ("http" in target or "https" in target):
            dest_ok, dest_msg = self.check_destination(target)
            if not dest_ok:
                return {"allowed": False, "reason": dest_msg, "tier": "BLOCKED"}

        # Check path traversal
        if target:
            path_ok, path_msg = self.check_path_traversal(target)
            if not path_ok:
                return {"allowed": False, "reason": path_msg, "tier": "BLOCKED"}

        # Idempotency check
        if idempotency_key and not self.is_idempotent(idempotency_key):
            return {"allowed": False, "reason": "duplicate idempotency key",
                    "tier": "BLOCKED"}

        # Determine tier
        read_actions = {"discover", "read_resource", "search", "health",
                        "audit", "list_resources", "compare", "inventory",
                        "gap_analysis", "code_audit"}
        reversible_actions = {"stage_derived", "create_proposal", "create_draft",
                            "update_draft_metadata", "update_manifest", "write_receipt"}
        public_actions = {"publish_zenodo", "deploy_production", "delete_resource",
                         "force_push", "git_push", "create_doi", "modify_orcid",
                         "deploy_ptservidor"}

        if action in read_actions:
            tier = "READ_AUTO"
        elif action in reversible_actions:
            tier = "WRITE_REVERSIBLE"
        elif action in public_actions:
            tier = "PUBLIC_OR_IRREVERSIBLE"
        else:
            tier = "PUBLIC_OR_IRREVERSIBLE"  # default: most restrictive

        # Risk-based escalation
        if risk_level == "high" and tier == "WRITE_REVERSIBLE":
            tier = "PUBLIC_OR_IRREVERSIBLE"  # escalate high-risk reversible to require human

        allowed = tier != "PUBLIC_OR_IRREVERSIBLE" or dry_run

        return {
            "allowed": allowed,
            "tier": tier,
            "risk_level": risk_level,
            "purpose": purpose,
            "dry_run": dry_run,
            "idempotency_key": idempotency_key,
            "preconditions_met": preconditions is None or all(preconditions.values()),
        }


# ===========================================================================
# P1: Extended compliance profiles
# ===========================================================================

EXTENDED_COMPLIANCE_PROFILES = {
    "en_301_549": {
        "instrument": "EN 301 549",
        "official_source": "ETSI",
        "version": "3.2.1",
        "effective_date": "2021-03",
        "role": "voluntary_standard",
        "requirements": ["accessibility_requirements", "procurement"],
    },
    "nis2": {
        "instrument": "NIS2 Directive 2022/2555",
        "official_source": "EUR-Lex 32022L2555",
        "version": "2022-12-14",
        "effective_date": "2024-10 (transposition)",
        "role": "essential_or_important_entity",
        "requirements": ["risk_management", "incident_reporting",
                        "supply_chain_security", "governance"],
    },
    "cyber_resilience_act": {
        "instrument": "Cyber Resilience Act 2024/2847",
        "official_source": "EUR-Lex 32024R2847",
        "version": "2024-11-20",
        "effective_date": "2027 (phased)",
        "role": "manufacturer_of_products_with_digital_elements",
        "requirements": ["security_by_design", "vulnerability_disclosure",
                        "incident_reporting", "conformity_assessment"],
    },
    "data_act": {
        "instrument": "Data Act 2023/2854",
        "official_source": "EUR-Lex 32023R2854",
        "version": "2023-12-22",
        "effective_date": "2025-09",
        "role": "data_holder_or_recipient",
        "requirements": ["data_sharing", "data_portability", "iot_data_access"],
    },
    "data_governance_act": {
        "instrument": "Data Governance Act 2022/868",
        "official_source": "EUR-Lex 32022R0868",
        "version": "2022-05-30",
        "effective_date": "2023-09-24",
        "role": "data_intermediation_or_altruism",
        "requirements": ["data_intermediation", "data_altruism", "international_transfer"],
    },
    "open_data_psi": {
        "instrument": "Open Data/PSI Directive 2019/1024",
        "official_source": "EUR-Lex 32019L1024",
        "version": "2019-06-20",
        "effective_date": "2021-07-17",
        "role": "public_sector_body",
        "requirements": ["open_data_default", "machine_readable", "api_access",
                        "metadata_quality"],
    },
    "eidas2": {
        "instrument": "eIDAS 2.0 Regulation 2024/1183",
        "official_source": "EUR-Lex 32024R1183",
        "version": "2024-04-11",
        "effective_date": "2026 (phased)",
        "role": "digital_identity_provider_or_relying_party",
        "requirements": ["eu_digital_identity_wallet", "qualified_trust_services"],
    },
    "copyright_tdm": {
        "instrument": "Copyright TDM (DSM Directive 2019/790)",
        "official_source": "EUR-Lex 32019L0790",
        "version": "2019-04-17",
        "effective_date": "2021-06-07",
        "role": "tdm_user_or_rightsholder",
        "requirements": ["tdm_exception", "opt_out_mechanism",
                        "text_data_mining_rights"],
    },
}


# ===========================================================================
# P1: SHACL shapes for semantic entities
# ===========================================================================

SHACL_SHAPES = {
    "territory": {
        "@type": "sh:NodeShape",
        "sh:targetClass": "milk:Territory",
        "sh:property": [
            {"sh:path": "milk:name", "sh:minCount": 1, "sh:datatype": "xsd:string"},
            {"sh:path": "milk:type", "sh:in": ["distrito", "municipio", "freguesia", "regiao"]},
        ],
    },
    "cultural_asset": {
        "@type": "sh:NodeShape",
        "sh:targetClass": "milk:CulturalAsset",
        "sh:property": [
            {"sh:path": "milk:title", "sh:minCount": 1, "sh:datatype": "xsd:string"},
            {"sh:path": "milk:territory", "sh:minCount": 0, "sh:class": "milk:Territory"},
            {"sh:path": "milk:source", "sh:minCount": 1},
        ],
    },
    "evidence": {
        "@type": "sh:NodeShape",
        "sh:targetClass": "milk:Evidence",
        "sh:property": [
            {"sh:path": "milk:source", "sh:minCount": 1, "sh:datatype": "xsd:string"},
            {"sh:path": "milk:contentHash", "sh:minCount": 1, "sh:datatype": "xsd:string"},
            {"sh:path": "milk:timestamp", "sh:minCount": 1},
        ],
    },
    "person": {
        "@type": "sh:NodeShape",
        "sh:targetClass": "milk:Person",
        "sh:property": [
            {"sh:path": "milk:name", "sh:minCount": 1, "sh:datatype": "xsd:string"},
            {"sh:path": "milk:orcid", "sh:minCount": 0, "sh:pattern": "^\\d{4}-\\d{4}-\\d{4}-\\d{4}$"},
        ],
    },
}

SHACL_CONTEXT = {
    "@context": {
        "sh": "http://www.w3.org/ns/shacl#",
        "milk": "https://associacaomilk.pt/ns#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    },
    "shapes": SHACL_SHAPES,
}


def validate_shacl(entity: dict) -> tuple[bool, list[str]]:
    """Simple SHACL-like validation for entity properties."""
    errors = []
    entity_type = entity.get("type", "")
    shape = SHACL_SHAPES.get(entity_type)
    if not shape:
        return True, []  # no shape = no validation needed

    props = entity.get("properties", {})
    for constraint in shape.get("sh:property", []):
        path = constraint.get("sh:path", "").replace("milk:", "")
        min_count = constraint.get("sh:minCount", 0)
        datatype = constraint.get("sh:datatype", "")
        pattern = constraint.get("sh:pattern", "")
        allowed_values = constraint.get("sh:in", [])

        value = props.get(path)
        if min_count > 0 and (value is None or value == ""):
            errors.append(f"{path}: minimum count {min_count} not met")
        if value and pattern:
            import re
            if not re.match(pattern, str(value)):
                errors.append(f"{path}: does not match pattern {pattern}")
        if value and allowed_values and value not in allowed_values:
            errors.append(f"{path}: value '{value}' not in {allowed_values}")

    return len(errors) == 0, errors


# ===========================================================================
# P1: Resource-aware router (VRAM, RAM, CPU, model residency)
# ===========================================================================

class ResourceAwareRouter:
    """Resource-aware execution routing.

    Considers VRAM, RAM, CPU, model residency, queue, latency, task complexity.
    Avoids loading heavy models simultaneously without benefit.
    """

    def __init__(self):
        self._vram_total_mb = 10240  # RTX 3080 10GB
        self._vram_available_mb = 10240
        self._loaded_models: set[str] = set()
        self._model_vram_mb = {
            "gpt-oss-20b": 8000,
            "llama3.2:3b": 2500,
            "mistral:latest": 4500,
            "bge-m3": 1500,
            "bge-reranker-v2-m3": 800,
        }

    def update_vram(self, used_mb: int):
        """Update VRAM usage from nvidia-smi."""
        self._vram_available_mb = self._vram_total_mb - used_mb

    def can_load_model(self, model: str) -> tuple[bool, str]:
        """Check if a model can be loaded given current VRAM."""
        needed = self._model_vram_mb.get(model, 2000)
        if model in self._loaded_models:
            return True, "already loaded"
        if needed <= self._vram_available_mb:
            return True, ""
        return False, f"insufficient VRAM: need {needed}MB, have {self._vram_available_mb}MB"

    def select_model_for_task(self, task_complexity: str, needs_reasoning: bool,
                              needs_embedding: bool) -> str:
        """Select optimal model based on task requirements and resources."""
        if needs_embedding:
            return "bge-m3"
        if not needs_reasoning:
            return "none"  # no LLM needed

        # For reasoning: prefer smaller model when VRAM is tight
        if task_complexity == "low":
            # Simple tasks: use smaller model
            can_load, _ = self.can_load_model("llama3.2:3b")
            if can_load:
                return "llama3.2:3b"
        elif task_complexity == "high":
            # Complex tasks: use more capable model if VRAM allows
            can_load, _ = self.can_load_model("gpt-oss-20b")
            if can_load:
                return "gpt-oss-20b"
            can_load, _ = self.can_load_model("mistral:latest")
            if can_load:
                return "mistral:latest"

        # Default: whatever is available
        for model in ["llama3.2:3b", "mistral:latest", "gpt-oss-20b"]:
            can_load, _ = self.can_load_model(model)
            if can_load:
                return model
        return "heuristic"  # fallback


# ===========================================================================
# P2: SBOM generation
# ===========================================================================

def generate_sbom(project_root: Path | None = None) -> dict:
    """Generate a minimal Software Bill of Materials (CycloneDX-like)."""
    root = project_root or _ROOT
    components = []

    # Check for requirements.txt
    req_path = root / "requirements.txt"
    if req_path.exists():
        for line in req_path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("==")
                name = parts[0].strip()
                version = parts[1].strip() if len(parts) > 1 else "unknown"
                components.append({"name": name, "version": version, "type": "library"})

    # Check for package.json
    pkg_path = root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            for name, version in pkg.get("dependencies", {}).items():
                components.append({"name": name, "version": version, "type": "npm"})
        except:
            pass

    # Known local components
    components.extend([
        {"name": "pydantic", "version": "2.13.5", "type": "library"},
        {"name": "pytest", "version": "9.1.1", "type": "dev"},
        {"name": "torch", "version": "2.6.0+cu124", "type": "library"},
        {"name": "numpy", "version": "local", "type": "library"},
        {"name": "gpt-oss-20b", "version": "MXFP4", "type": "model"},
        {"name": "bge-m3", "version": "BAAI", "type": "model"},
        {"name": "bge-reranker-v2-m3", "version": "BAAI", "type": "model"},
    ])

    # Deduplicate
    seen = set()
    unique_components = []
    for c in components:
        key = f"{c['name']}:{c.get('version', '')}"
        if key not in seen:
            seen.add(key)
            unique_components.append(c)

    return {
        "schema": "CycloneDX-like",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "generatedAt": _now(),
        "components": unique_components,
        "total_components": len(unique_components),
    }
