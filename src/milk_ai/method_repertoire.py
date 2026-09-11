"""MILK IA - Active Method / Curatorial Repertory (section 5 + addendum 20).

Source-grounded method and curatorial-work nodes derived from the canonical
biblioteca framework (biblioteca/milk_framework_conceptual.json) and from the
Final Relational Addendum (Husserl, Schaeffer/Chion, Dopafania, reading
architecture, zine, handwritten curatorial seeds).

Nothing is fabricated: every node carries a source_pointer and an
epistemic_status that distinguishes canonical source, method translation,
experimental hypothesis, curatorial seed, and academic article.

Represent:
    SOURCE PASSAGE -> CONCEPT -> METHOD -> POSSIBLE OPERATION
    -> CURATORIAL DEVICE -> TERRITORY/MODALITY -> OBSERVED OUTCOME

Provenance is sacred:
  - Husserl nodes are Husserl; Schaeffer nodes are Schaeffer; Chion nodes
    are Chion (provenance correction: the three-mode causal/semantic/reduced
    formulation is Chion's, with Schaeffer as antecedent).
  - ESCUTA_IDENTITARIA and DOPAFANIA are AUTHORIAL MILK concepts by Eduardo
    Mauricio Vieira Cabral e Araujo, not quotations from established theory.
  - Handwritten curatorial seeds are CURATORIAL_SEED, not METHOD_THEORY or
    SCIENTIFIC_SOURCE.
  - The Scliar-Cabral 2013 article is an ACADEMIC_ARTICLE with its own date
    and argumentative context; its pedagogical dispute is not promoted to
    universal MILK neural truth.
  - The zine "A Verdade Esta Em Outra Tribo" is a CURATORIAL/PHILOSOPHICAL
    source, not neuroscience.
"""
from __future__ import annotations

from .hypergraph import SovereignHypergraph, HyperNode, HyperEdge
from .provenance import CANONICAL_AUTHOR

_FRAMEWORK_SOURCE = "biblioteca/milk_framework_conceptual.json"
_ADDENDUM_SOURCE = "addendum:final_relational_addendum"
_MILK_AUTHOR = CANONICAL_AUTHOR.get("idealized_by", "Eduardo Mauricio Vieira Cabral e Araujo")
_MILK_ORCID = CANONICAL_AUTHOR.get("orcid", "0009-0007-6892-6570")

# Epistemic status values
EP_SOURCE = "SOURCE"
EP_METHOD_TRANSLATION = "METHOD_TRANSLATION"
EP_EXPERIMENTAL_HYPOTHESIS = "EXPERIMENTAL_HYPOTHESIS"
EP_CURATORIAL_SEED = "CURATORIAL_SEED"
EP_ACADEMIC_ARTICLE = "ACADEMIC_ARTICLE"

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


# ===========================================================================
# Addendum 20 — Extended nodes with explicit provenance and epistemic_status
# ===========================================================================
# Each entry: (node_id, label, type, operation, modality, source_pointer,
#              epistemic_status, author, extra_metadata)

# --- 20.1 Husserl — temporal consciousness ---
HUSSERL_NODES = [
    ("temporal:retention", "Husserl Retention", "CONCEPT",
     "consciousness of the just-elapsed phase", "text",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_SOURCE,
     "Edmund Husserl", {"phase": "retention"}),
    ("temporal:primal_impression", "Husserl Primal Impression", "CONCEPT",
     "narrowly present phase", "text",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_SOURCE,
     "Edmund Husserl", {"phase": "primal_impression"}),
    ("temporal:protention", "Husserl Protention", "CONCEPT",
     "openness/anticipation toward the about-to-occur phase", "text",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_SOURCE,
     "Edmund Husserl", {"phase": "protention"}),
    ("temporal:temporal_object", "Husserl Temporal Object", "CONCEPT",
     "perceived temporal whole (e.g. melody continuity)", "text",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_SOURCE,
     "Edmund Husserl", {"phase": "temporal_object"}),
    ("temporal:melody_continuity", "Husserl Melody Continuity", "CONCEPT",
     "previous_note_retained + current_note + anticipated_next_event", "sound",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_SOURCE,
     "Edmund Husserl", {"phase": "melody_continuity"}),
    ("temporal:expectation", "Husserl Expectation", "CONCEPT",
     "protentional expectation toward next event", "text",
     "source:husserl:phenomenology_of_internal_time_consciousness", EP_METHOD_TRANSLATION,
     "Edmund Husserl", {"phase": "expectation"}),
    ("temporal:surprise", "Temporal Surprise / Rupture", "CONCEPT",
     "confirmation OR rupture of protention -> reinterpretation", "text",
     _ADDENDUM_SOURCE, EP_METHOD_TRANSLATION,
     _MILK_AUTHOR, {"phase": "surprise", "note": "plot_twist is MILK translation"}),
]

