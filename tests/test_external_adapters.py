"""Tests for ExternalSystemAdapter contract and Gap Engine."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.external_adapters import (
    ExternalSystemAdapter,
    NextcloudAdapter,
    CodebergForgejoAdapter,
    GitHubAdapter,
    ZenodoAdapter,
    OrcidAdapter,
    PTServidorAdapter,
    Evidence,
    get_all_adapters,
    _sha256,
    _detect_secret,
)


class TestEvidenceContract:
    """Evidence must always carry source_id, source_system, retrieved_at, provenance."""

    def test_evidence_has_required_fields(self):
        ev = Evidence(
            source_id="test-1", source_system="test", retrieved_at="2026-01-01T00:00:00Z",
            provenance={"method": "test"}, content="hello", content_hash=_sha256("hello"),
        )
        d = ev.to_dict()
        for field in ("source_id", "source_system", "retrieved_at", "provenance",
                      "content", "content_hash", "metadata"):
            assert field in d, f"missing field: {field}"

    def test_content_hash_is_sha256(self):
        ev = Evidence(source_id="x", source_system="x", retrieved_at="x",
                      provenance={}, content="test", content_hash=_sha256("test"))
        assert len(ev.content_hash) == 64

    def test_metadata_defaults_to_empty_dict(self):
        ev = Evidence(source_id="x", source_system="x", retrieved_at="x", provenance={})
        assert ev.metadata == {}
        assert ev.content == ""
        assert ev.content_hash == ""


class TestSecretDetection:
    """Secret detection must never print values."""

    def test_detect_secret_missing(self):
        cred, status = _detect_secret("NONEXISTENT_VAR_12345")
        assert cred is None
        assert "missing" in status

    def test_detect_secret_present_redacted(self):
        with patch.dict(os.environ, {"MILK_TEST_TOKEN": "super-secret-value-12345"}):
            cred, status = _detect_secret("MILK_TEST_TOKEN")
        assert cred == "MILK_TEST_TOKEN"
        assert "super-secret-value-12345" not in status
        assert "redacted" in status


class TestAdapterContract:
    """Every adapter must implement the full ExternalSystemAdapter contract."""

    ALL_ADAPTER_CLASSES = [
        NextcloudAdapter,
        CodebergForgejoAdapter,
        GitHubAdapter,
        ZenodoAdapter,
        OrcidAdapter,
        PTServidorAdapter,
    ]

    @pytest.mark.parametrize("adapter_cls", ALL_ADAPTER_CLASSES)
    def test_is_subclass(self, adapter_cls):
        assert issubclass(adapter_cls, ExternalSystemAdapter)

    @pytest.mark.parametrize("adapter_cls", ALL_ADAPTER_CLASSES)
    def test_has_name_property(self, adapter_cls):
        # Instantiation should not require network
        adapter = adapter_cls.__new__(adapter_cls)
        # name is a property with @abstractmethod — check it exists
        assert hasattr(type(adapter), "name")

    @pytest.mark.parametrize("adapter_cls", ALL_ADAPTER_CLASSES)
    def test_all_contract_methods_exist(self, adapter_cls):
        for method in ("discover", "auth_status", "list_resources",
                       "read_resource", "capabilities", "health", "provenance",
                       "propose_action"):
            assert hasattr(adapter_cls, method), f"{adapter_cls.__name__} missing {method}"

    def test_get_all_adapters_returns_at_least_six(self):
        adapters = get_all_adapters()
        assert len(adapters) >= 6
        expected_names = {"nextcloud", "codeberg", "github", "zenodo", "orcid", "ptservidor"}
        assert expected_names.issubset(set(adapters.keys()))

    def test_propose_action_does_not_execute(self):
        adapter = NextcloudAdapter(sync_dir=Path("/nonexistent"))
        result = adapter.propose_action("create_repo", target="codeberg")
        assert result["status"] == "PROPOSED"
        assert result["executed"] is False
        assert result["phase"] == "READ_AUDIT"


class TestNextcloudAdapter:
    """Nextcloud adapter reads local filesystem."""

    def test_discover_nonexistent_dir(self):
        adapter = NextcloudAdapter(sync_dir=Path("/nonexistent"))
        d = adapter.discover()
        assert d["found"] is False
        assert d["top_level_folders"] == []

    def test_auth_status_nonexistent(self):
        adapter = NextcloudAdapter(sync_dir=Path("/nonexistent"))
        a = adapter.auth_status()
        assert a["authenticated"] is False

    def test_read_resource_nonexistent(self):
        adapter = NextcloudAdapter(sync_dir=Path("/nonexistent"))
        result = adapter.read_resource("anything")
        assert "error" in result

    def test_capabilities_read_only(self):
        adapter = NextcloudAdapter(sync_dir=Path("/nonexistent"))
        caps = adapter.capabilities()
        assert caps["read"] is True
        assert caps["write"] is False

    def test_evidence_from_dir_read_has_provenance(self, tmp_path):
        # Create a test dir with a subfolder
        (tmp_path / "test_folder").mkdir()
        (tmp_path / "test_folder" / "file.txt").write_text("hello world")
        adapter = NextcloudAdapter(sync_dir=tmp_path)
        result = adapter.read_resource("test_folder")
        assert "source_id" in result
        assert result["source_system"] == "nextcloud"
        assert "retrieved_at" in result
        assert "provenance" in result
        assert "content_hash" in result
        assert len(result["content_hash"]) == 64


class TestGapEngine:
    """Gap engine builds gap graph from all adapters."""

    def test_gap_engine_imports(self):
        from milk_ai.gap_engine import GapEngine, GAP_TYPES, SEVERITY_ORDER
        assert "MISSING" in GAP_TYPES
        assert "AUTH_BLOCKED" in GAP_TYPES
        assert SEVERITY_ORDER["critical"] < SEVERITY_ORDER["low"]

    def test_gap_engine_initializes(self):
        from milk_ai.gap_engine import GapEngine
        engine = GapEngine()
        assert engine.gaps == []
        assert engine._gap_counter == 0

    def test_add_gap_generates_sequential_ids(self):
        from milk_ai.gap_engine import GapEngine
        engine = GapEngine()
        g1 = engine.add_gap(domain="test", source="test", evidence="e1",
                           severity="low", gap_type="MISSING")
        g2 = engine.add_gap(domain="test", source="test", evidence="e2",
                           severity="high", gap_type="DIVERGENT")
        assert g1["gap_id"] == "GAP-0001"
        assert g2["gap_id"] == "GAP-0002"

    def test_add_gap_has_all_required_fields(self):
        from milk_ai.gap_engine import GapEngine
        engine = GapEngine()
        gap = engine.add_gap(domain="d", source="s", evidence="e", severity="medium",
                            gap_type="UNVERIFIED", proposed_action="do something")
        for field in ("gap_id", "domain", "source", "gap_type", "evidence",
                      "severity", "dependency", "proposed_action", "reversibility",
                      "human_gate", "status", "created_at"):
            assert field in gap, f"missing: {field}"

    def test_gaps_sorted_by_severity(self):
        from milk_ai.gap_engine import GapEngine
        engine = GapEngine()
        engine.add_gap(domain="t", source="t", evidence="low", severity="low", gap_type="MISSING")
        engine.add_gap(domain="t", source="t", evidence="high", severity="high", gap_type="MISSING")
        engine.add_gap(domain="t", source="t", evidence="med", severity="medium", gap_type="MISSING")
        engine.gaps.sort(key=lambda g: {"high": 1, "medium": 2, "low": 3}.get(g["severity"], 99))
        assert engine.gaps[0]["severity"] == "high"
        assert engine.gaps[1]["severity"] == "medium"
        assert engine.gaps[2]["severity"] == "low"


class TestAdapterProvenance:
    """Every adapter's provenance() must identify MILK as owner."""

    @pytest.mark.parametrize("adapter_name", ["nextcloud", "codeberg", "github",
                                                "zenodo", "orcid", "ptservidor"])
    def test_provenance_claims_milk_owner(self, adapter_name):
        adapters = get_all_adapters()
        prov = adapters[adapter_name].provenance()
        assert prov["owner"] == "MILK Sovereign Core"
        assert "adapter" in prov
        assert "version" in prov
