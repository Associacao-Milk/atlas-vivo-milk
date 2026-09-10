"""Tests for Sovereign Hypergraph Research Consciousness."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.hypergraph import (
    SovereignHypergraph, HyperNode, HyperEdge, ReferenceCapsule,
    ResearchGap, DiscoveryPath,
    NODE_TYPES, EDGE_TYPES, MULTIMODAL_TYPES, MULTISENSORY_DIMENSIONS,
    AESTHETIC_DIMENSIONS, TEMPORAL_STATES, VALIDATION_STATES,
)


class TestHypergraphTypes:
    def test_node_types_comprehensive(self):
        assert len(NODE_TYPES) >= 45
        for nt in ["AUTHOR", "PLACE", "TERRITORY", "METHOD", "EMOTION", "RESEARCH_GAP"]:
            assert nt in NODE_TYPES

    def test_edge_types_comprehensive(self):
        assert len(EDGE_TYPES) >= 32
        for et in ["AUTHORED_BY", "INSPIRED_BY", "CONTRADICTS", "RESONATES_WITH",
                   "SUCCESSFUL_FOR", "AESTHETICALLY_LINKED"]:
            assert et in EDGE_TYPES

    def test_multimodal_types(self):
        assert len(MULTIMODAL_TYPES) >= 24

    def test_multisensory_dimensions(self):
        assert len(MULTISENSORY_DIMENSIONS) >= 19
        for d in ["SILENCE", "ABSENCE", "ATMOSPHERE", "SURPRISE", "RUPTURE"]:
            assert d in MULTISENSORY_DIMENSIONS

    def test_aesthetic_dimensions(self):
        assert len(AESTHETIC_DIMENSIONS) >= 20

    def test_temporal_states(self):
        assert "PAST" in TEMPORAL_STATES
        assert "PRESENT" in TEMPORAL_STATES
        assert "POSSIBLE_FUTURE" in TEMPORAL_STATES


class TestHyperNode:
    def test_valid_node(self):
        n = HyperNode(id="test:1", type="AUTHOR", label="Test")
        assert n.type == "AUTHOR"
        assert n.validation_state == "pending"
        assert n.temporal_state == "present"

    def test_invalid_node_type_rejected(self):
        with pytest.raises(ValueError):
            HyperNode(id="x", type="INVALID_TYPE")

    def test_invalid_validation_state(self):
        with pytest.raises(ValueError):
            HyperNode(id="x", type="AUTHOR", validation_state="invalid")

    def test_invalid_temporal_state(self):
        with pytest.raises(ValueError):
            HyperNode(id="x", type="AUTHOR", temporal_state="future")

    def test_node_to_dict(self):
        n = HyperNode(id="t:1", type="PLACE", label="Alfama", modality="territory")
        d = n.to_dict()
        assert d["id"] == "t:1"
        assert d["modality"] == "territory"


class TestHyperEdge:
    def test_valid_edge(self):
        e = HyperEdge(id="e:1", source="a", edge_type="INSPIRED_BY", target="b")
        assert e.edge_type == "INSPIRED_BY"
        assert e.confidence == 0.0

    def test_invalid_edge_type_rejected(self):
        with pytest.raises(ValueError):
            HyperEdge(id="x", source="a", edge_type="INVALID", target="b")

    def test_edge_to_dict(self):
        e = HyperEdge(id="e:1", source="a", edge_type="RESONATES_WITH", target="b",
                      confidence=0.9)
        d = e.to_dict()
        assert d["confidence"] == 0.9


class TestSovereignHypergraph:
    def _build_test_graph(self):
        hg = SovereignHypergraph()
        hg.add_node(HyperNode(id="author:eduardo", type="AUTHOR", label="Eduardo Mauer", modality="text"))
        hg.add_node(HyperNode(id="author:nuno", type="AUTHOR", label="Nuno A", modality="text"))
        hg.add_node(HyperNode(id="place:alfama", type="PLACE", label="Alfama", modality="territory"))
        hg.add_node(HyperNode(id="method:boal", type="METHOD", label="Teatro do Oprimido", modality="body"))
        hg.add_node(HyperNode(id="sound:sussurro", type="SOUND", label="O Sussurro", modality="sound"))
        hg.add_node(HyperNode(id="concept:wabi_sabi", type="AESTHETIC", label="Wabi-Sabi", modality="image"))
        hg.add_edge(HyperEdge(id="e:1", source="author:eduardo", edge_type="AUTHORED_BY", target="author:eduardo"))
        hg.add_edge(HyperEdge(id="e:2", source="place:alfama", edge_type="LOCATED_IN", target="place:alfama"))
        hg.add_edge(HyperEdge(id="e:3", source="method:boal", edge_type="INSPIRED_BY", target="author:eduardo"))
        hg.add_edge(HyperEdge(id="e:4", source="sound:sussurro", edge_type="LOCATED_IN", target="place:alfama"))
        hg.add_edge(HyperEdge(id="e:5", source="concept:wabi_sabi", edge_type="AESTHETICALLY_LINKED", target="sound:sussurro"))
        hg.add_edge(HyperEdge(id="e:6", source="method:boal", edge_type="SUCCESSFUL_FOR", target="territorial_curation",
                             confidence=0.96, outcome_score=0.9, validation_state="validated"))
        return hg

    def test_graph_builds(self):
        hg = self._build_test_graph()
        assert hg.node_count >= 6
        assert hg.edge_count >= 6

    def test_nodes_by_type(self):
        hg = self._build_test_graph()
        authors = hg.nodes_by_type("AUTHOR")
        assert len(authors) == 2

    def test_nodes_by_modality(self):
        hg = self._build_test_graph()
        territory = hg.nodes_by_modality("territory")
        assert len(territory) >= 1
        sound = hg.nodes_by_modality("sound")
        assert len(sound) >= 1

    def test_edges_by_type(self):
        hg = self._build_test_graph()
        inspired = hg.edges_by_type("INSPIRED_BY")
        assert len(inspired) >= 1

    def test_neighbors(self):
        hg = self._build_test_graph()
        nb = hg.neighbors("place:alfama")
        assert len(nb) >= 1

    def test_traverse(self):
        hg = self._build_test_graph()
        adj = hg.traverse("method:boal", max_depth=3)
        assert "method:boal" in adj
        assert len(adj) >= 1

    def test_path_between(self):
        hg = self._build_test_graph()
        paths = hg.path_between("concept:wabi_sabi", "place:alfama", max_depth=4)
        assert len(paths) >= 1

    def test_reference_capsule(self):
        hg = self._build_test_graph()
        cap = hg.create_capsule("method:boal", relevance=0.95)
        assert cap is not None
        assert cap.label == "Teatro do Oprimido"
        assert cap.relevance == 0.95
        assert len(cap.key_relations) >= 1

    def test_capsules_for_context(self):
        hg = self._build_test_graph()
        caps = hg.capsules_for_context(["method:boal", "place:alfama", "sound:sussurro"])
        assert len(caps) == 3

    def test_research_gap(self):
        hg = self._build_test_graph()
        gap = hg.create_gap("What sounds exist in Alfama?", territory="Alfama")
        assert gap.question == "What sounds exist in Alfama?"
        assert gap.territory == "Alfama"
        results = hg.search_gaps("alfama")
        assert len(results) >= 1

    def test_discovery_path(self):
        hg = self._build_test_graph()
        path = hg.create_path("serendipity", ["wabi_sabi", "sussurro", "alfama"],
                              description="wabi-sabi → sound → territory")
        assert path.path_type == "serendipity"
        assert len(path.nodes) == 3

    def test_contradiction_preservation(self):
        hg = self._build_test_graph()
        hg.register_contradiction("source_a", "source_b",
                                  evidence_a="EB001", evidence_b="EB002",
                                  description="conflicting accounts")
        assert len(hg._contradictions) == 1
        assert hg._contradictions[0]["description"] == "conflicting accounts"

    def test_temporal_link(self):
        hg = self._build_test_graph()
        hg.link_temporal("place:alfama", "past", "historical account")
        assert len(hg._temporal_links) == 1

    def test_outcome_edge(self):
        hg = self._build_test_graph()
        outcomes = hg.edges_by_type("SUCCESSFUL_FOR")
        assert len(outcomes) >= 1
        assert outcomes[0].confidence == 0.96
        assert outcomes[0].outcome_score == 0.9

    def test_record_outcome(self):
        hg = SovereignHypergraph()
        hg.record_outcome("method:schafer", "territorial_curation", success=True,
                          confidence=0.88, score=0.92)
        outcomes = hg.edges_by_type("SUCCESSFUL_FOR")
        assert len(outcomes) == 1
        assert outcomes[0].confidence == 0.88

    def test_aesthetic_neighbors(self):
        hg = self._build_test_graph()
        aest = hg.aesthetic_neighbors("concept:wabi_sabi")
        assert len(aest) >= 1
        assert any(n.label == "O Sussurro" for n in aest)

    def test_multimodal_neighbors(self):
        hg = self._build_test_graph()
        mm = hg.multimodal_neighbors("place:alfama")
        assert "sound" in mm
        assert len(mm["sound"]) >= 1

    def test_stats(self):
        hg = self._build_test_graph()
        s = hg.stats()
        assert s["nodes"] >= 6
        assert s["edges"] >= 6
        assert s["node_types"] >= 3
        assert s["edge_types"] >= 3
        assert s["modalities"] >= 3

    def test_authorship_immutability(self):
        """Eduardo and Nuno are distinct entities. Identity fusion forbidden."""
        hg = self._build_test_graph()
        eduardo = hg.get_node("author:eduardo")
        nuno = hg.get_node("author:nuno")
        assert eduardo is not None
        assert nuno is not None
        assert eduardo.id != nuno.id
        assert eduardo.label != nuno.label


class TestTokenEfficiency:
    def test_capsule_is_compact(self):
        hg = SovereignHypergraph()
        hg.add_node(HyperNode(id="test:1", type="DOCUMENT", label="Test doc",
                              modality="text", source_pointer="hash:abc"))
        cap = hg.create_capsule("test:1")
        d = cap.to_dict()
        assert "source_pointer" in d
        assert d["source_pointer"] == "hash:abc"
        # capsule should NOT contain full content
        assert "content" not in d
        assert "text" not in d


class TestResearchBeforeReasoning:
    def test_gap_searchable_when_evidence_insufficient(self):
        hg = SovereignHypergraph()
        hg.create_gap("What is the oral history of Oleiros?",
                      missing_evidence=["oral recordings", "junta actas"],
                      territory="Oleiros")
        results = hg.search_gaps("oleiros")
        assert len(results) == 1
        assert "oral recordings" in results[0].missing_evidence
