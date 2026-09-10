"""MILK Sovereign Action Gate — operational gate for all MILK actions.

Three tiers:
  READ_AUTO          — leitura, inventário, pesquisa, health, comparação.
  WRITE_REVERSIBLE   — staging, drafts, derived data, metadata proposta;
                       exige snapshot/diff/rollback/receipt.
  PUBLIC_OR_IRREVERSIBLE — publicação Zenodo, produção PTServidor, delete,
                            alteração destrutiva, push; exige human approval.

Every action produces a receipt with before_hash/after_hash/rollback info.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Action tiers
READ_AUTO = "READ_AUTO"
WRITE_REVERSIBLE = "WRITE_REVERSIBLE"
PUBLIC_OR_IRREVERSIBLE = "PUBLIC_OR_IRREVERSIBLE"

TIER_ORDER = [READ_AUTO, WRITE_REVERSIBLE, PUBLIC_OR_IRREVERSIBLE]

# Auto-approval rules for READ_AUTO
AUTO_APPROVED_ACTIONS = {
    "discover", "auth_status", "list_resources", "read_resource", "search",
    "health", "capabilities", "provenance", "audit", "compare", "inventory",
    "gap_analysis", "code_audit",
}

# Reversible write actions (require snapshot but auto-approved)
REVERSIBLE_ACTIONS = {
    "create_draft", "update_draft_metadata", "stage_derived", "create_proposal",
    "update_manifest", "write_receipt",
}

# Public/irreversible actions (require explicit human approval)
PUBLIC_ACTIONS = {
    "publish_zenodo", "deploy_production", "delete_resource", "force_push",
    "git_push", "create_doi", "modify_orcid", "deploy_ptservidor",
}


@dataclass
class ActionReceipt:
    """Receipt for a completed or proposed action."""
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
    status: str = "proposed"  # proposed, approved, executed, rejected, failed

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @staticmethod
    def from_dict(d: dict) -> "ActionReceipt":
        return ActionReceipt(**{k: d[k] for k in ActionReceipt.__dataclass_fields__ if k in d})


class ActionGate:
    """Sovereign Action Gate — validates and logs all MILK actions."""

    def __init__(self, receipts_path: Path | None = None):
        self.root = Path(__file__).resolve().parents[2]
        self.receipts_path = receipts_path or self.root / "state" / "action_receipts.json"
        self.receipts: list[dict] = self._load_receipts()
        self._counter = len(self.receipts)

    def _load_receipts(self) -> list[dict]:
        if self.receipts_path.exists():
            return json.loads(self.receipts_path.read_text(encoding="utf-8"))
        return []

    def _save_receipts(self):
        self.receipts_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipts_path.write_text(json.dumps(self.receipts, ensure_ascii=False, indent=2),
                                       encoding="utf-8")

    def _next_id(self) -> str:
        self._counter += 1
        return f"ACT-{self._counter:04d}"

    def classify(self, action: str) -> str:
        """Classify an action into a tier."""
        if action in AUTO_APPROVED_ACTIONS or action.endswith("_read") or action.endswith("_audit"):
            return READ_AUTO
        if action in REVERSIBLE_ACTIONS or action.endswith("_draft") or action.endswith("_proposal"):
            return WRITE_REVERSIBLE
        if action in PUBLIC_ACTIONS or action.startswith("publish_") or action.startswith("deploy_"):
            return PUBLIC_OR_IRREVERSIBLE
        # Default: most restrictive
        return PUBLIC_OR_IRREVERSIBLE

    def request(self, *, action: str, actor: str = "milk_system", source: str = "",
                target: str = "", evidence: str = "", before_hash: str = "",
                human_approved: bool = False, force_tier: str | None = None) -> dict:
        """Request an action through the gate. Returns a receipt dict.

        For READ_AUTO: auto-approved, status=executed.
        For WRITE_REVERSIBLE: auto-approved, status=executed, requires rollback plan.
        For PUBLIC_OR_IRREVERSIBLE: requires human_approved=True, else status=proposed.
        """
        tier = force_tier or self.classify(action)
        receipt = ActionReceipt(
            action_id=self._next_id(), actor=actor, action=action, tier=tier,
            source=source, target=target, timestamp=_now(),
            evidence=evidence, before_hash=before_hash,
            reversible=tier != PUBLIC_OR_IRREVERSIBLE,
            rollback="", human_gate=tier == PUBLIC_OR_IRREVERSIBLE,
            status="proposed"
        )

        if tier == READ_AUTO:
            receipt.status = "approved"
            receipt.human_gate = False
        elif tier == WRITE_REVERSIBLE:
            receipt.status = "approved"
            receipt.rollback = f"revert {target} to before_hash={before_hash[:16]}"
        elif tier == PUBLIC_OR_IRREVERSIBLE:
            if human_approved:
                receipt.status = "approved"
                receipt.reversible = False
            else:
                receipt.status = "proposed"
                receipt.reversible = False

        self.receipts.append(receipt.to_dict())
        self._save_receipts()
        return receipt.to_dict()

    def execute_with_receipt(self, *, action: str, actor: str = "milk_system",
                             source: str = "", target: str = "",
                             fn: Callable | None = None,
                             before_state: str = "", human_approved: bool = False) -> dict:
        """Execute an action with full receipt lifecycle.

        1. Requests the action through the gate.
        2. If approved, executes fn() and records after_hash.
        3. If not approved, returns receipt with status=proposed.
        """
        before_hash = _sha256(before_state) if before_state else ""
        receipt = self.request(action=action, actor=actor, source=source, target=target,
                               before_hash=before_hash, human_approved=human_approved)

        if receipt["status"] != "approved":
            return receipt

        if fn:
            try:
                result = fn()
                after_state = str(result)
                receipt["after_hash"] = _sha256(after_state)[:16] if after_state else ""
                receipt["status"] = "executed"
            except Exception as e:
                receipt["status"] = "failed"
                receipt["evidence"] = f"ERROR: {e}"
        else:
            receipt["status"] = "executed"

        # Update in receipts list
        self.receipts[-1] = receipt
        self._save_receipts()
        return receipt

    def summary(self) -> dict:
        return {
            "total_actions": len(self.receipts),
            "by_tier": {t: sum(1 for r in self.receipts if r["tier"] == t) for t in TIER_ORDER},
            "by_status": {s: sum(1 for r in self.receipts if r["status"] == s)
                          for s in ("proposed", "approved", "executed", "rejected", "failed")},
            "pending_human_gate": [r for r in self.receipts
                                   if r["tier"] == PUBLIC_OR_IRREVERSIBLE and r["status"] == "proposed"],
        }
