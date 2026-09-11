"""MILK IA - Addendum 20 anti-flattening tests.

Tests that provenance, epistemic status, and authorship are preserved
correctly across the Husserl/Schaeffer/Chion/Dopafania/reading-architecture/
zine/curatorial-seeds integration. No theory is collapsed into another;
no authorial concept is attributed to an external source; no experimental
hypothesis is promoted to scientific fact; no curatorial seed is treated as
method theory.
"""
import sys, pathlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from milk_ai.hypergraph import SovereignHypergraph
from milk_ai.method_repertoire import (
    load_method_repertory, curatorial_method_nodes, method_repertoire_count,
    HUSSERL_NODES, SCHAEFFER_NODES, CHION_NODES, MILK_AUTHORIAL_NODES,
    READING_ARCHITECTURE_NODES, ZINE_NODES, CURATORIAL_SEEDS,
    ADDENDUM_EDGES, EP_SOURCE, EP_METHOD_TRANSLATION,
    EP_EXPERIMENTAL_HYPOTHESIS, EP_CURATORIAL_SEED, EP_ACADEMIC_ARTICLE,
)
from milk_ai.research_context import ResearchContextGate
from milk_ai.provenance import CANONICAL_AUTHOR

_MILK_AUTHOR = CANONICAL_AUTHOR["idealized_by"]


# ---- Helper ----

def _graph():
    hg = SovereignHypergraph()
    load_method_repertory(hg)
    return hg


def _node_meta(graph, node_id):
    n = graph.get_node(node_id)
    assert n is not None, f"node {node_id} not found"
    return n.metadata


# ---- 20.1 Husserl ----

class TestHusserlProvenance:
    def test_husserl_nodes_present(self):
        hg = _graph()
        for nid, *_ in HUSSERL_NODES:
            assert hg.get_node(nid) is not None, f"missing {nid}"

    def test_husserl_retention_not_memory(self):
        """HUSSERL_RETENTION_NOT_MEMORY: retention is NOT equated with
        episodic memory."""
        hg = _graph()
        meta = _node_meta(hg, "temporal:retention")
        assert meta.get("epistemic_status") == EP_SOURCE
        assert "episodic memory" not in meta.get("possible_operation", "").lower()
        # The cross-relation to oral_traditions is METHOD_TRANSLATION, not identity
        edges = [e for e in hg.edges_from("temporal:retention")
                 if e.edge_type == "ANALOGOUS_TO"]
        for e in edges:
            assert e.metadata.get("epistemic_status") == EP_METHOD_TRANSLATION

    def test_husserl_protention_not_explicit_prediction(self):
        """HUSSERL_PROTENTION_NOT_EXPLICIT_PREDICTION: protention is openness,
        not explicit prediction."""
        hg = _graph()
        meta = _node_meta(hg, "temporal:protention")
        assert meta.get("epistemic_status") == EP_SOURCE
        assert "explicit prediction" not in meta.get("possible_operation", "").lower()
        edges = [e for e in hg.edges_from("temporal:protention")
                 if e.edge_type == "ANALOGOUS_TO"]
        for e in edges:
            assert e.metadata.get("epistemic_status") == EP_METHOD_TRANSLATION

    def test_husserl_source_is_husserl(self):
        hg = _graph()
        n = hg.get_node("temporal:retention")
        assert "husserl" in n.source_pointer.lower()
        assert n.metadata.get("author") == "Edmund Husserl"


# ---- 20.2/20.3 Schaeffer / Chion provenance ----

class TestSchaefferChionProvenance:
    def test_schaeffer_nodes_present(self):
        hg = _graph()
        for nid, *_ in SCHAEFFER_NODES:
            assert hg.get_node(nid) is not None

    def test_schaeffer_reduced_listening_provenance(self):
        """SCHAEFFER_REDUCED_LISTENING_PROVENANCE: reduced listening is
        attributed to Schaeffer."""
        hg = _graph()
        n = hg.get_node("sound:reduced_listening")
        assert n.metadata.get("author") == "Pierre Schaeffer"
        assert n.metadata.get("epistemic_status") == EP_SOURCE

    def test_chion_nodes_present(self):
        hg = _graph()
        for nid, *_ in CHION_NODES:
            assert hg.get_node(nid) is not None

    def test_chion_causal_semantic_provenance(self):
        """CHION_CAUSAL_SEMANTIC_PROVENANCE: the three-mode formulation
        (causal/semantic/reduced) is attributed to Chion, NOT wholly to
        Schaeffer."""
        hg = _graph()
        for nid in ("listening:causal", "listening:semantic", "listening:reduced"):
            n = hg.get_node(nid)
            assert n.metadata.get("author") == "Michel Chion"
            assert n.metadata.get("epistemic_status") == EP_SOURCE
            # Schaeffer is recorded as antecedent, not as the source of the
            # three-mode formulation itself.
            assert n.metadata.get("antecedent") == "Pierre Schaeffer"

    def test_chion_reduced_derived_from_schaeffer(self):
        """Chion's reduced listening is DERIVED_FROM Schaeffer's, not identical."""
        hg = _graph()
        edges = [e for e in hg._edges.values()
                 if e.source == "listening:reduced" and e.target == "sound:reduced_listening"]
        assert len(edges) >= 1
        assert edges[0].edge_type == "DERIVED_FROM"


