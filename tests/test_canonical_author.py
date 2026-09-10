"""Tests for canonical authorship identity — single source of truth.

Validates that the canonical author identity is correctly defined, exported,
and wired into all provenance, governance, and annotation structures.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.provenance import CANONICAL_AUTHOR, canonical_author_identity


class TestCanonicalAuthorIdentity:
    def test_required_fields_present(self):
        required = [
            "idealized_by", "artistic_name", "conceptual_author",
            "architectural_origin", "curatorial_method_author",
            "human_sovereign", "orcid",
        ]
        for field in required:
            assert field in CANONICAL_AUTHOR, f"missing field: {field}"

    def test_orcid_correct(self):
        assert CANONICAL_AUTHOR["orcid"] == "0009-0007-6892-6570"

    def test_orcid_not_wrong_value(self):
        assert CANONICAL_AUTHOR["orcid"] != "0009-0007-6992-6570"

    def test_author_name(self):
        assert "Eduardo" in CANONICAL_AUTHOR["idealized_by"]
        assert "Araújo" in CANONICAL_AUTHOR["idealized_by"]

    def test_artistic_name(self):
        assert CANONICAL_AUTHOR["artistic_name"] == "Eduardo Mauer"

    def test_all_author_roles_same_person(self):
        name = CANONICAL_AUTHOR["idealized_by"]
        for field in ["conceptual_author", "architectural_origin",
                      "curatorial_method_author", "human_sovereign"]:
            assert CANONICAL_AUTHOR[field] == name

    def test_canonical_author_identity_returns_copy(self):
        a = canonical_author_identity()
        a["test"] = "mutated"
        assert "test" not in CANONICAL_AUTHOR


class TestProvenanceIntegration:
    def test_sovereign_gate_includes_canonical_author(self):
        from milk_ai.sovereign_gate import run_gate, report_to_dict
        r = run_gate()
        d = report_to_dict(r)
        assert "canonical_author" in d["details"]
        assert "canonical_orcid" in d["details"]
        assert "0009-0007-6892-6570" in d["details"]["canonical_orcid"]

    def test_external_adapters_orcid_uses_canonical(self):
        from milk_ai.external_adapters import OrcidAdapter
        adapter = OrcidAdapter()
        assert adapter.known_orcids["eduardo_mauricio"] == "0009-0007-6892-6570"

    def test_evidence_bundle_prov_o_includes_canonical_person(self):
        from milk_ai.cognitive_control_plane import EvidenceBundle
        b = EvidenceBundle("task-prov", "trace-prov")
        b.add_evidence(source="test", content="prov test", content_hash="h")
        prov = b.to_prov_o()
        agents = prov.get("agents", [])
        person_agents = [a for a in agents if a.get("@type") == "prov:Person"]
        assert len(person_agents) >= 1
        assert "0009-0007-6892-6570" in person_agents[0].get("@id", "")
