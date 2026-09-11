"""MILK IA - Concept Depth Profiles (Phase 2-3).

A ConceptDepthProfile carries the deep conceptual structure of each
reference in the MILK repertoire. It is NOT a second library — it is a
metadata overlay on the existing SovereignHypergraph nodes, stored in the
node's ``metadata`` dict under the key ``depth_profile``.

Every field may be:
  - a string/dict with real, source-grounded content
  - "N/A" when explicitly not applicable
  - "RESEARCH_GAP" when unknown and needs investigation

Nothing is fabricated. Depth comes from established knowledge of the
thinker's actual published work, not from invention.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# ConceptDepthProfile dataclass
# ---------------------------------------------------------------------------

DEPTH_AXES = (
    "ontology", "temporality", "perception", "attention", "body",
    "gesture", "affect", "memory", "language", "image", "sound",
    "space", "territory", "materiality", "sociality", "power",
    "ritual", "play", "failure", "silence", "uncertainty",
    "transformation", "return",
)

RELEVANCE_AXES = (
    "ontological_resonance", "temporal_resonance", "perceptual_resonance",
    "embodied_resonance", "affective_resonance", "linguistic_resonance",
    "material_resonance", "territorial_resonance", "social_resonance",
    "political_resonance", "ritual_resonance", "formal_resonance",
    "productive_contradiction", "epistemic_distance", "historical_distance",
)


@dataclass
class ConceptDepthProfile:
    """Deep conceptual structure for a repertoire reference."""
    # Provenance
    source_pointer: str = ""
    source_type: str = ""
    author: str = ""
    work: str = ""
    publication_context: str = ""
    epistemic_status: str = ""

    # Foundational
    historical_context: str = "N/A"
    foundational_problem: str = "N/A"
    foundational_question: str = "N/A"

    # Conceptual nucleus
    conceptual_nucleus: str = "N/A"
    extended_definition: str = "N/A"
    what_it_changes: str = "N/A"
    what_it_resists: str = "N/A"
    what_it_is_not: str = "N/A"

    # Axes (dict of axis -> description or "N/A")
    axes: dict[str, str] = field(default_factory=dict)

    # Relational
    internal_dependencies: list[str] = field(default_factory=list)
    conceptual_neighbors: list[str] = field(default_factory=list)
    productive_antagonists: list[str] = field(default_factory=list)
    known_tensions: list[str] = field(default_factory=list)
    counter_readings: list[str] = field(default_factory=list)
    misreading_risks: list[str] = field(default_factory=list)

    # Operators
    curatorial_operator: str = "N/A"
    experiential_operator: str = "N/A"
    territorial_operator: str = "N/A"
    cross_modal_potential: str = "N/A"

    # COSMICOXES
    cosmicoxes_projection: str = "N/A"

    # Validation
    human_validation_required: bool = False
    rights_provenance: str = "N/A"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_pointer": self.source_pointer,
            "source_type": self.source_type,
            "author": self.author,
            "work": self.work,
            "publication_context": self.publication_context,
            "epistemic_status": self.epistemic_status,
            "historical_context": self.historical_context,
            "foundational_problem": self.foundational_problem,
            "foundational_question": self.foundational_question,
            "conceptual_nucleus": self.conceptual_nucleus,
            "extended_definition": self.extended_definition,
            "what_it_changes": self.what_it_changes,
            "what_it_resists": self.what_it_resists,
            "what_it_is_not": self.what_it_is_not,
            "axes": dict(self.axes),
            "internal_dependencies": list(self.internal_dependencies),
            "conceptual_neighbors": list(self.conceptual_neighbors),
            "productive_antagonists": list(self.productive_antagonists),
            "known_tensions": list(self.known_tensions),
            "counter_readings": list(self.counter_readings),
            "misreading_risks": list(self.misreading_risks),
            "curatorial_operator": self.curatorial_operator,
            "experiential_operator": self.experiential_operator,
            "territorial_operator": self.territorial_operator,
            "cross_modal_potential": self.cross_modal_potential,
            "cosmicoxes_projection": self.cosmicoxes_projection,
            "human_validation_required": self.human_validation_required,
            "rights_provenance": self.rights_provenance,
        }


# ---------------------------------------------------------------------------
# RelevanceManifold — multiaxial relevance vector (NOT a scalar)
# ---------------------------------------------------------------------------

@dataclass
class RelevanceManifold:
    """Multiaxial relevance vector. Never collapsed to a single score.

    A pair can have low semantic_similarity but high temporal_resonance
    and high formal_resonance and still be extremely fertile.
    """
    ontological_resonance: float = 0.0
    temporal_resonance: float = 0.0
    perceptual_resonance: float = 0.0
    embodied_resonance: float = 0.0
    affective_resonance: float = 0.0
    linguistic_resonance: float = 0.0
    material_resonance: float = 0.0
    territorial_resonance: float = 0.0
    social_resonance: float = 0.0
    political_resonance: float = 0.0
    ritual_resonance: float = 0.0
    formal_resonance: float = 0.0
    productive_contradiction: float = 0.0
    epistemic_distance: float = 0.0
    historical_distance: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {axis: getattr(self, axis) for axis in RELEVANCE_AXES}

    def dominant_axes(self, threshold: float = 0.5) -> list[str]:
        """Return axes above threshold, sorted by value."""
        vals = [(axis, getattr(self, axis)) for axis in RELEVANCE_AXES
                if getattr(self, axis) >= threshold]
        vals.sort(key=lambda x: -x[1])
        return [axis for axis, _ in vals]


# ---------------------------------------------------------------------------
# DeepRelation — non-lexical, non-equivalent conceptual relation
# ---------------------------------------------------------------------------

@dataclass
class DeepRelation:
    """A conceptual relation that is NOT deduced primarily by lexical overlap.

    Every relation declares its non_equivalence: the two nodes are related
    but NOT equivalent. The bridge_explanation describes the structural
    resonance; the non_equivalence describes why they remain distinct.
    """
    relation_id: str
    relation_type: str
    source_nodes: list[str]
    target_nodes: list[str]
    basis_axes: list[str]
    bridge_explanation: str
    productive_tension: str
    non_equivalence: str
    epistemic_difference: str
    evidence_refs: list[str]
    activation_context: str
    lexical_overlap: int = 0
    relevance_manifold: RelevanceManifold | None = None
    cosmicoxes_grammar: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "source_nodes": list(self.source_nodes),
            "target_nodes": list(self.target_nodes),
            "basis_axes": list(self.basis_axes),
            "bridge_explanation": self.bridge_explanation,
            "productive_tension": self.productive_tension,
            "non_equivalence": self.non_equivalence,
            "epistemic_difference": self.epistemic_difference,
            "evidence_refs": list(self.evidence_refs),
            "activation_context": self.activation_context,
            "lexical_overlap": self.lexical_overlap,
            "relevance_manifold": self.relevance_manifold.to_dict() if self.relevance_manifold else None,
            "cosmicoxes_grammar": self.cosmicoxes_grammar,
        }


# ---------------------------------------------------------------------------
# COSMICOXES relational grammar — generative spatial/temporal behavior
# ---------------------------------------------------------------------------

COSMICOXES_GRAMMAR: dict[str, str] = {
    "retention": "afterglow / rastro que permanece",
    "protention": "vetor/tensao para regiao ainda nao ocupada",
    "rupture": "quebra de trajetoria",
    "resonance": "sincronizacao parcial",
    "contradiction": "atracao/repulsao simultanea",
    "silence": "regiao de baixa actividade com potencial alto",
    "emergence": "formacao nao predeterminada",
    "scene_fulgor": "condensacao subita de intensidade",
    "rhizome": "ramificacao sem centro unico",
    "potential_space": "regiao de jogo com topologia permissiva",
    "failure": "trajetoria interrompida que pode criar nova ligacao",
    "return": "orbita que regressa transformada",
    "anachronism": "coexistencia de ritmos/temporalidades incompativeis",
    "dialogism": "multiplas trajetorias que nao colapsam numa voz",
    "carnival": "inversao temporaria de hierarquias",
    "punctum": "perturbacao singular de campo",
    "soundscape": "propriedade distribuida do campo, nao do no isolado",
    "dopafania_bloom": "salience bloom (NUNCA representacao pseudo-cientifica de dopamina)",
    "tension": "forca direcional entre dois pontos",
    "threshold": "zona de transicao entre estados",
    "depth": "dimensao vertical de camadas sobrepostas",
    "encounter": "cruzamento de trajetorias que altera ambas",
    "void": "regiao vazia com potencial de preenchimento",
    # --- Systemic/Complexity delta states ---
    "reinforcing_loop": "expanding spiral / growing orbit",
    "balancing_loop": "convergence toward region",
    "delay": "visible phase lag",
    "phase_lag": "temporal offset between cause and observable effect",
    "overshoot": "crossing target before correction",
    "oscillation": "recurrent trajectory around goal",
    "damping": "progressive reduction of amplitude",
    "accumulation": "growing stock / increasing density",
    "depletion": "shrinking stock / decreasing density",
    "recursion": "output becomes input of next cycle",
    "observer_effect": "observing node becomes causal participant",
    "reflexivity": "model changes what it models",
    "self_organization": "order arising without external command",
    "order_from_noise": "structure emerging from apparent disorder",
    "attractor": "trajectory converging toward a region",
    "bifurcation": "trajectory splitting into divergent paths",
    "sensitive_divergence": "nearby trajectories separate progressively",
    "dialogical_coexistence": "two incompatible patterns coexist",
    "hologrammatic_nesting": "local structure recursively echoes global organization",
    "polyphony": "multiple simultaneous layers without collapse",
    "multiscale": "phenomenon operates at multiple scales simultaneously",
    "unresolved_tension": "contradiction maintained without resolution",
    "gritaria": "overlapping high-intensity trajectories",
    "laughter": "punctuated contagious rhythmic propagation",
    "contemplation": "sustained low-velocity attention trajectory",
}


def cosmicoxes_projection_for(concept: str) -> str:
    """Return the COSMICOXES spatial/temporal grammar for a concept."""
    c = concept.lower().strip()
    for key, grammar in COSMICOXES_GRAMMAR.items():
        if key in c or c in key:
            return grammar
    return "trajetoria emergente — comportamento nao predeterminado"