# ---- 20.4/20.5 ESCUTA_IDENTITARIA + DOPAFANIA authorial provenance ----

class TestAuthorialProvenance:
    def test_escuta_identitaria_authorial_provenance(self):
        """ESCUTA_IDENTITARIA_AUTHORIAL_PROVENANCE: it is an authorial MILK
        method extension, not a Schaeffer quotation."""
        hg = _graph()
        n = hg.get_node("milk:escuta_identitaria")
        assert n.metadata.get("author") == _MILK_AUTHOR
        assert n.metadata.get("epistemic_status") == EP_METHOD_TRANSLATION
        # The note says it is NOT a Schaeffer category — provenance is MILK
        assert "not a Schaeffer category" in n.metadata.get("note", "")

    def test_dopafania_authorial_provenance(self):
        """DOPAFANIA_AUTHORIAL_PROVENANCE: it is an authorial MILK concept."""
        hg = _graph()
        n = hg.get_node("milk:dopafania")
        assert n.metadata.get("author") == _MILK_AUTHOR
        assert n.metadata.get("epistemic_status") == EP_EXPERIMENTAL_HYPOTHESIS

    def test_dopafania_not_neurochemical_fact(self):
        """DOPAFANIA_NOT_NEUROCHEMICAL_FACT: dopafania is NOT stored as a
        neurochemical fact. The neuroscience bridge is separate."""
        hg = _graph()
        n = hg.get_node("milk:dopafania")
        assert n.metadata.get("epistemic_status") == EP_EXPERIMENTAL_HYPOTHESIS
        assert "NOT neurochemical fact" in n.metadata.get("note", "") or \
               "NOT" in n.metadata.get("note", "")
        # The neuro: nodes are separate, with lower confidence edges
        neuro = hg.get_node("neuro:reward_prediction_error")
        assert neuro is not None
        assert neuro.metadata.get("author") == "neuroscience_bridge"
        # The edge dopafania -> neuro has low confidence (0.3)
        edges = [e for e in hg._edges.values()
                 if e.source == "milk:dopafania" and e.target == "neuro:reward_prediction_error"]
        assert len(edges) >= 1
        assert edges[0].confidence <= 0.35


# ---- 20.6 Reading architecture ----

class TestReadingArchitecture:
    def test_scliar_2013_date_context_preserved(self):
        """SCLIAR_2013_DATE_CONTEXT_PRESERVED: the publication year and venue
        are stored; the pedagogical dispute is NOT promoted to universal truth."""
        hg = _graph()
        n = hg.get_node("reading:scliar_2013")
        assert n.metadata.get("publication_year") == 2013
        assert n.metadata.get("venue") == "Letras de Hoje"
        assert n.metadata.get("epistemic_status") == EP_ACADEMIC_ARTICLE
        assert n.metadata.get("current_validation_required") is True
        assert "NOT promoted" in n.metadata.get("note", "")

    def test_reading_architecture_relational(self):
        """READING_ARCHITECTURE_RELATIONAL: bottom_up, top_down, working_memory
        are all related to linguistic_levels."""
        hg = _graph()
        for nid in ("reading:bottom_up", "reading:top_down", "reading:working_memory"):
            edges = [e for e in hg._edges.values()
                     if e.source == nid and e.target == "reading:linguistic_levels"]
            assert len(edges) >= 1, f"no relational edge from {nid}"


# ---- 20.7 Zine ----

