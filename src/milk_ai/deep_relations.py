"""MILK IA - Deep Relations and Loader (Phase 4-8).

Deep relations with non-equivalence, multi-hop constellations, and the
loader that attaches depth profiles to the existing SovereignHypergraph.
"""
from __future__ import annotations
from .depth_profile import DeepRelation, RelevanceManifold
from .depth_registry import DEPTH_PROFILES, RESEARCH_GAPS_REGISTRY
from .provenance import CANONICAL_AUTHOR

_MILK_AUTHOR = CANONICAL_AUTHOR["idealized_by"]

DEEP_RELATIONS: list[DeepRelation] = [
    DeepRelation(
        relation_id="dr:husserl_protention_kandinsky_line",
        relation_type="formal_temporal_resonance",
        source_nodes=["temporal:protention"],
        target_nodes=["method:kandinsky"],
        basis_axes=["temporal_resonance", "formal_resonance"],
        bridge_explanation="Both describe a direction emerging from a present configuration: protention is the horizon of the about-to-occur; the Kandinsky line is a force that points beyond itself.",
        productive_tension="The protention is a structural openness of consciousness; the line is a plastic-formal force. They resonate without explaining each other.",
        non_equivalence="Protention is a phenomenological structure; the Kandinsky line is a plastic-formal category. One does NOT scientifically explain the other.",
        epistemic_difference="PHILOSOPHY vs ART_THEORY",
        evidence_refs=["source:husserl:phenomenology_of_internal_time_consciousness"],
        activation_context="When analyzing how a form or sound anticipates what has not yet occurred",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(temporal_resonance=0.8, formal_resonance=0.75, epistemic_distance=0.7),
        cosmicoxes_grammar="tension: forca direcional entre dois pontos",
    ),
    DeepRelation(
        relation_id="dr:winnicott_clown_birth",
        relation_type="experiential_structural_resonance",
        source_nodes=["method:winnicott"],
        target_nodes=["clown:birth"],
        basis_axes=["embodied_resonance", "ritual_resonance"],
        bridge_explanation="Both describe a space where failure is not error but possibility: Winnicott's potential space; the clown's birth. The relation is through the architecture of play, contingency, and relation.",
        productive_tension="Winnicott describes a structural space; the clown birth describes a performative event. They share the structure but not the modality.",
        non_equivalence="Winnicott's potential space is psychoanalytic-philosophical; the clown birth is performative practice. One does NOT explain the other.",
        epistemic_difference="PSYCHOANALYSIS vs PERFORMANCE_STUDIES",
        evidence_refs=["source:winnicott:playing_and_reality"],
        activation_context="When examining how failure, play, and presence relate",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(embodied_resonance=0.85, ritual_resonance=0.75, epistemic_distance=0.6),
        cosmicoxes_grammar="potential_space: regiao de jogo com topologia permissiva",
    ),
    DeepRelation(
        relation_id="dr:schaeffer_schafer_contradiction",
        relation_type="productive_contradiction",
        source_nodes=["sound:reduced_listening"],
        target_nodes=["method:schafer"],
        basis_axes=["productive_contradiction", "perceptual_resonance"],
        bridge_explanation="Schaeffer listens to sound as object (bracketing context); Schafer listens to sound as environment (context is the field). These are NOT the same operation.",
        productive_tension="The contradiction INCREASES relational interest. Hearing sound as object and as environment are both valid but different.",
        non_equivalence="Schaeffer brackets context; Schafer requires context. They are NOT equivalent — the contradiction is the relation.",
        epistemic_difference="Both MUSIC_THEORY but opposed orientations: object vs field.",
        evidence_refs=["source:schaeffer:traite_des_objets_musicaux"],
        activation_context="When listening to a sound and asking: is it an object or an environment?",
        lexical_overlap=1,
        relevance_manifold=RelevanceManifold(productive_contradiction=0.9, perceptual_resonance=0.7, epistemic_distance=0.3),
        cosmicoxes_grammar="contradiction: atracao/repulsao simultanea",
    ),
    DeepRelation(
        relation_id="dr:llansol_didi_huberman_nachleben",
        relation_type="temporal_anachronistic_resonance",
        source_nodes=["method:llansol"],
        target_nodes=["method:didi_huberman"],
        basis_axes=["temporal_resonance", "historical_distance"],
        bridge_explanation="Both describe survival of the past in the present: Llansol through cena-fulgor; Didi-Huberman through Nachleben. Both refuse linear temporality.",
        productive_tension="Llansol's survival is textual-literary; Didi-Huberman's is art-historical. They share the structure of anachronistic encounter.",
        non_equivalence="Llansol is literature; Didi-Huberman is art history. They resonate structurally, not identically.",
        epistemic_difference="LITERATURE vs ART_HISTORY",
        evidence_refs=["addendum:final_relational_addendum"],
        activation_context="When a past image, word, or figure returns unexpectedly",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(temporal_resonance=0.85, historical_distance=0.8, formal_resonance=0.6),
        cosmicoxes_grammar="anachronism: coexistencia de ritmos incompativeis",
    ),
    DeepRelation(
        relation_id="dr:merleau_ponty_escuta_identitaria",
        relation_type="embodied_perceptual_resonance",
        source_nodes=["method:merleau_ponty"],
        target_nodes=["milk:escuta_identitaria"],
        basis_axes=["embodied_resonance", "perceptual_resonance"],
        bridge_explanation="Merleau-Ponty's body-world intertwining provides philosophical ground for escuta identitaria: the body that perceives sound is part of the world from which the sound comes.",
        productive_tension="Merleau-Ponty is phenomenology; escuta identitaria is an authorial MILK concept. The relation is philosophical grounding, not identity.",
        non_equivalence="Merleau-Ponty's intertwining is an ontological claim; escuta identitaria is a curatorial method. The latter draws on the former but does not reduce to it.",
        epistemic_difference="PHILOSOPHY vs AUTHORIAL_CONCEPT",
        evidence_refs=["source:merleau-ponty:phenomenology_of_perception"],
        activation_context="When listening is not acoustic processing but bodily-worldly resonance",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(embodied_resonance=0.8, perceptual_resonance=0.75, epistemic_distance=0.5),
        cosmicoxes_grammar="encounter: cruzamento de trajetorias que altera ambas",
    ),
    DeepRelation(
        relation_id="dr:camus_clown_failure",
        relation_type="existential_performative_resonance",
        source_nodes=["method:camus"],
        target_nodes=["clown:birth"],
        basis_axes=["affective_resonance", "productive_contradiction"],
        bridge_explanation="Camus's lucidity without despair resonates with the clown's birth: both face failure/absurd without denial.",
        productive_tension="Camus is philosophical; the clown is performative. The absurd is confronted by lucidity (Camus) or presence (clown) — different modalities, same structure.",
        non_equivalence="Camus's absurd is an ontological condition; the clown's failure is a performative event.",
        epistemic_difference="PHILOSOPHY vs PERFORMANCE_STUDIES",
        evidence_refs=["biblioteca/milk_framework_conceptual.json"],
        activation_context="When failure or absurdity is faced without denial",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(affective_resonance=0.8, productive_contradiction=0.5, epistemic_distance=0.6),
        cosmicoxes_grammar="failure: trajetoria interrompida que pode criar nova ligacao",
    ),
    DeepRelation(
        relation_id="dr:freire_territorial_reading",
        relation_type="pedagogical_territorial_resonance",
        source_nodes=["method:freire"],
        target_nodes=["device:mapping_territorial"],
        basis_axes=["territorial_resonance", "linguistic_resonance", "social_resonance"],
        bridge_explanation="Freire's 'reading the world' resonates with the territorial mapping device: both treat reading as territorial.",
        productive_tension="Freire is pedagogy; the device is curatorial. The relation is through the structure of 'reading the territory'.",
        non_equivalence="Freire's reading the world is a pedagogical-political concept; mapping territorial is a curatorial device.",
        epistemic_difference="PEDAGOGY vs CURATORIAL_DEVICE",
        evidence_refs=["biblioteca/milk_framework_conceptual.json"],
        activation_context="When reading a territory is not cartography but understanding lived relations",
        lexical_overlap=1,
        relevance_manifold=RelevanceManifold(territorial_resonance=0.85, linguistic_resonance=0.7, social_resonance=0.8),
        cosmicoxes_grammar="return: orbita que regressa transformada",
    ),
    DeepRelation(
        relation_id="dr:bispo_materiality_archive",
        relation_type="material_political_resonance",
        source_nodes=["method:bispo_do_rosario"],
        target_nodes=["method:wabi_sabi"],
        basis_axes=["material_resonance", "temporal_resonance"],
        bridge_explanation="Both treat materiality as a site of transformation: Bispo rearranges discarded materials; wabi-sabi finds beauty in the impermanent.",
        productive_tension="Bispo is a singular practice; wabi-sabi is an aesthetic tradition. They share material resistance from different origins.",
        non_equivalence="Bispo's inventory is a singular rearrangement; wabi-sabi is an aesthetic philosophy.",
        epistemic_difference="ART vs AESTHETIC",
        evidence_refs=["addendum:final_relational_addendum"],
        activation_context="When discarded or imperfect material becomes a site of knowledge",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(material_resonance=0.85, temporal_resonance=0.7, epistemic_distance=0.5),
        cosmicoxes_grammar="depth: dimensao vertical de camadas sobrepostas",
    ),
    DeepRelation(
        relation_id="dr:deleuze_cosmicoxes_territory",
        relation_type="territorial_generative_resonance",
        source_nodes=["method:deleuze"],
        target_nodes=["work:cosmic_flow"],
        basis_axes=["territorial_resonance", "formal_resonance", "affective_resonance"],
        bridge_explanation="Deleuze/Guattari's deterritorialization resonates with COSMICOXES as a generative field: both describe a space without a fixed center that proliferates through connections.",
        productive_tension="Deleuze is philosophy; COSMICOXES is a curatorial work. The relation is structural, not illustrative.",
        non_equivalence="Deleuze's concepts are philosophical; COSMICOXES is a performative work. They share a generative structure.",
        epistemic_difference="PHILOSOPHY vs AUTHORIAL_WORK",
        evidence_refs=["biblioteca/milk_framework_conceptual.json"],
        activation_context="When a space generates connections without a fixed center",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(territorial_resonance=0.8, formal_resonance=0.75, affective_resonance=0.6),
        cosmicoxes_grammar="rhizome: ramificacao sem centro unico",
    ),
    DeepRelation(
        relation_id="dr:artaud_clown_presence",
        relation_type="performative_bodily_resonance",
        source_nodes=["method:artaud"],
        target_nodes=["clown:birth"],
        basis_axes=["embodied_resonance", "ritual_resonance"],
        bridge_explanation="Artaud's cruelty as exposure (not violence) resonates with the clown's birth: both involve the body exposed to its limit, where presence emerges from vulnerability.",
        productive_tension="Artaud seeks exposure without representation; the clown finds presence through failure.",
        non_equivalence="Artaud's cruelty is a theatrical principle; the clown's birth is a performative event.",
        epistemic_difference="THEATRE_THEORY vs PERFORMANCE_STUDIES",
        evidence_refs=["addendum:final_relational_addendum"],
        activation_context="When the body is exposed as event, not representation",
        lexical_overlap=0,
        relevance_manifold=RelevanceManifold(embodied_resonance=0.85, ritual_resonance=0.7, epistemic_distance=0.4),
        cosmicoxes_grammar="encounter: cruzamento de trajetorias que altera ambas",
    ),
]

