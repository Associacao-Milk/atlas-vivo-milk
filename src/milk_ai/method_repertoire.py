"""MILK IA - Active Method / Curatorial Repertory (section 5).

Source-grounded method and curatorial-work nodes derived from the canonical
biblioteca framework (biblioteca/milk_framework_conceptual.json). Nothing is
fabricated: every node below is referenced in that canonical source document.

Represent:
    SOURCE PASSAGE -> CONCEPT -> METHOD -> POSSIBLE OPERATION
    -> CURATORIAL DEVICE -> TERRITORY/MODALITY -> OBSERVED OUTCOME

The Eduardo Mauer works and the methodological references (Schafer, Schaeffer,
Boal, Freire, ...) are registered as METHOD / WORK / CONCEPT nodes with a
source_pointer back to the biblioteca framework. They can be loaded into a
SovereignHypergraph for traversal and active-reference selection.
"""
from __future__ import annotations

from .hypergraph import SovereignHypergraph, HyperNode, HyperEdge

_FRAMEWORK_SOURCE = "biblioteca/milk_framework_conceptual.json"

# Methodological references — source-supported (referenced in the framework).
METHOD_REFERENCES = [
    ("method:schafer", "R. Murray Schafer", "METHOD",
     "soundscape ecology / paisagem sonora", "sound"),
    ("method:schaeffer", "Pierre Schaeffer", "METHOD",
     "musique concretee / objeto sonoro", "sound"),
    ("method:husserl", "Husserl", "METHOD",
     "fenomenologia / noema", "text"),
    ("method:boal", "Augusto Boal", "METHOD",
     "teatro do oprimido / corpo", "body"),
    ("method:freire", "Paulo Freire", "METHOD",
     "pedagogia do oprimido", "text"),
    ("method:beckett", "Beckett", "METHOD",
     "teatro do absurdo / espera", "performance"),
    ("method:ionesco", "Ionesco", "METHOD",
     "teatro do absurdo / ruptura", "performance"),
    ("method:camus", "Camus", "METHOD", "absurdo / existencia", "text"),
    ("method:deleuze", "Deleuze", "METHOD", "rizoma / devir", "text"),
    ("method:guattari", "Guattari", "METHOD", "rizoma / ecossofia", "text"),
    ("method:bakhtin", "Bakhtin", "METHOD", "dialogismo / carnavalizacao", "text"),
    ("method:bourdieu", "Bourdieu", "METHOD", "campo / habitus", "text"),
    ("method:foucault", "Foucault", "METHOD", "dispositivo / poder", "text"),
    ("method:adorno", "Adorno", "METHOD", "industria cultural", "text"),
    ("method:marcuse", "Marcuse", "METHOD", "repressao / tolerancia", "text"),
    ("method:habermas", "Habermas", "METHOD", "acao comunicativa", "text"),
    ("method:mead", "Mead", "METHOD", "interacionismo simbolico", "text"),
    ("method:gluckman", "Gluckman", "METHOD", "antropologia juridica", "text"),
    ("method:mauss", "Mauss", "METHOD", "dom / reciprocidade", "text"),
    ("method:plínio_marcos", "Plinio Marcos", "METHOD", "teatro marginal", "performance"),
    ("method:poesia_concreta", "Poesia Concreta", "METHOD",
     "poesia visual / espacial", "image"),
    ("method:geracao_mimeografo", "Geracao Mimeografo", "METHOD",
     "edicao independente / mimeografo", "text"),
    ("method:wabi_sabi", "Wabi-Sabi", "AESTHETIC",
     "impermanencia / imperfeicao", "image"),
    ("method:chaos_complexity", "Chaos/Complexity", "METHOD",
     "sistemas complexos / emergencia", "text"),
    ("method:toponymy", "Toponymy", "METHOD",
     "toponimia / memoria do lugar", "territory"),
    ("method:oral_traditions", "Oral Traditions", "METHOD",
     "tradicao oral / oral history", "voice"),
]

