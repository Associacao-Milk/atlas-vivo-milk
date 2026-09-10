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


class TestExtendedFramework:
    def test_camadas_arquitetura(self):
        engine = MultimodalRelationalEngine()
        camadas = engine.nodes_by_type("camada_arquitetura")
        assert len(camadas) >= 7  # 7 camadas arquitecturais

    def test_dispositivos_interacao(self):
        engine = MultimodalRelationalEngine()
        dispositivos = engine.nodes_by_type("dispositivo_interacao")
        assert len(dispositivos) >= 5
        nomes = {d["nome"] for d in dispositivos}
        assert "Ouvido Pensante" in nomes
        assert "Espect-Ator" in nomes
        assert "Vazio de Ressonância" in nomes

    def test_protocolos_confiabilidade(self):
        engine = MultimodalRelationalEngine()
        protos = engine.nodes_by_type("protocolo")
        assert len(protos) >= 3

    def test_governanca_camadas(self):
        engine = MultimodalRelationalEngine()
        gov = engine.nodes_by_type("camada_governanca")
        assert len(gov) >= 7  # Fonte, Evidência, Interpretação, Hipótese, Proposta, Decisão, Publicação

    def test_opera_neon_node(self):
        engine = MultimodalRelationalEngine()
        portals = engine.nodes_by_type("portal_navegacao")
        assert len(portals) >= 1
        assert "Ópera Néon" in portals[0]["nome"]

    def test_tecnicas_multimodais(self):
        engine = MultimodalRelationalEngine()
        tecnicas = engine.nodes_by_type("tecnica_multimodal")
        assert len(tecnicas) >= 9

    def test_gestao_estrategica(self):
        engine = MultimodalRelationalEngine()
        modulos = engine.nodes_by_type("modulo_estrategico")
        assert len(modulos) >= 3  # NDIF, LCAFC, DCAN

    def test_adorno_node(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("adorno")
        assert len(nb) >= 1  # should connect to foucault and marcuse

    def test_boal_node(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("boal")
        assert len(nb) >= 2  # connects to habermas and campo_possivel

    def test_extended_graph_size(self):
        engine = MultimodalRelationalEngine()
        assert engine.node_count >= 60  # significantly larger after extension
        assert engine.edge_count >= 50

    def test_framework_has_camadas(self):
        fw = load_framework()
        assert "camadas_arquitetura" in fw
        assert len(fw["camadas_arquitetura"]) == 7

    def test_framework_has_memoria_relacional(self):
        fw = load_framework()
        assert "memoria_relacional" in fw
        assert "Alfama" in fw["memoria_relacional"]["exemplo_cadeia"]

    def test_framework_has_cronologia(self):
        fw = load_framework()
        assert "cronologia_handover" in fw
        assert len(fw["cronologia_handover"]) >= 7

    def test_framework_has_gestao_estrategica(self):
        fw = load_framework()
        assert "gestao_estrategica" in fw
        assert "ndif" in fw["gestao_estrategica"]
        assert "lcafc" in fw["gestao_estrategica"]
        assert "dcan" in fw["gestao_estrategica"]


class TestDossieTerritorial:
    def test_dossie_territorial_present(self):
        fw = load_framework()
        assert "dossie_territorial" in fw
        assert "Territorial" in fw["dossie_territorial"]["titulo"]

    def test_three_motores_territoriais(self):
        engine = MultimodalRelationalEngine()
        motores = engine.nodes_by_type("motor_territorial")
        assert len(motores) >= 3
        nomes = {m["nome"] for m in motores}
        assert "Situação Territorial" in nomes
        assert "Densidade Relacional" in nomes

    def test_six_tipologias_infraestrutura(self):
        engine = MultimodalRelationalEngine()
        tipos = engine.nodes_by_type("tipologia_infraestrutura")
        assert len(tipos) >= 6

    def test_plataformas_referencia(self):
        engine = MultimodalRelationalEngine()
        plats = engine.nodes_by_type("plataforma_referencia")
        assert len(plats) >= 5
        ids = {p.get("nome", p.get("id", "")) for p in plats}
        assert any("Terrastories" in i for i in ids)
        assert any("Mapme" in i for i in ids)
        assert any("Historypin" in i for i in ids)

    def test_fontes_dados_abertas(self):
        engine = MultimodalRelationalEngine()
        fontes = engine.nodes_by_type("fonte_dados")
        assert len(fontes) >= 7

    def test_cartografia_node(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("cartografia_nao_representacional")
        assert len(nb) >= 1

    def test_principio_convite(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("principio_convite")
        assert len(nb) >= 2  # connects to silencio + tensao

    def test_densidade_relacional_node(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("densidade_relacional")
        assert len(nb) >= 1

    def test_framework_has_fluxo_leitura_proposta(self):
        fw = load_framework()
        assert "fluxo_leitura_proposta" in fw
        assert len(fw["fluxo_leitura_proposta"]) == 6

    def test_framework_has_taxonomia_escalas(self):
        fw = load_framework()
        assert "taxonomia_escalas" in fw
        assert len(fw["taxonomia_escalas"]) >= 5

    def test_framework_has_regimes_uso(self):
        fw = load_framework()
        assert "regimes_uso_territorio" in fw
        assert "uso_comum_ordinario" in fw["regimes_uso_territorio"]

    def test_framework_has_auditoria_territorial(self):
        fw = load_framework()
        assert "auditoria_territorial" in fw
        assert len(fw["auditoria_territorial"]) >= 4

    def test_extended_graph_much_larger(self):
        engine = MultimodalRelationalEngine()
        assert engine.node_count >= 80
        assert engine.edge_count >= 70


class TestFALArte:
    def test_falarte_present(self):
        fw = load_framework()
        assert "falarte" in fw
        assert "Cosmic Flow" in fw.get("cosmic_flow", {}).get("nome", "")

    def test_ten_mecanicas_curatoriais(self):
        engine = MultimodalRelationalEngine()
        mecs = engine.nodes_by_type("mecanica_curatorial")
        assert len(mecs) >= 10

    def test_cosmic_flow_motor(self):
        engine = MultimodalRelationalEngine()
        motors = [n for n in engine.nodes_by_type("motor_sistemico") if "cosmic" in n.get("nome","").lower()]
        assert len(motors) >= 1

    def test_rgpd_formulario(self):
        fw = load_framework()
        assert "rgpd_formulario_falarte" in fw
        assert fw["rgpd_formulario_falarte"]["idade_minima"] == 13
        assert "Lei n.º 58/2019" in fw["rgpd_formulario_falarte"]["lei_referencia"]

    def test_freire_node(self):
        engine = MultimodalRelationalEngine()
        nb = engine.neighbors("freire")
        assert len(nb) >= 2  # connects to boal and pedagogia_autonomia

    def test_remetente_ausente(self):
        fw = load_framework()
        mecs = fw["mecanicas_curatoriais_falarte"]
        ra = [m for m in mecs if "remetente" in m["id"].lower()]
        assert len(ra) == 1
        assert "carta" in ra[0]["especial"].lower()

    def test_referenciais_operados(self):
        fw = load_framework()
        refs = fw["cosmic_flow"]["referenciais_operados"]
        assert "freire" in refs
        assert "deleuze" in refs
        assert "songline" in refs
        assert "grio" in refs
        assert "quipu" in refs
        assert "ogham" in refs

    def test_museu_references(self):
        engine = MultimodalRelationalEngine()
        museus = engine.nodes_by_type("referencia_museologica")
        assert len(museus) >= 2

    def test_falarte_codigo(self):
        fw = load_framework()
        assert "falarte_codigo" in fw
        assert fw["falarte_codigo"]["ficheiro_destino"] == "deploy/atlas-public/falarte.html"