CONSTELLATIONS = [
    {"name": "Husserl-ritmo-Schaeffer-Schafer-escuta_identitaria",
     "hops": ["temporal:retention", "temporal:melody_continuity", "sound:reduced_listening", "method:schafer", "milk:escuta_identitaria"],
     "description": "From retention to rhythm to sound-object to soundscape to identity-listening",
     "preserves_contradiction": True,
     "contradiction_note": "Schaeffer (object) and Schafer (field) maintain their opposition."},
    {"name": "Llansol-cena_fulgor-Didi-Huberman-Barthes-Palavra_Ritual",
     "hops": ["method:llansol", "method:didi_huberman", "method:barthes", "work:palavra_ritual"],
     "description": "From textual encounter to image survival to punctum to word-as-ritual",
     "preserves_contradiction": False},
    {"name": "Winnicott-espaco_potencial-brincar-clown-Boal-Campo_Possivel",
     "hops": ["method:winnicott", "clown:birth", "method:boal", "work:campo_do_possivel"],
     "description": "From potential space to clown birth to spect-actor to field of possibility",
     "preserves_contradiction": False},
    {"name": "Freire-leitura_mundo-Motor_Territorial-vestigio-devolucao",
     "hops": ["method:freire", "device:mapping_territorial", "method:toponymy", "method:oral_traditions"],
     "description": "From reading the world to territorial mapping to toponymy to oral tradition",
     "preserves_contradiction": False},
    {"name": "Deleuze-COSMICOXES-Llansol-territory",
     "hops": ["method:deleuze", "method:llansol", "work:cosmic_flow"],
     "description": "From deterritorialization to textual geography to generative field",
     "preserves_contradiction": False},
    {"name": "Schaeffer-suspensao-Chion-causal_semantic_reduced-Schafer-ecologia",
     "hops": ["sound:reduced_listening", "listening:causal", "listening:semantic", "listening:reduced", "method:schafer"],
     "description": "From reduced listening to the three Chion modes to soundscape ecology",
     "preserves_contradiction": True,
     "contradiction_note": "Schaeffer (object) and Schafer (field) maintain contradiction."},
    {"name": "Camus-absurdo-falha_clown-Artaud-presenca-revolta",
     "hops": ["method:camus", "clown:birth", "method:artaud"],
     "description": "From absurd to failure-as-presence to cruelty-as-exposure",
     "preserves_contradiction": False},
]