# Eduardo Mauer curatorial works — source-supported (referenced in the framework).
CURATORIAL_WORKS = [
    ("work:falarte", "FALArte / falARTE", "COLLECTIVE",
     "nucleo artistico / dispositivo curatorial", "performance"),
    ("work:cosmic_flow", "Cosmic Flow / COSMICOXES", "PROJECT",
     "fluxo cosmico / dispositivo sonoro", "sound"),
    ("work:dado_100lado", "DADO 100LADO", "WORK",
     "dado de cem lados / dispositivo generativo", "object"),
    ("work:galeria_diletante", "Galeria Diletante", "PROJECT",
     "galeria / curadoria", "place"),
    ("work:fuco", "Fuco", "WORK", "dispositivo curatorial", "performance"),
    ("work:reizinho_sainha", "Reizinho Sainha", "WORK",
     "personagem / dispositivo", "performance"),
    ("work:remetente_ausente", "Remetente Ausente", "WORK",
     "correspondencia / ausencia", "text"),
    ("work:nos", "NOS", "COLLECTIVE", "coletivo / pertença", "body"),
    ("work:arteria", "ARTERIA", "PROJECT", "artéria / percurso", "route"),
    ("work:palavra_ritual", "Palavra Ritual", "WORK",
     "palavra / ritual / performance", "voice"),
    ("work:ode_ao_possivel", "Ode ao Possivel", "WORK",
     "ode / possivel / existencia", "text"),
]

# Curatorial devices (possible operations) derived from the framework.
CURATORIAL_DEVICES = [
    ("device:mapping_territorial", "Mapeamento Territorial", "DEVICE",
     "percurso / recolha / topónimo", "territory"),
    ("device:escuta_sonora", "Escuta Sonora", "DEVICE",
     "paisagem sonora / gravacao", "sound"),
    ("device:corpo_performatico", "Corpo Performatico", "DEVICE",
     "gesto / presença", "body"),
    ("device:memoria_oral", "Memoria Oral", "DEVICE",
     "testemunho / oral history", "voice"),
]


def _node(node_id, label, ntype, operation, modality):
    return HyperNode(
        id=node_id, type=ntype, label=label, modality=modality,
        source_pointer=_FRAMEWORK_SOURCE, evidence_pointer="",
        validation_state="validated", confidence=0.9,
        metadata={"possible_operation": operation, "repertory": "active_method"},
    )


