"""Tests for the Multimodal Relational Engine — Framework Conceptual."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.conceptual_engine import (
    MultimodalRelationalEngine, MODALITIES, EDGE_TYPES, load_framework,
)


class TestFrameworkLibrary:
    def test_framework_loads(self):
        fw = load_framework()
        assert fw["schema"] == "ia_milk.biblioteca.framework.v1"
        assert len(fw["documentos_fonte"]) >= 10

    def test_framework_has_canonical_identity(self):
        fw = load_framework()
        assert "0009-0007-6892-6570" in fw["identidade_canonica"]["orcid_idealizador"]
        assert "0009-0009-1781-4020" in fw["identidade_canonica"]["orcid_coautor"]

    def test_framework_has_all_documents(self):
        fw = load_framework()
        doc_ids = [d["id"] for d in fw["documentos_fonte"]]
        assert "doc_palavra_ritual" in doc_ids
        assert "doc_deriva_sentido" in doc_ids
        assert "doc_sussurro" in doc_ids
        assert "doc_toponomastica_qr" in doc_ids
        assert "doc_dois_joguinhos" in doc_ids
        assert "doc_sesc_estudo" in doc_ids

    def test_framework_has_conceptual_nodes(self):
        fw = load_framework()
        nodes = fw["framework_conceptual"]["nos"]
        for key in ["husserl", "schaeffer", "lyotard", "wagner", "jung",
                     "heisenberg", "hilbert", "graham", "lacan"]:
            assert key in nodes

    def test_framework_has_typed_edges(self):
        fw = load_framework()
        edges = fw["framework_conceptual"]["arestas_tipadas"]
        assert len(edges) >= 8
        types = {e["tipo"] for e in edges}
        assert "influência_documentada" in types
        assert "tensão_produtiva" in types
        assert "distinção_preservada" in types

    def test_framework_has_funding_strategy(self):
        fw = load_framework()
        fontes = fw["estrategia_financiamento"]["fontes_financiamento"]
        assert len(fontes) >= 5
        assert any("DGARTES" in f["fonte"] for f in fontes)

    def test_framework_has_campo_possivel(self):
        fw = load_framework()
        cp = fw["projeto_campo_possivel"]
        assert "Manuel da Maia" in cp["escola"]
        assert "portão" in cp["frase_chave"]

    def test_framework_has_ethical_framework(self):
        fw = load_framework()
        fe = fw["framework_etico"]
        assert "não maleficência" in fe["principios"]
        assert "consentimento informado" in fe["principios"]

    def test_framework_has_camada_publica(self):
        fw = load_framework()
        cp = fw["camada_publica"]
        assert "Perder o tempo sem perder o lugar" in cp["regra_navegacao"]
        assert "não explica" in cp["regra_frontend"]

    def test_framework_has_operational_rules(self):
        fw = load_framework()
        rules = fw["regras_operacionais"]
        assert len(rules) >= 9
        assert any("duplicado" in r for r in rules)


class TestRelationalEngine:
    def test_engine_builds_graph(self):
        engine = MultimodalRelationalEngine()
        assert engine.node_count > 30
        assert engine.edge_count > 30

    def test_nodes_by_type(self):
        engine = MultimodalRelationalEngine()
        docs = engine.nodes_by_type("documento")
        assert len(docs) >= 10
        dispositivos = engine.nodes_by_type("dispositivo_curatorial")
        assert len(dispositivos) >= 5

    def test_edges_by_type(self):
        engine = MultimodalRelationalEngine()
        needs = engine.edges_by_type("necessidade_pública_atende")
        assert len(needs) >= 5

    def test_neighbors(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("doc_palavra_ritual")
        assert len(nb) >= 2

    def test_multimodal_edges(self):
        engine = MultimodalRelationalEngine()
        sound_edges = engine.by_modality("sound")
        assert len(sound_edges) >= 1
        territory_edges = engine.by_modality("territory")
        assert len(territory_edges) >= 1

    def test_husserl_schaeffer_edge(self):
        engine = MultimodalRelationalEngine()
        influences = engine.edges_by_type("influência_documentada")
        hs = [e for e in influences if e["source"] == "husserl" and e["target"] == "schaeffer"]
        assert len(hs) == 1

    def test_wagner_lyotard_tension(self):
        engine = MultimodalRelationalEngine()
        tensions = engine.edges_by_type("tensão_produtiva")
        wl = [e for e in tensions if "wagner" in e["source"] and "lyotard" in e["target"]]
        assert len(wl) == 1

    def test_hilbert_graham_distinction(self):
        engine = MultimodalRelationalEngine()
        dists = engine.edges_by_type("distinção_preservada")
        hg = [e for e in dists if "hilbert" in e["source"] and "graham" in e["target"]]
        assert len(hg) == 1

    def test_campo_possivel_has_devices(self):
        engine = MultimodalRelationalEngine()
        applicable = engine.edges_by_type("dispositivo_aplicável_em")
        targets = {e["target"] for e in applicable}
        assert "projeto:campo_possivel" in targets

    def test_funding_connects_to_needs(self):
        engine = MultimodalRelationalEngine()
        funding_edges = engine.edges_by_type("financia")
        assert len(funding_edges) >= 5

    def test_path_finding(self):
        engine = MultimodalRelationalEngine()
        paths = engine.path_between("husserl", "schaeffer", max_depth=2)
        assert len(paths) >= 1

    def test_graph_output(self):
        engine = MultimodalRelationalEngine()
        g = engine.graph()
        assert g["schema"] == "ia_milk.motor_relacional_multimodal.v1"
        assert g["stats"]["nodes"] > 30
        assert g["stats"]["edges"] > 30

    def test_all_edge_types_defined(self):
        for et in EDGE_TYPES:
            assert isinstance(et, str) and len(et) > 0

    def test_all_modalities_defined(self):
        assert "text" in MODALITIES
        assert "sound" in MODALITIES
        assert "image" in MODALITIES
        assert "body" in MODALITIES
        assert "territory" in MODALITIES
