"""Tests for canonical authorship identity — single source of truth.

Validates that the canonical author identity is correctly defined, exported,
and wired into all provenance, governance, and annotation structures.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.provenance import (
    CANONICAL_AUTHOR, CANONICAL_AUTHOR_NUNO, CANONICAL_AUTHORS,
    canonical_author_identity, canonical_nuno_identity,
    all_canonical_authors, resolve_author_by_orcid,
)


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


class TestNunoIdentity:
    def test_nuno_required_fields(self):
        required = ["author", "artistic_name", "signature", "orcid", "role", "works"]
        for field in required:
            assert field in CANONICAL_AUTHOR_NUNO, f"missing field: {field}"

    def test_nuno_orcid(self):
        assert CANONICAL_AUTHOR_NUNO["orcid"] == "0009-0009-1781-4020"

    def test_nuno_artistic_name(self):
        assert CANONICAL_AUTHOR_NUNO["artistic_name"] == "Nuno A"

    def test_nuno_signature_preserved(self):
        assert CANONICAL_AUTHOR_NUNO["signature"] == "Nuno A"

    def test_nuno_full_name(self):
        assert "Nuno Filipe" in CANONICAL_AUTHOR_NUNO["author"]
        assert "Araújo" in CANONICAL_AUTHOR_NUNO["author"]

    def test_nuno_works_include_guia_queer(self):
        works = CANONICAL_AUTHOR_NUNO["works"]
        assert any("Guia Queer" in w for w in works)
        assert any("fotográfica" in w for w in works)
        assert any("página" in w for w in works)

    def test_genealogical_separation(self):
        """Eduardo and Nuno are distinct authors with distinct ORCIDs."""
        assert CANONICAL_AUTHOR["orcid"] != CANONICAL_AUTHOR_NUNO["orcid"]
        assert CANONICAL_AUTHOR["idealized_by"] != CANONICAL_AUTHOR_NUNO["author"]
        assert CANONICAL_AUTHOR["artistic_name"] != CANONICAL_AUTHOR_NUNO["artistic_name"]

    def test_all_canonical_authors_has_both(self):
        authors = all_canonical_authors()
        assert "eduardo_mauer" in authors
        assert "nuno_a" in authors
        assert authors["eduardo_mauer"]["orcid"] == "0009-0007-6892-6570"
        assert authors["nuno_a"]["orcid"] == "0009-0009-1781-4020"

    def test_resolve_by_orcid_eduardo(self):
        a = resolve_author_by_orcid("0009-0007-6892-6570")
        assert a is not None
        assert a["artistic_name"] == "Eduardo Mauer"

    def test_resolve_by_orcid_nuno(self):
        a = resolve_author_by_orcid("0009-0009-1781-4020")
        assert a is not None
        assert a["artistic_name"] == "Nuno A"

    def test_resolve_by_orcid_unknown(self):
        assert resolve_author_by_orcid("0000-0000-0000-0000") is None

    def test_canonical_nuno_identity_returns_copy(self):
        a = canonical_nuno_identity()
        a["test"] = "mutated"
        assert "test" not in CANONICAL_AUTHOR_NUNO

    def test_external_adapters_has_nuno_a_orcid(self):
        from milk_ai.external_adapters import OrcidAdapter
        adapter = OrcidAdapter()
        assert adapter.known_orcids["nuno_a"] == "0009-0009-1781-4020"