_NEW_NODES_FOR_GRAPH = [
    ("method:merleau_ponty", "Merleau-Ponty", "METHOD",
     "corpo vivido / percepcao / carne", "body",
     "source:merleau-ponty:phenomenology_of_perception", "SOURCE", "Maurice Merleau-Ponty"),
    ("method:winnicott", "D. W. Winnicott", "METHOD",
     "espaco potencial / brincar / objeto transicional", "body",
     "source:winnicott:playing_and_reality", "SOURCE", "D. W. Winnicott"),
    ("method:barthes", "Roland Barthes", "METHOD",
     "punctum / studium / grano da voz / texto escrevivel", "image",
     "addendum:final_relational_addendum", "SOURCE", "Roland Barthes"),
    ("method:llansol", "Maria Gabriela Llansol", "METHOD",
     "cena-fulgor / legencia / geografia textual", "text",
     "addendum:final_relational_addendum", "SOURCE", "Maria Gabriela Llansol"),
    ("method:didi_huberman", "Georges Didi-Huberman", "METHOD",
     "Nachleben / Pathosformel / anacronismo", "image",
     "addendum:final_relational_addendum", "SOURCE", "Georges Didi-Huberman"),
    ("method:artaud", "Antonin Artaud", "METHOD",
     "crueldade teatral / corpo / presenca", "performance",
     "addendum:final_relational_addendum", "SOURCE", "Antonin Artaud"),
    ("method:maturana_varela", "Maturana/Varela", "METHOD",
     "autopoiese / acoplamento estrutural / enacao", "body",
     "addendum:final_relational_addendum", "SOURCE", "Humberto Maturana, Francisco Varela"),
    ("method:bispo_do_rosario", "Arthur Bispo do Rosario", "METHOD",
     "inventario / rearranjo / materialidade / nomeacao", "object",
     "addendum:final_relational_addendum", "SOURCE", "Arthur Bispo do Rosario"),
    ("method:kandinsky", "Wassily Kandinsky", "METHOD",
     "ponto / linha / plano / tensao / forca / necessidade interior", "image",
     "addendum:final_relational_addendum", "SOURCE", "Wassily Kandinsky"),
    ("clown:birth", "Nascimento do Palhaco", "CONCEPT",
     "nascimento / falha / exposicao / vulnerabilidade / presenca / transformacao", "body",
     "addendum:final_relational_addendum", "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("work:campo_do_possivel", "CAMPO DO POSSIVEL", "WORK",
     "possibilidade / encontro / infraestrutura", "place",
     "biblioteca/milk_framework_conceptual.json", "SOURCE", _MILK_AUTHOR),
    ("work:dado_sem_lado", "CUBO / Dado sem lado", "WORK",
     "dado sem lado / generatividade / indeterminacao", "object",
     "biblioteca/milk_framework_conceptual.json", "SOURCE", _MILK_AUTHOR),
]