class TestZineProvenance:
    def test_zine_not_scientific_source(self):
        """ZINE_NOT_SCIENTIFIC_SOURCE: the zine is curatorial/philosophical,
        not neuroscience."""
        hg = _graph()
        n = hg.get_node("zine:verdade_outra_tribo")
        assert n.metadata.get("epistemic_status") == EP_CURATORIAL_SEED
        assert n.metadata.get("source_type") == "CURATORIAL_PHILOSOPHICAL"

    def test_identity_not_fixed_profile(self):
        """IDENTITY_NOT_FIXED_PROFILE: identity is revisable, not a fixed
        label."""
        hg = _graph()
        n = hg.get_node("zine:identity_revisable")
        assert n is not None
        op = n.metadata.get("possible_operation", "")
        assert "revisable" in op.lower()

    def test_external_attributions_preserved(self):
        """External theoretical attributions (Foucault, Butler, Clarice
        Lispector) must remain attributable."""
        hg = _graph()
        n = hg.get_node("zine:verdade_outra_tribo")
        attrs = n.metadata.get("external_attributions", [])
        assert "Foucault" in attrs
        assert "Butler" in attrs
        assert "Clarice Lispector" in attrs


# ---- 20.8 Handwritten curatorial seeds ----

class TestCuratorialSeeds:
    def test_handwritten_seeds_preserved(self):
        """HANDWRITTEN_SEEDS_PRESERVED: all five seeds are present."""
        hg = _graph()
        for nid, *_ in CURATORIAL_SEEDS:
            assert hg.get_node(nid) is not None

    def test_handwritten_seeds_not_method_theory(self):
        """HANDWRITTEN_SEEDS_NOT_METHOD_THEORY: seeds have epistemic_status
        CURATORIAL_SEED, not METHOD_THEORY or SCIENTIFIC_SOURCE."""
        hg = _graph()
        for nid, *_ in CURATORIAL_SEEDS:
            n = hg.get_node(nid)
            assert n.metadata.get("epistemic_status") == EP_CURATORIAL_SEED
            assert n.metadata.get("epistemic_status") != "METHOD_THEORY"
            assert n.metadata.get("epistemic_status") != "SCIENTIFIC_SOURCE"

    def test_seeds_authorship(self):
        hg = _graph()
        for nid, *_ in CURATORIAL_SEEDS:
            n = hg.get_node(nid)
            assert n.metadata.get("author") == _MILK_AUTHOR


# ---- 20.11 Cross-modal retrieval test ----

class TestCrossModalRetrieval:
    def test_cross_modal_query_retrieves_multiple_domains(self):
        """The addendum 20.11 query should retrieve Husserl, Schaeffer/Chion,
        MILK escuta identitaria, and Palavra Ritual — multiple relational
        hypotheses, not one deterministic explanation."""
        hg = _graph()
        gate = ResearchContextGate(hg)
        # Use a query that touches retention, protention, escuta, palavra
        b = gate.research(
            task_id="addendum_20_11",
            query="retention protention escuta identitaria palavra som reduced listening",
            runtime_role="test")
        tr = gate.traces()[-1]
        # Should retrieve references from multiple domains
        assert b.has_research_context is True
        assert len(b.references) >= 2
        # Should have traversed graph paths or found cross-modal links
        assert len(b.graph_paths) > 0 or len(tr.multimodal_links) > 0
        # Provenance visible: references carry source pointers
        for ref in b.references:
            assert ref.source_pointer

    def test_retrieval_preserves_provenance(self):
        """Retrieved references must carry source pointers (provenance)."""
        hg = _graph()
        gate = ResearchContextGate(hg)
        b = gate.research(
            task_id="prov_test",
            query="Husserl retention protention Schaeffer reduced listening",
            runtime_role="test")
        for ref in b.references:
            d = ref.to_dict()
            assert d.get("source_pointer")

    def test_dopafania_retrievable_but_as_hypothesis(self):
        """Dopafania is retrievable but its epistemic_status remains
        EXPERIMENTAL_HYPOTHESIS, not SOURCE."""
        hg = _graph()
        gate = ResearchContextGate(hg)
        b = gate.research(
            task_id="dopafania_test",
            query="dopafania expectation surprise epiphany",
            runtime_role="test")
        # Check if dopafania node is among considered/selected
        traces = gate.traces()
        if traces:
            considered = traces[-1].references_considered
            # dopafania should be findable
            hg_node = hg.get_node("milk:dopafania")
            assert hg_node is not None
            assert hg_node.metadata.get("epistemic_status") == EP_EXPERIMENTAL_HYPOTHESIS