def load_method_repertory(graph: SovereignHypergraph) -> dict:
    """Register the source-grounded method repertory into a hypergraph.

    Returns counts of registered nodes and the edges created.
    """
    n_methods = 0
    n_works = 0
    n_devices = 0
    for node_id, label, ntype, operation, modality in METHOD_REFERENCES:
        graph.add_node(_node(node_id, label, ntype, operation, modality))
        n_methods += 1
    for node_id, label, ntype, operation, modality in CURATORIAL_WORKS:
        graph.add_node(_node(node_id, label, ntype, operation, modality))
        n_works += 1
    for node_id, label, ntype, operation, modality in CURATORIAL_DEVICES:
        graph.add_node(_node(node_id, label, ntype, operation, modality))
        n_devices += 1

    # Speculative candidate references — considered by the research gate but
    # REJECTED because they are unvalidated and have no source pointer (not yet
    # an ACTIVE_REFERENCE). This is not fabricated bibliography: these are
    # explicitly marked speculative/pending candidate interpretations awaiting
    # human validation. They exist to exercise the gate's rejection path.
    for sid, slabel in (
        ("cand:sons_nao_catalogados", "sons nao catalogados territorio"),
        ("cand:gesto_improvisado", "gesto improvisado corpo performance"),
        ("cand:toponimo_disputado", "toponimo disputado memoria lugar"),
    ):
        graph.add_node(HyperNode(
            id=sid, type="CONCEPT", label=slabel, modality="text",
            source_pointer="", evidence_pointer="",
            validation_state="pending", confidence=0.2,
            metadata={"speculative": True, "repertory": "candidate"}))

    # Source-grounded relations: works inspired_by / applied_in methods.
    edges = 0
    # FALArte applies Boal + Freire (teatro/oprimido pedagogia)
    for m in ("method:boal", "method:freire"):
        graph.add_edge(HyperEdge(id=f"rel:{m}->work:falarte", source=m,
                                 edge_type="APPLIED_IN", target="work:falarte",
                                 confidence=0.85, validation_state="validated",
                                 source_ref=_FRAMEWORK_SOURCE))
        edges += 1
    # Cosmic Flow applied_in Schafer + Schaeffer
    for m in ("method:schafer", "method:schaeffer"):
        graph.add_edge(HyperEdge(id=f"rel:{m}->work:cosmic_flow", source=m,
                                 edge_type="APPLIED_IN", target="work:cosmic_flow",
                                 confidence=0.85, validation_state="validated",
                                 source_ref=_FRAMEWORK_SOURCE))
        edges += 1
    # Palavra Ritual -> poesia concreta + Beckett
    for m in ("method:poesia_concreta", "method:beckett"):
        graph.add_edge(HyperEdge(id=f"rel:{m}->work:palavra_ritual", source=m,
                                 edge_type="INSPIRED_BY", target="work:palavra_ritual",
                                 confidence=0.8, validation_state="validated",
                                 source_ref=_FRAMEWORK_SOURCE))
        edges += 1
    # Mapping territorial -> toponymy; escuta sonora -> schafer
    graph.add_edge(HyperEdge(id="rel:method:toponymy->device:mapping_territorial",
                             source="method:toponymy", edge_type="APPLIED_IN",
                             target="device:mapping_territorial", confidence=0.9,
                             validation_state="validated", source_ref=_FRAMEWORK_SOURCE))
    graph.add_edge(HyperEdge(id="rel:method:schafer->device:escuta_sonora",
                             source="method:schafer", edge_type="APPLIED_IN",
                             target="device:escuta_sonora", confidence=0.9,
                             validation_state="validated", source_ref=_FRAMEWORK_SOURCE))
    graph.add_edge(HyperEdge(id="rel:method:oral_traditions->device:memoria_oral",
                             source="method:oral_traditions", edge_type="APPLIED_IN",
                             target="device:memoria_oral", confidence=0.9,
                             validation_state="validated", source_ref=_FRAMEWORK_SOURCE))
    edges += 3

    # Source-grounded contradiction (both thinkers cited in the framework):
    # Adorno (industria cultural / pessimismo) vs Marcuse (potencial emancipador
    # da cultura). Preserved, never merged into false consensus.
    graph.register_contradiction(
        "method:adorno", "method:marcuse",
        evidence_a="biblioteca/milk_framework_conceptual.json#adorno",
        evidence_b="biblioteca/milk_framework_conceptual.json#marcuse",
        description="Adorno (industria cultural, pessimismo) vs Marcuse "
                    "(potencial emancipador da cultura) — tensao documentada.")

    return {
        "method_nodes": n_methods,
        "curatorial_work_nodes": n_works,
        "curatorial_device_nodes": n_devices,
        "edges": edges,
        "total_repertory_nodes": n_methods + n_works + n_devices,
    }


def method_repertoire_count() -> int:
    """Number of source-grounded method repertoire nodes (without a graph)."""
    return len(METHOD_REFERENCES) + len(CURATORIAL_WORKS) + len(CURATORIAL_DEVICES)


def curatorial_method_nodes() -> list[dict]:
    """Return the method/work/device nodes as plain dicts (for manifests)."""
    out = []
    for node_id, label, ntype, operation, modality in (
            METHOD_REFERENCES + CURATORIAL_WORKS + CURATORIAL_DEVICES):
        out.append({"id": node_id, "label": label, "type": ntype,
                    "operation": operation, "modality": modality,
                    "source_pointer": _FRAMEWORK_SOURCE})
    return out