# --- 20.2 Schaeffer — sound object / reduced listening ---
SCHAEFFER_NODES = [
    ("sound:sound_object", "Schaeffer Sound Object", "CONCEPT",
     "objet sonore — the sound as perceived in reduced listening", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:acousmatic_reduction", "Schaeffer Acousmatic Reduction", "CONCEPT",
     "bracketing source/cause to attend to sonic properties", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:reduced_listening", "Schaeffer Reduced Listening", "CONCEPT",
     "attention to sonic qualities while bracketing source and ordinary meaning", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:ecouter", "Schaeffer Ecouter", "CONCEPT",
     "listening mode: hear and listen", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:ouir", "Schaeffer Ouir", "CONCEPT",
     "listening mode: to hear (perceive sound)", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:entendre", "Schaeffer Entendre", "CONCEPT",
     "listening mode: to intend/signify", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
    ("sound:comprendre", "Schaeffer Comprendre", "CONCEPT",
     "listening mode: to comprehend/understand", "sound",
     "source:schaeffer:traite_des_objets_musicaux", EP_SOURCE,
     "Pierre Schaeffer", {}),
]

# --- 20.3 Chion — listening modes (provenance correction: Chion, not Schaeffer) ---
CHION_NODES = [
    ("listening:causal", "Chion Causal Listening", "CONCEPT",
     "sound -> infer source/cause", "sound",
     "source:chion:audio_vision", EP_SOURCE,
     "Michel Chion", {"antecedent": "Pierre Schaeffer"}),
    ("listening:semantic", "Chion Semantic Listening", "CONCEPT",
     "sound -> decode sign/code/language", "sound",
     "source:chion:audio_vision", EP_SOURCE,
     "Michel Chion", {"antecedent": "Pierre Schaeffer"}),
    ("listening:reduced", "Chion Reduced Listening", "CONCEPT",
     "sound -> attend to sound itself", "sound",
     "source:chion:audio_vision", EP_SOURCE,
     "Michel Chion", {"antecedent": "Pierre Schaeffer"}),
]

# --- 20.4 ESCUTA IDENTITARIA — authorial MILK method extension ---
MILK_AUTHORIAL_NODES = [
    ("milk:escuta_identitaria", "Escuta Identitaria", "CONCEPT",
     "sound/voice/word/rhythm/silence -> autobiographical or territorial resonance -> recognition -> affective association -> identity trace",
     "voice", _ADDENDUM_SOURCE, EP_METHOD_TRANSLATION,
     _MILK_AUTHOR, {"orcid": _MILK_ORCID,
                    "note": "Authorial MILK method extension, not a Schaeffer category"}),
    ("milk:dopafania", "Dopafania", "CONCEPT",
     "expectation -> interruption/unexpected relation -> recognition or discovery -> sudden subjective salience -> experienced epiphany",
     "text", _ADDENDUM_SOURCE, EP_EXPERIMENTAL_HYPOTHESIS,
     _MILK_AUTHOR, {"orcid": _MILK_ORCID,
                    "note": "NOT neurochemical fact; experimental hypothesis. "
                            "Neuroscience bridge (reward_prediction_error, dopaminergic_response) "
                            "remains separate and does not claim a unique dopamine mechanism."}),
    # Neuroscience bridge nodes — separate from the experiential concept
    ("neuro:reward_prediction_error", "Reward Prediction Error", "CONCEPT",
     "expected_reward vs actual_reward -> prediction error", "text",
     _ADDENDUM_SOURCE, EP_EXPERIMENTAL_HYPOTHESIS,
     "neuroscience_bridge", {"note": "Separate from dopafania; no unique mechanism claimed"}),
    ("neuro:dopaminergic_response", "Dopaminergic Response", "CONCEPT",
     "learning_signal from unexpected_reward", "text",
     _ADDENDUM_SOURCE, EP_EXPERIMENTAL_HYPOTHESIS,
     "neuroscience_bridge", {"note": "Separate from dopafania; no unique mechanism claimed"}),
]

# --- 20.6 Reading / language architecture (Scliar-Cabral 2013) ---
READING_ARCHITECTURE_NODES = [
    ("reading:scliar_2013", "Scliar-Cabral 2013 — Desmistificacao do Metodo Global", "DOCUMENT",
     "academic article on reading architecture / linguistic levels", "text",
     "source:scliar_cabral:2013:letras_de_hoje", EP_ACADEMIC_ARTICLE,
     "Leonor Scliar-Cabral", {"publication_year": 2013,
                              "venue": "Letras de Hoje",
                              "current_validation_required": True,
                              "note": "Pedagogical dispute (global vs phonic) NOT promoted to universal MILK neural truth"}),
    ("reading:linguistic_levels", "Linguistic Levels (Reading Architecture)", "CONCEPT",
     "parallel_processing of visual_features, graphemes, phonological_relations", "text",
     "source:scliar_cabral:2013:letras_de_hoje", EP_ACADEMIC_ARTICLE,
     "Leonor Scliar-Cabral", {}),
    ("reading:bottom_up", "Bottom-Up Processing (Reading)", "CONCEPT",
     "features -> graphemic units -> lexical access -> semantic activation", "text",
     "source:scliar_cabral:2013:letras_de_hoje", EP_ACADEMIC_ARTICLE,
     "Leonor Scliar-Cabral", {}),
    ("reading:top_down", "Top-Down Processing (Reading)", "CONCEPT",
     "prior_knowledge -> cognitive_schemas -> top-down modulation", "text",
     "source:scliar_cabral:2013:letras_de_hoje", EP_ACADEMIC_ARTICLE,
     "Leonor Scliar-Cabral", {}),
    ("reading:working_memory", "Working Memory (Reading Integration)", "CONCEPT",
     "temporary integration of linguistic levels", "text",
     "source:scliar_cabral:2013:letras_de_hoje", EP_ACADEMIC_ARTICLE,
     "Leonor Scliar-Cabral", {}),
]

# --- 20.7 Zine — A Verdade Esta Em Outra Tribo ---
ZINE_NODES = [
    ("zine:verdade_outra_tribo", "Zine: A Verdade Esta Em Outra Tribo", "DOCUMENT",
     "curatorial/philosophical source on identity, gender_performance, devenir", "text",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED,
     _MILK_AUTHOR, {"source_type": "CURATORIAL_PHILOSOPHICAL",
                    "external_attributions": ["Foucault", "Butler", "Clarice Lispector"],
                    "note": "Not neuroscience; external attributions must be independently verifiable"}),
    ("zine:identity_revisable", "Identity Is Not Fixed Label", "CONCEPT",
     "identity -> historical_context -> performed_relation -> lived_experience -> revisable_self_description", "text",
     _ADDENDUM_SOURCE, EP_METHOD_TRANSLATION,
     _MILK_AUTHOR, {"derived_from": "zine:verdade_outra_tribo"}),
]

# --- 20.8 Handwritten curatorial seeds ---
CURATORIAL_SEEDS = [
    ("seed:eu_lembrei", "eu lembrei", "MEMORY",
     "affective memory / recognition", "voice",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED, _MILK_AUTHOR, {}),
    ("seed:juntos_sempre", "juntos sempre", "MEMORY",
     "proximity / togetherness", "body",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED, _MILK_AUTHOR, {}),
    ("seed:eu_ri", "eu ri", "EMOTION",
     "affect / joy / surprise", "voice",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED, _MILK_AUTHOR, {}),
    ("seed:vem_me_reencontrar", "vem me reencontrar", "MEMORY",
     "return / encounter / absence and presence", "voice",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED, _MILK_AUTHOR, {}),
    ("seed:um_abraco", "um abraco", "GESTURE",
     "affective gesture / proximity", "body",
     _ADDENDUM_SOURCE, EP_CURATORIAL_SEED, _MILK_AUTHOR, {}),
]

# --- All addendum node groups for iteration ---
ADDENDUM_NODE_GROUPS = [
    HUSSERL_NODES, SCHAEFFER_NODES, CHION_NODES,
    MILK_AUTHORIAL_NODES, READING_ARCHITECTURE_NODES,
    ZINE_NODES, CURATORIAL_SEEDS,
]

# --- 20.9 Cross-relations (edges between addendum and existing nodes) ---
# Each: (source, edge_type, target, confidence, description)
ADDENDUM_EDGES = [
    # Husserl temporal structure
    ("temporal:retention", "RELATED_TO", "temporal:primal_impression", 0.95,
     "retention -> present -> protention (Husserl structure)"),
    ("temporal:primal_impression", "RELATED_TO", "temporal:protention", 0.95,
     "present -> protention (Husserl structure)"),
    ("temporal:protention", "RELATED_TO", "temporal:expectation", 0.85,
     "protention -> expectation"),
    ("temporal:expectation", "RELATED_TO", "temporal:surprise", 0.75,
     "confirmation OR rupture -> surprise -> reinterpretation"),
    ("temporal:retention", "RELATED_TO", "temporal:melody_continuity", 0.9,
     "retention of previous note enables melody continuity"),
    ("temporal:protention", "RELATED_TO", "temporal:melody_continuity", 0.9,
     "protention of next event enables melody continuity"),

    # Husserl <-> memory/expectation cross-relations (METHOD_TRANSLATION)
    ("temporal:retention", "ANALOGOUS_TO", "method:oral_traditions", 0.6,
     "retention ~= memory_trace (NOT episodic memory; METHOD_TRANSLATION)"),
    ("temporal:protention", "ANALOGOUS_TO", "temporal:expectation", 0.8,
     "protention ~= expectation (NOT explicit prediction; METHOD_TRANSLATION)"),

    # Schaeffer reduced listening chain
    ("sound:reduced_listening", "RELATED_TO", "sound:sound_object", 0.95,
     "bracket_source -> bracket_semantic -> attend_to_sonic -> sound_object"),
    ("sound:acousmatic_reduction", "RELATED_TO", "sound:reduced_listening", 0.9,
     "acousmatic reduction enables reduced listening"),

    # Chion <-> Schaeffer provenance link
    ("listening:reduced", "DERIVED_FROM", "sound:reduced_listening", 0.85,
     "Chion reduced listening derived from Schaeffer (antecedent)"),
    ("listening:causal", "RELATED_TO", "sound:ecouter", 0.6,
     "causal listening relates to Schaeffer ecouter"),
    ("listening:semantic", "RELATED_TO", "sound:entendre", 0.6,
     "semantic listening relates to Schaeffer entendre"),

    # MILK escuta_identitaria cross-relations
    ("milk:escuta_identitaria", "RELATED_TO", "listening:causal", 0.5,
     "escuta identitaria may engage causal listening but adds identity trace"),
    ("milk:escuta_identitaria", "RELATED_TO", "method:schafer", 0.5,
     "schafer sound_memory <-> identity_listening (METHOD_TRANSLATION)"),
    ("milk:escuta_identitaria", "RELATED_TO", "method:oral_traditions", 0.6,
     "autobiographical or territorial resonance"),

    # Dopafania chain
    ("temporal:protention", "RELATED_TO", "milk:dopafania", 0.5,
     "protention -> expectation; expectation_violation -> surprise -> dopafania candidate"),
    ("temporal:surprise", "RELATED_TO", "milk:dopafania", 0.65,
     "surprise -> possible salience -> dopafania candidate"),
    ("milk:dopafania", "RELATED_TO", "neuro:reward_prediction_error", 0.3,
     "experimental bridge; NOT a unique dopamine mechanism"),
    ("neuro:reward_prediction_error", "RELATED_TO", "neuro:dopaminergic_response", 0.4,
     "prediction error -> dopaminergic learning signal (neuroscience bridge, separate)"),

    # Reading architecture
    ("reading:bottom_up", "RELATED_TO", "reading:linguistic_levels", 0.85,
     "bottom-up: features -> graphemes -> lexical access -> semantic activation"),
    ("reading:top_down", "RELATED_TO", "reading:linguistic_levels", 0.85,
     "top-down: prior knowledge -> cognitive schemas -> modulation"),
    ("reading:working_memory", "RELATED_TO", "reading:linguistic_levels", 0.7,
     "working memory provides temporary integration"),
    ("reading:scliar_2013", "RELATED_TO", "reading:linguistic_levels", 0.9,
     "source article -> relational architecture"),

    # Zine / identity
    ("zine:verdade_outra_tribo", "RELATED_TO", "zine:identity_revisable", 0.85,
     "identity != fixed_label; identity is revisable and situated"),
    ("zine:identity_revisable", "RELATED_TO", "method:foucault", 0.4,
     "Foucault power/knowledge; external attribution, independently verifiable"),

    # Cross-modal: territory -> soundscape -> memory -> identity
    ("device:escuta_sonora", "RELATED_TO", "milk:escuta_identitaria", 0.5,
     "territory -> soundscape -> memory -> identity (cross-modal)"),
    ("method:toponymy", "RELATED_TO", "milk:escuta_identitaria", 0.4,
     "territorial resonance in escuta identitaria"),

    # Palavra Ritual <-> semantic listening
    ("work:palavra_ritual", "RELATED_TO", "listening:semantic", 0.6,
     "word ritual <-> semantic listening (sound -> decode sign/language)"),
    ("work:palavra_ritual", "RELATED_TO", "milk:escuta_identitaria", 0.5,
     "living language <-> identity listening"),

    # Curatorial seeds -> affective retrieval
    ("seed:eu_lembrei", "RELATED_TO", "milk:escuta_identitaria", 0.4,
     "memory / recognition seed"),
    ("seed:vem_me_reencontrar", "RELATED_TO", "temporal:protention", 0.3,
     "return / encounter seed -> expectation of reunion"),
]


def _node(node_id, label, ntype, operation, modality):
    return HyperNode(
        id=node_id, type=ntype, label=label, modality=modality,
        source_pointer=_FRAMEWORK_SOURCE, evidence_pointer="",
        validation_state="validated", confidence=0.9,
        metadata={"possible_operation": operation, "repertory": "active_method"},
    )


def _addendum_node(entry):
    """Build a HyperNode from an addendum 9-tuple."""
    node_id, label, ntype, operation, modality, source_ptr, epistemic, author, extra = entry
    # Validate node type against NODE_TYPES; fall back to CONCEPT
    from .hypergraph import NODE_TYPES
    if ntype not in NODE_TYPES:
        ntype = "CONCEPT"
    meta = {"possible_operation": operation, "repertory": "addendum_20",
            "epistemic_status": epistemic, "author": author}
    meta.update(extra)
    return HyperNode(
        id=node_id, type=ntype, label=label, modality=modality,
        source_pointer=source_ptr, evidence_pointer="",
        validation_state="validated", confidence=0.8,
        metadata=meta,
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

    # --- Addendum 20: extended nodes and cross-relations ---
    n_addendum_nodes = 0
    for group in ADDENDUM_NODE_GROUPS:
        for entry in group:
            graph.add_node(_addendum_node(entry))
            n_addendum_nodes += 1

    n_addendum_edges = 0
    from .hypergraph import EDGE_TYPES as _VALID_EDGE_TYPES
    for src, etype, tgt, conf, desc in ADDENDUM_EDGES:
        if etype not in _VALID_EDGE_TYPES:
            etype = "RELATED_TO"
        graph.add_edge(HyperEdge(
            id=f"addendum:{src}->{tgt}", source=src, edge_type=etype,
            target=tgt, confidence=conf, validation_state="validated",
            source_ref=_ADDENDUM_SOURCE,
            metadata={"description": desc, "epistemic_status": EP_METHOD_TRANSLATION}))
        n_addendum_edges += 1

    return {
        "method_nodes": n_methods,
        "curatorial_work_nodes": n_works,
        "curatorial_device_nodes": n_devices,
        "edges": edges,
        "total_repertory_nodes": n_methods + n_works + n_devices,
        "addendum_nodes": n_addendum_nodes,
        "addendum_edges": n_addendum_edges,
    }


def method_repertoire_count() -> int:
    """Number of source-grounded method repertoire nodes (without a graph).

    Includes the original framework nodes plus addendum 20 nodes.
    """
    base = len(METHOD_REFERENCES) + len(CURATORIAL_WORKS) + len(CURATORIAL_DEVICES)
    addendum = sum(len(g) for g in ADDENDUM_NODE_GROUPS)
    return base + addendum


def curatorial_method_nodes() -> list[dict]:
    """Return the method/work/device nodes as plain dicts (for manifests).

    Includes original framework nodes and addendum 20 nodes.
    """
    out = []
    for node_id, label, ntype, operation, modality in (
            METHOD_REFERENCES + CURATORIAL_WORKS + CURATORIAL_DEVICES):
        out.append({"id": node_id, "label": label, "type": ntype,
                    "operation": operation, "modality": modality,
                    "source_pointer": _FRAMEWORK_SOURCE,
                    "epistemic_status": EP_SOURCE})
    for group in ADDENDUM_NODE_GROUPS:
        for entry in group:
            node_id, label, ntype, operation, modality, source_ptr, epistemic, author, extra = entry
            d = {"id": node_id, "label": label, "type": ntype,
                 "operation": operation, "modality": modality,
                 "source_pointer": source_ptr,
                 "epistemic_status": epistemic,
                 "author": author}
            d.update(extra)
            out.append(d)
    return out
