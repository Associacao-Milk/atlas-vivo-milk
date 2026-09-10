"""Tests for Action Gate and extended adapters."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.action_gate import (
    ActionGate, ActionReceipt, READ_AUTO, WRITE_REVERSIBLE,
    PUBLIC_OR_IRREVERSIBLE, AUTO_APPROVED_ACTIONS, REVERSIBLE_ACTIONS, PUBLIC_ACTIONS,
)
from milk_ai.external_adapters import (
    LocalFSAdapter, CloudSyncAdapter, OneDriveAdapter, DockerAdapter,
    GitAdapter, BoxAdapter, Base44Adapter, get_all_adapters,
)


# ---- Action Gate tests ----

class TestActionGateClassification:
    """Action classification must correctly assign tiers."""

    def test_read_auto_actions(self):
        gate = ActionGate()
        for action in ["discover", "read_resource", "search", "health", "audit"]:
            assert gate.classify(action) == READ_AUTO

    def test_write_reversible_actions(self):
        gate = ActionGate()
        for action in ["create_draft", "stage_derived", "update_manifest"]:
            assert gate.classify(action) == WRITE_REVERSIBLE

    def test_public_irreversible_actions(self):
        gate = ActionGate()
        for action in ["publish_zenodo", "deploy_production", "delete_resource", "git_push"]:
            assert gate.classify(action) == PUBLIC_OR_IRREVERSIBLE

    def test_unknown_action_defaults_to_most_restrictive(self):
        gate = ActionGate()
        assert gate.classify("unknown_destructive_action") == PUBLIC_OR_IRREVERSIBLE


class TestActionGateReceipt:
    """Receipts must carry all required fields."""

    def test_read_auto_receipt_auto_approved(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        r = gate.request(action="discover", actor="test")
        assert r["status"] == "approved"
        assert r["tier"] == READ_AUTO
        assert r["human_gate"] is False

    def test_write_reversible_receipt_auto_approved(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        r = gate.request(action="create_draft", actor="test", target="file.txt")
        assert r["status"] == "approved"
        assert r["tier"] == WRITE_REVERSIBLE
        assert r["reversible"] is True
        assert "rollback" in r

    def test_public_action_requires_human_approval(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        r = gate.request(action="publish_zenodo", actor="test")
        assert r["status"] == "proposed"
        assert r["tier"] == PUBLIC_OR_IRREVERSIBLE
        assert r["human_gate"] is True
        assert r["reversible"] is False

    def test_public_action_approved_with_human_flag(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        r = gate.request(action="publish_zenodo", actor="test", human_approved=True)
        assert r["status"] == "approved"

    def test_receipt_has_all_fields(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "receipts.json")
        r = gate.request(action="read_resource", actor="test", source="nc", target="file",
                        evidence="reading file", before_hash="abc123")
        for field in ("action_id", "actor", "action", "tier", "source", "target",
                      "timestamp", "evidence", "before_hash", "after_hash",
                      "reversible", "rollback", "human_gate", "status"):
            assert field in r, f"missing field: {field}"

    def test_receipts_persist(self, tmp_path):
        path = tmp_path / "receipts.json"
        gate = ActionGate(receipts_path=path)
        gate.request(action="discover", actor="test1")
        gate.request(action="read_resource", actor="test2")
        # Reload
        gate2 = ActionGate(receipts_path=path)
        assert len(gate2.receipts) == 2

    def test_execute_with_receipt_executes_fn(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "r.json")
        result = gate.execute_with_receipt(
            action="discover", actor="test",
            fn=lambda: "success",
            before_state="before",
        )
        assert result["status"] == "executed"
        assert "after_hash" in result

    def test_execute_with_receipt_blocks_unapproved(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "r.json")
        result = gate.execute_with_receipt(
            action="publish_zenodo", actor="test",
            fn=lambda: "should_not_execute",
        )
        assert result["status"] == "proposed"

    def test_summary(self, tmp_path):
        gate = ActionGate(receipts_path=tmp_path / "r.json")
        gate.request(action="discover", actor="t")
        gate.request(action="create_draft", actor="t")
        gate.request(action="publish_zenodo", actor="t")
        s = gate.summary()
        assert s["total_actions"] == 3
        assert s["by_tier"][READ_AUTO] == 1
        assert s["by_tier"][WRITE_REVERSIBLE] == 1
        assert s["by_tier"][PUBLIC_OR_IRREVERSIBLE] == 1
        assert len(s["pending_human_gate"]) == 1


# ---- Extended adapter tests ----

class TestExtendedAdapters:
    """Test the new adapters added in Phase 3."""

    def test_get_all_adapters_returns_thirteen(self):
        adapters = get_all_adapters()
        assert len(adapters) == 13
        expected = {"localfs", "cloudsync", "nextcloud", "onedrive", "github",
                    "codeberg", "zenodo", "orcid", "docker", "git", "box",
                    "base44", "ptservidor"}
        assert set(adapters.keys()) == expected

    def test_all_adapters_have_search_method(self):
        adapters = get_all_adapters()
        for name, adapter in adapters.items():
            assert hasattr(adapter, "search"), f"{name} missing search()"

    def test_localfs_discover(self):
        adapter = LocalFSAdapter()
        d = adapter.discover()
        assert d["found"] is True

    def test_localfs_read_resource(self):
        adapter = LocalFSAdapter()
        result = adapter.read_resource("README.md")
        if "content_hash" in result:
            assert len(result["content_hash"]) == 64

    def test_localfs_search(self):
        adapter = LocalFSAdapter()
        result = adapter.search("manifest", limit=5)
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_cloudsync_discover(self):
        adapter = CloudSyncAdapter()
        d = adapter.discover()
        assert "sources" in d
        assert isinstance(d["count"], int)

    def test_onedrive_discover(self):
        adapter = OneDriveAdapter()
        d = adapter.discover()
        assert "found" in d

    def test_git_discover(self):
        adapter = GitAdapter()
        d = adapter.discover()
        assert d["has_git"] is True

    def test_git_list_resources(self):
        adapter = GitAdapter()
        r = adapter.list_resources()
        assert "branches" in r
        assert "remotes" in r
        assert len(r["branches"]) > 0

    def test_git_read_log(self):
        adapter = GitAdapter()
        result = adapter.read_resource("log:5")
        if "content_hash" in result:
            assert len(result["content_hash"]) == 64
            assert result["source_system"] == "git"

    def test_docker_discover(self):
        adapter = DockerAdapter()
        d = adapter.discover()
        assert "available" in d

    def test_box_discover(self):
        adapter = BoxAdapter()
        d = adapter.discover()
        assert "found" in d

    def test_base44_discover(self):
        adapter = Base44Adapter()
        d = adapter.discover()
        assert "cli_found" in d

    def test_base44_is_tool_only(self):
        adapter = Base44Adapter()
        caps = adapter.capabilities()
        assert caps.get("sovereign_core_dependency") is False

    def test_all_adapters_provenance_owner(self):
        adapters = get_all_adapters()
        for name, adapter in adapters.items():
            prov = adapter.provenance()
            assert prov["owner"] == "MILK Sovereign Core", f"{name} owner not MILK"