def load_depth_profiles(graph) -> dict:
    """Attach ConceptDepthProfile to hypergraph nodes and register new nodes/edges."""
    from .hypergraph import HyperNode, HyperEdge, EDGE_TYPES
    from .method_repertoire import _addendum_node

    profiles_attached = 0
    new_nodes_created = 0
    new_edges_created = 0

    for node_id, label, ntype, operation, modality, source_ptr, epistemic, author in _NEW_NODES_FOR_GRAPH:
        if graph.get_node(node_id) is None:
            entry = (node_id, label, ntype, operation, modality, source_ptr, epistemic, author, {})
            graph.add_node(_addendum_node(entry))
            new_nodes_created += 1

    for node_id, dp in DEPTH_PROFILES.items():
        node = graph.get_node(node_id)
        if node is not None:
            node.metadata["depth_profile"] = dp.to_dict()
            profiles_attached += 1

    for dr in DEEP_RELATIONS:
        for src in dr.source_nodes:
            for tgt in dr.target_nodes:
                if graph.get_node(src) and graph.get_node(tgt):
                    edge_id = f"dr:{src}->{tgt}"
                    graph.add_edge(HyperEdge(
                        id=edge_id, source=src, edge_type="RELATED_TO",
                        target=tgt, confidence=0.75,
                        validation_state="validated",
                        source_ref="addendum:depth_relations",
                        metadata={
                            "deep_relation": dr.to_dict(),
                            "non_equivalence": dr.non_equivalence,
                            "lexical_overlap": dr.lexical_overlap,
                            "cosmicoxes_grammar": dr.cosmicoxes_grammar,
                        }))
                    new_edges_created += 1

    for gap_id, gap_info in RESEARCH_GAPS_REGISTRY.items():
        graph.create_gap(
            question=gap_info["question"],
            missing_evidence=gap_info["missing_evidence"],
            territory=gap_info.get("territory", ""),
            confidence=0.0)

    return {
        "profiles_attached": profiles_attached,
        "new_nodes_created": new_nodes_created,
        "new_edges_created": new_edges_created,
        "deep_relations": len(DEEP_RELATIONS),
        "constellations": len(CONSTELLATIONS),
        "research_gaps": len(RESEARCH_GAPS_REGISTRY),
    }
