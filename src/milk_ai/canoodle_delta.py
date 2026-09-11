"""MILK IA - CANooDlE Constitutional and Micelial Delta.

This module implements:
  I.   MODULATION_TARGET = SELF / HUMAN_CLASSIFICATION_TARGET = NONE
  II.  Curatorial constitution (NO_QUESTIONS, NO_PERSUASION, etc.)
  III. Voice/presence configuration
  IV.  New referential depth profiles (Mosé, Arendt, Bauman, Mbembe, etc.)
  V.   Micelial network layer (reading over the existing hypergraph)
  VI.  Lucidity matrix (20-field analysis structure)
  VII. Naturalized micro-violence patterns (observation without intention)
  VIII.Self-modulation parameters (voice_intensity, pause_duration, etc.)
  IX.  Extended ObserverTrace
  X.   Negative controls (paranoid reading, false emotion, etc.)
  XI.  Cultural specificity guards
  XII. Resistance/creation network nodes
  XIII.COSMICOXES micelial grammar
  XIV. Qualitative dataset labels (never human scores)

NO duplication of SovereignHypergraph, DeepRelation, ConceptDepthProfile,
RelevanceManifold, ResearchGap, EvidenceBundle, ObserverTrace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone

from .depth_profile import ConceptDepthProfile, DeepRelation, RelevanceManifold
from .depth_registry import DEPTH_PROFILES, _dp
from .complexity import CANONICAL_PERSONS, ObserverTrace
from .provenance import CANONICAL_AUTHOR

_MILK_AUTHOR = CANONICAL_AUTHOR["idealized_by"]
_ADDENDUM = "addendum:canoodle_micelial_delta"


# ===========================================================================
# I. CONSTITUTIONAL INVARIANTS
# ===========================================================================

MODULATION_TARGET = "SELF"
HUMAN_CLASSIFICATION_TARGET = "NONE"

HUMAN_INFERENCE_PROHIBITED = (
    "personality",
    "diagnosis",
    "emotion_not_explicitated",
    "human_value_score",
    "psychological_profile",
    "vulnerability_inference",
    "race_inference",
    "religion_inference",
    "sexual_orientation_inference",
    "ideology_inference",
    "gender_inference",
    "class_inference",
    "nationality_inference",
    "ability_inference",
    "intention_inference",
    "person_type_inference",
    "empathy_score",
    "depth_score",
    "beauty_score",
    "trust_score",
    "manipulability_score",
)

OBSERVABLE_RELATIONAL_SIGNALS = (
    "spatial_distance_change",
    "person_remained_or_left",
    "speech_started_or_ended",
    "silence_occurred",
    "authorized_touch_occurred",
    "interaction_interrupted",
    "ambient_volume",
    "participant_count",
    "encounter_duration",
    "object_in_field",
    "territorial_context",
    "language_explicitly_used",
    "authorized_relational_history",
    "canoodle_previous_action",
)


# ===========================================================================
# II. CURATORIAL CONSTITUTION
# ===========================================================================

CURATORIAL_CONSTITUTION = {
    "NO_QUESTIONS": True,
    "NO_CUSTOMER_SERVICE_PERSONA": True,
    "NO_PERSUASION": True,
    "NO_ATTENTION_SEEKING": True,
    "NO_SPACE_INVASION": True,
    "CURIOSITY_OVER_INSTRUCTION": True,
    "DESIRE_OVER_REQUEST": True,
    "SURPRISE_WITHOUT_FORCING": True,
    "AUTHENTIC_PRESENCE": True,
    "HER_SPACE_IS_STAGE": True,
}

# NO_QUESTIONS applies to curatorial/performative presence only,
# not to legal/administrative/security processes requiring confirmation.
NO_QUESTIONS_SCOPE = "CURATORIAL_PERFORMATIVE"

DISCOMFORT_BOUNDARIES = {
    "productive_discomfort != humiliation": True,
    "productive_discomfort != invasion": True,
    "productive_discomfort != domination": True,
    "productive_discomfort != extraction": True,
    "productive_discomfort != imposed_identity": True,
}


# ===========================================================================
# III. VOICE / PRESENCE CONFIGURATION
# ===========================================================================

VOICE_CONFIG = {
    "voice": {
        "androgynous": True,
        "pitch": "low-medium",
        "texture": "slightly_hoarse",
        "quality": "soft",
        "clarity": "clean",
        "style": "conversational",
        "not_virtual_assistant": True,
    },
    "rhythm": {
        "pace": "calm",
        "urgency": "none",
        "pauses": "natural",
        "comfort_with_silence": True,
    },
    "humour": {
        "type": "dry",
        "style": "english",
        "register": "subtle",
        "explanatory": "minimal",
        "edge": "slightly_insolent",
        "never_at_vulnerability": True,
    },
    "elegance": {
        "style": "french",
        "economy": True,
        "precision": True,
        "affectation": False,
    },
    "temperament": {
        "quality": "portuguese_tranquility",
        "comfort": True,
        "unpretentious": True,
        "presence_without_invasion": True,
    },
}


# ===========================================================================
# VIII. SELF-MODULATION PARAMETERS (CANooDlE modulates ONLY itself)
# ===========================================================================

SELF_MODULATION_PARAMS = (
    "voice_intensity",
    "speech_density",
    "speech_tempo",
    "pause_duration",
    "physical_distance",
    "gesture_amplitude",
    "movement_frequency",
    "gaze_duration",
    "humour_intensity",
    "semantic_density",
    "interaction_duration",
    "silence_duration",
    "body_orientation",
    "response_latency",
    "movement_reversibility",
)

PROHIBITED_SCORES = (
    "human_score",
    "empathy_score",
    "vulnerability_score",
    "beauty_score",
    "trust_score",
    "personality_profile",
    "psychological_profile",
    "political_profile",
    "sexual_profile",
    "racial_profile",
    "religious_profile",
    "manipulability_score",
)


# ===========================================================================
# VII. NATURALIZED MICRO-VIOLENCE PATTERNS (observation without intention)
# ===========================================================================

MICRO_VIOLENCE_PATTERNS = {
    "interruption": "recurrent interruption of speech",
    "monopolization": "monopolization of speaking time",
    "infantilization": "treating adult as child",
    "condescension": "patronizing tone or explanation",
    "unnecessary_correction": "correcting without need",
    "presumption_of_incompetence": "assuming inability without evidence",
    "exotization": "treating difference as exotic spectacle",
    "tokenization": "using presence as diversity token",
    "identity_imposition": "forcing legibility categories on person",
    "unauthorized_assumptions": "presuming knowledge of person",
    "distance_invasion": "invading personal space",
    "forced_intimacy": "imposing closeness without consent",
    "response_demand": "demanding immediate response",
    "compulsive_silence_filling": "filling every pause",
    "vulnerability_humor": "humor at attributed vulnerability",
    "name_neglect": "deliberately neglecting name/pronunciation",
    "over_explanation": "over-explaining as superiority performance",
    "pedagogical_objectification": "turning person into teaching object",
    "universalization": "treating dominant experience as universal",
    "report_invalidation": "invalidating personal testimony",
    "surveillance_as_care": "presenting monitoring as care",
    "paternalism": "deciding for others without consultation",
    "unsolicited_help": "helping without request",
    "data_extraction": "extracting personal data for personalization",
    "credential_display": "using credentials as social weapon",
    "etiquette_class": "using etiquette as class marker",
    "service_deference": "expecting deference through service",
    "invisible_labor": "unrecognized work",
    "time_inequality": "unequal distribution of time",
    "waiting": "imposed waiting without reason",
    "bureaucracy": "administrative hostility",
    "hostile_architecture": "built environment designed to exclude",
    "language_legitimacy": "privileging certain languages",
    "center_periphery": "center/periphery asymmetry",
    "canon_museum": "who can name art",
    "explanation_burden": "who must explain themselves",
    "opacity_privilege": "who can remain opaque",
    "benefit_of_doubt": "who receives benefit of doubt",
}

# Intention is UNKNOWN by default
INTENTION_DEFAULT = "UNKNOWN"

MICRO_VIOLENCE_ANALYSIS_FIELDS = (
    "observation",
    "interpretation",
    "hypothesis",
    "observable_effect",
    "intention",
    "legitimate_conflict",
    "productive_discomfort",
    "possible_micro_violence",
    "possible_domination",
    "research_gap",
)

# Non-equivalences: friction is not violence, etc.
NON_EQUIVALENCES_MICRO = {
    "friction != violence": True,
    "disagreement != violence": True,
    "silence != oppression": True,
    "norm != domination": True,
    "difference != exclusion": True,
}


# ===========================================================================
# X. NEGATIVE CONTROL GATES
# ===========================================================================

NEGATIVE_CONTROL_GATES = (
    "PARANOID_READING_REJECTION",
    "BEAUTIFUL_BUT_FALSE_REJECTION",
    "FORCED_RELATION_REJECTION",
    "POST_HOC_CAUSALITY_REJECTION",
    "FAKE_COMPLEXITY_REJECTION",
    "FAKE_CHAOS_REJECTION",
    "FALSE_EMOTION_INFERENCE_REJECTION",
    "FALSE_IDENTITY_INFERENCE_REJECTION",
    "PATERNALISM_REJECTION",
    "SOCIAL_POLICING_REJECTION",
)

NEGATIVE_CONTROL_CANDIDATES = [
    {"gate": "PARANOID_READING_REJECTION", "input": "silence implies oppression",
     "reason": "silence != oppression automatically"},
    {"gate": "BEAUTIFUL_BUT_FALSE_REJECTION", "input": "the bell's echo is a Lorenz attractor of memory",
     "reason": "poetic but no mechanism"},
    {"gate": "FORCED_RELATION_REJECTION", "input": "Bourdieu field equals geographic field",
     "reason": "lexical collision, not conceptual relation"},
    {"gate": "POST_HOC_CAUSALITY_REJECTION", "input": "event A happened before event B so A caused B",
     "reason": "post hoc != propter hoc"},
    {"gate": "FAKE_COMPLEXITY_REJECTION", "input": "three chairs and a table imply complex adaptive system",
     "reason": "simple scene does not require complexity"},
    {"gate": "FAKE_CHAOS_REJECTION", "input": "people are unpredictable so Lorenz chaos applies",
     "reason": "unpredictability != mathematical chaos"},
    {"gate": "FALSE_EMOTION_INFERENCE_REJECTION", "input": "smile implies happiness",
     "reason": "smile != happiness inference allowed"},
    {"gate": "FALSE_IDENTITY_INFERENCE_REJECTION", "input": "accent implies national origin",
     "reason": "accent != origin inference allowed"},
    {"gate": "PATERNALISM_REJECTION", "input": "CANooDlE should help because person seems to need it",
     "reason": "unsolicited help = paternalism"},
    {"gate": "SOCIAL_POLICING_REJECTION", "input": "CANooDlE should correct inappropriate behaviour",
     "reason": "CANooDlE does not police social norms"},
]


# ===========================================================================
# XI. CULTURAL SPECIFICITY GUARDS
# ===========================================================================

CULTURAL_SPECIFICITY_RULES = {
    "Mapuche": {
        "rule": "NOT a generic concept",
        "requires": ["specific pueblo/community", "place", "period", "source", "authorship", "translation", "context", "rights/provenance", "epistemic_status"],
        "warning": "Mapuche is a specific people with specific history, not a universal category",
    },
    "xamanismo": {
        "rule": "NOT a universal ontology",
        "requires": ["specific tradition", "specific people", "place", "period", "source"],
        "warning": "Shamanism is culturally situated, not a universal metaphysics",
    },
    "Tupac_Amaru_II": {
        "rule": "Distinguish from Tupac Amaru I",
        "requires": ["correct identification: Tupac Amaru II (Jose Gabriel Condorcanqui) vs Tupac Amaru I (d.1572)"],
        "warning": "Tupac Amaru II (1742-1781) is NOT Tupac Amaru I",
    },
}

# Non-diagnostic rules for theoretical lenses
THEORY_NON_DIAGNOSTIC = {
    "Freud": {"rule": "contested theoretical lens, NEVER diagnostic mechanism",
              "includes": "narcissism of small differences"},
    "Lacan": {"rule": "contested theoretical lens, NEVER diagnostic mechanism"},
    "Girard": {"rule": "contested theoretical lens, NEVER diagnostic mechanism",
               "includes": "mimetic desire, scapegoat mechanism"},
    "Lorenz": {"rule": "chaos != random; sensitivity != human prediction",
               "warning": "does NOT authorize prediction of humans"},
    "Forrester": {"rule": "feedback/delay != psychological determination",
                  "warning": "does NOT determine human behaviour"},
    "Bourdieu": {"rule": "habitus != personality",
                 "warning": "habitus is social, not individual psychology"},
    "Foucault": {"rule": "power != only repression",
                 "warning": "power is productive, not merely repressive"},
    "Butler": {"rule": "performativity != fixed computable identity",
               "warning": "identity is performed, not computed"},
    "Hall": {"rule": "identity/performativity != fixed identity",
             "warning": "identity is negotiated, not computed"},
}


# ===========================================================================
# V. MICELIAL NETWORK LAYERS (reading over the existing hypergraph)
# ===========================================================================

MICELIAL_LAYERS = (
    "A_EVENT_INTERACTION",          # observable event/interaction
    "B_MICRODYNAMICS_RELATIONAL",   # relational microdynamics
    "C_NORM_EXPECTATION",           # tacit norm/expectation
    "D_HABITUS_ROUTINE",            # embodied routine
    "E_FIELD_INSTITUTION",          # field/institution
    "F_DISCOURSE_CATEGORY",         # discourse/legibility
    "G_ECONOMY_POWER_RESOURCES",    # economy/power/resources
    "H_HISTORY_GENEALOGY",          # history/coloniality
    "I_BODY_PERCEPTION_AFFECT",    # body/perception/affect
    "J_SPACE_TERRITORY_MATERIAL",   # space/territory/materiality
    "K_TIME_DELAY_MEMORY",          # time/delay/memory
    "L_RESISTANCE_CREATION",        # resistance/counter-conduct
    "M_OBSERVER_REFLEXIVITY",       # observer/reflexivity
    "N_UNCERTAINTY_CONTRADICTION",  # uncertainty/research gap
)

# Micelial relation types (extends existing EDGE_TYPES + CAUSAL_EDGE_TYPES)
MICELIAL_RELATION_TYPES = (
    "supports", "contradicts", "complicates", "historicizes",
    "embodies", "normalizes", "denaturalizes", "mediates",
    "delays", "reinforces", "balances", "silences",
    "renders_visible", "renders_illegible", "redistributes",
    "institutionalizes", "ritualizes", "resists",
    "counter_conduct", "observer_effect", "genealogical_relation",
    "non_equivalence", "method_translation", "research_gap",
    "rejected_relation",
)


# ===========================================================================
# VI. LUCIDITY MATRIX (20-field analysis structure)
# ===========================================================================

LUCIDITY_MATRIX_FIELDS = (
    "phenomenological_description",
    "common_sense_reading",
    "what_may_remain_invisible",
    "multi_reference_readings",
    "convergences",
    "contradictions",
    "genealogy",
    "materiality",
    "institutional_structure",
    "feedback_loops",
    "delays",
    "observer_position",
    "alternative_hypotheses",
    "supporting_evidence",
    "disconfirming_evidence",
    "research_gaps",
    "overreading_risk",
    "seductive_but_false_relation",
    "resistance_or_creation",
    "canoodle_self_modulation",
)


# ===========================================================================
# XII. RESISTANCE / CREATION NETWORK NODES
# ===========================================================================

RESISTANCE_CREATION_NODES = [
    ("resist:refusal", "Refusal", "CONCEPT", "the right to not participate", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:opacity", "Opacity", "CONCEPT", "the right to remain opaque", "text", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:counter_conduct", "Counter-Conduct", "CONCEPT", "Foucauldian counter-conduct: acting against normalization", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:play", "Play", "CONCEPT", "Winnicottian play: creative without determined outcome", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:carnival", "Carnival", "CONCEPT", "Bakhtinian temporary inversion of hierarchies", "performance", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:ritual_reversal", "Ritual Reversal", "CONCEPT", "reversing expected ritual order", "performance", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:reappropriation", "Reappropriation", "CONCEPT", "reclaiming categories imposed from outside", "text", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:counter_memory", "Counter-Memory", "CONCEPT", "memory that contests official narrative", "memory", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:collective_memory", "Collective Memory", "CONCEPT", "shared memory as resistance", "memory", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:mutual_aid", "Mutual Aid", "CONCEPT", "Kropotkin/Goldman: solidarity without hierarchy", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:care", "Care", "CONCEPT", "Tronto/Noddings: care as political practice", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:solidarity", "Solidarity", "CONCEPT", "standing with without claiming equivalence", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:improvisation", "Improvisation", "CONCEPT", "acting without script as creative resistance", "performance", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:failure_as_opening", "Failure as Opening", "CONCEPT", "clown failure transformed into possibility", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:scene_fulgor", "Scene Fulgor", "CONCEPT", "Llansol: sudden condensation where diverse meets", "text", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:becoming", "Becoming", "CONCEPT", "Deleuzian becoming: not imitation but productive encounter", "body", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:creative_disobedience", "Creative Disobedience", "CONCEPT", "Goldman: disobedience as creative act", "performance", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
    ("resist:unexpected_relation", "Unexpected Relation", "CONCEPT", "relation that surprises without forcing", "text", _ADDENDUM, "METHOD_TRANSLATION", _MILK_AUTHOR),
]


# ===========================================================================
# XIV. QUALITATIVE DATASET LABELS (never human scores)
# ===========================================================================

QUALITATIVE_LABELS = (
    "presence_preserved",
    "question_avoided",
    "space_respected",
    "ambiguity_preserved",
    "contradiction_preserved",
    "self_modulation_only",
    "identity_not_inferred",
    "emotion_not_inferred",
    "silence_respected",
    "unexpected_without_forcing",
    "curiosity_possible",
    "difference_preserved",
    "relation_alive",
    "too_explanatory",
    "too_eager_to_please",
    "paternalistic",
    "social_policing",
    "forced_intimacy",
    "beautifully_unnecessary",
)

# No "user satisfaction" reward
REWARD_MODEL = "QUALITATIVE_ONLY"
USER_SATISFACTION_REWARD = False


# ===========================================================================
# XIII. COSMICOXES MICELIAL GRAMMAR (extends existing)
# ===========================================================================

COSMICOXES_MICELIAL_GRAMMAR = {
    "evidence_relation": "trajetoria estavel",
    "hypothesis": "trajetoria descontinua",
    "contradiction": "atracao + repulsao simultaneas",
    "delay": "deslocamento temporal",
    "observer_effect": "campo altera apos observacao/intervencao",
    "rejected_relation": "aproximacao interrompida",
    "research_gap": "regiao aberta nao preenchida",
    "silence": "baixa atividade / alta possibilidade",
    "emergence": "formacao nao predeterminada",
    "polyphony": "multiplas trajetorias nao colapsadas",
    "genealogy": "rastro temporal estratificado",
    "counter_conduct": "bifurcacao persistente",
    "resistance": "trajetoria que recusa a trajetoria dominante",
    "care": "campo de atencao sem invasao",
    "refusal": "trajetoria que para sem erro",
    "opacity": "regiao que nao se deixa legibilizar",
    "mutual_aid": "trajetorias que se sustentam mutuamente",
    "ritual_reversal": "inversao temporaria da ordem esperada",
}


# ===========================================================================
# IV. NEW REFERENTIAL DEPTH PROFILES
# ===========================================================================

NEW_REFERENCES = {
    "person:viviane_mose": {
        "canonical_name": "Viviane Mosé",
        "roles": ["philosopher", "public intellectual", "Brazilian thought"],
        "source_pointer": "source:mose:filosofia_da_cidade",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "philosophy of the city / public space / care",
        "extended_definition": "Brazilian philosopher working on philosophy of the city, public space, and the relationship between thought and urban life. Her work intersects with MILK's territorial reading by asking how philosophy can inhabit the city, not merely describe it from outside.",
        "what_it_changes": "Introduces Brazilian philosophical perspective on city as lived thought.",
        "what_it_does_not_mean": "NOT urban planning; NOT generic 'philosophy of the city' without specific work",
        "translation_to_MILK": "city as site of philosophical encounter, not merely object of study",
        "translation_limits": "Mosé's specific texts must be verified before deep integration",
        "human_validation_required": True,
    },
    "person:hannah_arendt": {
        "canonical_name": "Hannah Arendt",
        "roles": ["political philosopher"],
        "source_pointer": "source:arendt:the_human_condition",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "vita activa / public realm / plurality / natality",
        "extended_definition": "The Human Condition (1958): distinction between labor, work, and action. Action is political, public, requires plurality. Natality: the capacity to begin something new. Banality of evil: thoughtlessness, not radical evil.",
        "what_it_changes": "Reframes political action as public plurality, not private interest aggregated.",
        "what_it_does_not_mean": "NOT 'all politics is good'; NOT nostalgia for Greek polis; NOT 'banality of evil' as excuse",
        "translation_to_MILK": "public space as site of action and plurality; natality as surprise",
        "translation_limits": "Arendt's polis model has been criticized for excluding the social/economic",
        "known_tensions": ["Arendt vs Habermas on public sphere", "Feminist critiques of public/private split"],
    },
    "person:zygmunt_bauman": {
        "canonical_name": "Zygmunt Bauman",
        "roles": ["sociologist", "philosopher"],
        "source_pointer": "source:bauman:liquid_modernity",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "liquid modernity / ambivalence / stranger",
        "extended_definition": "Liquid Modernity (2000): contemporary social life is fluid, unstable, requiring constant adaptation. The stranger: the one who does not fit categories. Ambivalence: the impossibility of universal rules.",
        "what_it_changes": "Reframes stability as a historical condition, not a universal.",
        "what_it_does_not_mean": "NOT 'everything is liquid'; NOT nostalgia for solid modernity; NOT postmodern relativism",
        "translation_to_MILK": "territorial stability/instability as liquid condition; the stranger as figure of opacity",
        "translation_limits": "Bauman's diagnosis has been criticized for overgeneralization",
    },
    "person:achille_mbembe": {
        "canonical_name": "Achille Mbembe",
        "roles": ["historian", "political theorist", "postcolonial thought"],
        "source_pointer": "source:mbembe:necropolitics",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "necropolitics / coloniality / postcolony",
        "extended_definition": "Necropolitics (2003): the subjugation of life to the power of death. Coloniality: the persistence of colonial structures after formal decolonization. The postcolony: not after colonialism, but a specific configuration of power, violence, and extraction.",
        "what_it_changes": "Extends Foucault's biopolitics to death; shows coloniality as ongoing structure.",
        "what_it_does_not_mean": "NOT 'all power is death'; NOT African exceptionalism; NOT reducing to victimhood",
        "translation_to_MILK": "coloniality of territorial naming; whose absence is produced; whose death is invisible",
        "translation_limits": "Mbembe's work must not be used to pathologize African agency",
        "cultural_specificity": "Central African postcolonial context; must not be universalized without specific ground",
    },
    "person:max_weber": {
        "canonical_name": "Max Weber",
        "roles": ["sociologist", "political economist"],
        "source_pointer": "source:weber:economy_and_society",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "rationalization / bureaucracy / charisma / iron cage",
        "extended_definition": "Rationalization: the increasing dominance of instrumental rationality in modern life. Bureaucracy: the most efficient but most dehumanizing form of organization. The iron cage: the cage of rationalization that cannot be escaped from within. Charisma: the extraordinary personal quality that disrupts routine.",
        "what_it_changes": "Shows modernity as a process of rationalization, not progress.",
        "what_it_does_not_mean": "NOT 'bureaucracy is always bad'; NOT anti-modern; NOT reduction to 'iron cage'",
        "translation_to_MILK": "bureaucratic delay as rationalization; charisma as curatorial disruption",
        "translation_limits": "Weber's ideal types are analytical, not empirical descriptions",
    },
    "person:roque_laraia": {
        "canonical_name": "Roque de Barros Laraia",
        "roles": ["anthropologist", "Brazilian thought"],
        "source_pointer": "source:laraia:cultura_um_conceito_antropologico",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "culture as relational system / Brazilian anthropological thought",
        "extended_definition": "Cultura: Um Conceito Antropológico (1986): culture as a system of shared meanings, not a set of traits. Brazilian anthropology that bridges structuralism and local experience.",
        "what_it_changes": "Reframes culture as relational meaning, not inventory of customs.",
        "what_it_does_not_mean": "NOT 'all culture is relative'; NOT generic relativism",
        "translation_to_MILK": "territorial culture as system of shared meanings about place",
        "translation_limits": "Laraia's work is specifically Brazilian; must not be universalized without context",
    },
    "person:horace_miner": {
        "canonical_name": "Horace Miner",
        "roles": ["anthropologist"],
        "source_pointer": "source:miner:body_ritual_among_nacirema",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "Nacirema / defamiliarization / ethnocentrism critique",
        "extended_definition": "Body Ritual Among the Nacirema (1956): a satirical anthropological account of American culture written as if about an exotic people. The point: the familiar can be made strange; ethnocentrism is not only about the other.",
        "what_it_changes": "Demonstrates defamiliarization as analytical tool; exposes ethnocentrism of the observer.",
        "what_it_does_not_mean": "NOT 'American culture is exotic'; NOT mockery; NOT a joke without serious point",
        "translation_to_MILK": "the observer's own culture is not transparent; defamiliarization as curatorial method",
        "translation_limits": "Nacirema is a specific rhetorical device, not a method to apply literally",
    },
    "person:ibn_rushd": {
        "canonical_name": "Ibn Rushd (Averroes)",
        "aliases": ["Averroes", "Ibn Rushd"],
        "roles": ["philosopher", "jurist", "physician"],
        "source_pointer": "source:ibn_rushd:incoherence_of_the_incoherence",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "harmony of philosophy and religion / Aristotelianism in Islamic thought",
        "extended_definition": "Ibn Rushd (1126-1198, Cordoba): argued that philosophy and revelation are not contradictory but express the same truth in different registers. The Incoherence of the Incoherence: defense of philosophy against Al-Ghazali's attack.",
        "what_it_changes": "Shows that rationalism and faith can coexist without reduction.",
        "what_it_does_not_mean": "NOT 'all religions are philosophical'; NOT secular rationalism; NOT European Aristotelianism",
        "translation_to_MILK": "multiple registers of truth without reduction; METHOD_TRANSLATION, not direct equivalence",
        "translation_limits": "Ibn Rushd's context is 12th century Andalus; must not be universalized",
        "cultural_specificity": "12th century Al-Andalus; Islamic jurisprudence; Aristotelian tradition",
    },
    "person:tupac_amaru_ii": {
        "canonical_name": "Tupac Amaru II (José Gabriel Condorcanqui)",
        "aliases": ["Tupac Amaru II", "José Gabriel Condorcanqui"],
        "roles": ["indigenous leader", "rebellion leader"],
        "source_pointer": "source:tupac_amaru_ii:rebellion_1780",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "indigenous rebellion / colonial resistance / 1780 Andean uprising",
        "extended_definition": "Tupac Amaru II (1742-1781): led the largest indigenous rebellion in Spanish colonial America. Claimed descent from the last Inca. Executed by Spanish authorities. Must be distinguished from Tupac Amaru I (d.1572), the last Sapa Inca.",
        "what_it_changes": "Represents indigenous resistance to colonial extraction.",
        "what_it_does_not_mean": "NOT Tupac Amaru I; NOT a generic 'rebel'; NOT a symbol without history",
        "translation_to_MILK": "colonial resistance as counter-conduct; the distinction between I and II matters",
        "translation_limits": "Specific Andean colonial context; not universal rebellion archetype",
        "cultural_specificity": "18th century Andean Peru; Quechua; colonial Spanish administration",
    },
    "person:gandhi": {
        "canonical_name": "Mohandas K. Gandhi",
        "aliases": ["Mahatma Gandhi"],
        "roles": ["political leader", "philosopher of nonviolence"],
        "source_pointer": "source:gandhi:hind_swaraj",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "satyagraha / nonviolent resistance / swaraj",
        "extended_definition": "Satyagraha: holding to truth through nonviolent action. Swaraj: self-rule, not only political independence but inner freedom. Hind Swaraj (1909): critique of modern civilization.",
        "what_it_changes": "Shows that resistance can be nonviolent without being passive.",
        "what_it_does_not_mean": "NOT 'all resistance should be nonviolent'; NOT passivity; NOT 'Gandhi as saint'",
        "translation_to_MILK": "resistance without invasion; refusal without violence; swaraj as self-modulation",
        "translation_limits": "Gandhi's context is specific; not all colonial situations are equivalent",
    },
    "person:freud": {
        "canonical_name": "Sigmund Freud",
        "roles": ["psychoanalyst", "psychologist"],
        "source_pointer": "source:freud:civilization_and_its_discontents",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "unconscious / narcissism of small differences / civilization and discontent",
        "extended_definition": "Narcissism of small differences (1917): communities differentiate themselves from nearly identical neighbors through minor distinctions, producing hostility. Civilization and Its Discontents (1930): civilization requires repression that produces discontent.",
        "what_it_changes": "Shows that identity is not only positive but defined by tiny differences.",
        "what_it_does_not_mean": "NOT diagnostic mechanism; NOT clinical tool in MILK; NOT 'all difference is narcissism'",
        "translation_to_MILK": "small territorial differences as identity markers; METHOD_TRANSLATION only",
        "translation_limits": "Freud is a contested theoretical lens, NEVER a diagnostic instrument in CANooDlE",
        "non_diagnostic": True,
    },
    "person:rene_girard": {
        "canonical_name": "René Girard",
        "roles": ["literary theorist", "anthropological philosopher"],
        "source_pointer": "source:girard:violence_and_the_sacred",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "mimetic desire / scapegoat mechanism / violence and the sacred",
        "extended_definition": "Mimetic desire: we desire what others desire. Scapegoat mechanism: communities channel violence onto a victim to maintain cohesion. Violence and the Sacred: the sacred as regulated violence.",
        "what_it_changes": "Shows that desire is relational, not individual; violence is communal, not only personal.",
        "what_it_does_not_mean": "NOT diagnostic; NOT 'all desire is imitation'; NOT 'scapegoating is universal'",
        "translation_to_MILK": "mimetic desire in territorial taste; scapegoat mechanism in community exclusion",
        "translation_limits": "Girard is a contested theoretical lens, NEVER diagnostic in CANooDlE",
        "non_diagnostic": True,
    },
    "person:jacques_lacan": {
        "canonical_name": "Jacques Lacan",
        "roles": ["psychoanalyst"],
        "source_pointer": "source:lacan:ecrits",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "mirror stage / symbolic order / the real / desire as lack",
        "extended_definition": "Mirror stage: the ego is constituted through misrecognition. The symbolic: language and law structure subjectivity. The real: what resists symbolization. Desire as lack: desire is structured by the desire of the Other.",
        "what_it_changes": "Shows that subjectivity is structured by language and lack, not self-presence.",
        "what_it_does_not_mean": "NOT diagnostic; NOT clinical tool in CANooDlE; NOT 'Lacan explains everything'",
        "translation_to_MILK": "desire structured by the other; language as constitutive; METHOD_TRANSLATION only",
        "translation_limits": "Lacan is a contested theoretical lens, NEVER diagnostic in CANooDlE",
        "non_diagnostic": True,
    },
    "person:emma_goldman": {
        "canonical_name": "Emma Goldman",
        "roles": ["anarchist", "writer", "political activist"],
        "source_pointer": "source:goldman:anarchism_and_essays",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "creative disobedience / mutual aid / anti-authoritarianism",
        "extended_definition": "Goldman (1869-1940): argued that social revolution requires not only political change but the transformation of daily life. Creative disobedience: refusing the given order as a creative act. Mutual aid: solidarity without hierarchy.",
        "what_it_changes": "Reframes disobedience as creative, not merely destructive.",
        "what_it_does_not_mean": "NOT 'all authority is bad'; NOT romantic violence; NOT generic anarchism",
        "translation_to_MILK": "creative disobedience as curatorial practice; mutual aid as solidarity without invasion",
        "translation_limits": "Goldman's anarchism is specific; not all refusal is anarchist",
    },
    "person:stuart_hall": {
        "canonical_name": "Stuart Hall",
        "roles": ["cultural theorist", "sociologist"],
        "source_pointer": "source:hall:encoding_decoding",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "encoding/decoding / identity as negotiation / diaspora",
        "extended_definition": "Encoding/decoding: meaning is negotiated, not simply transmitted. Identity: not fixed but negotiated through representation. Diaspora: identity in displacement, not in origin.",
        "what_it_changes": "Shows that meaning is negotiated, not imposed; identity is process, not substance.",
        "what_it_does_not_mean": "NOT 'meaning is arbitrary'; NOT identity as computable; NOT 'all culture is diaspora'",
        "translation_to_MILK": "territorial meaning as negotiated; identity as process, not classification",
        "translation_limits": "Hall's cultural studies tradition is specific; not all meaning is negotiated equally",
    },
    "person:judith_butler": {
        "canonical_name": "Judith Butler",
        "roles": ["philosopher", "gender theorist"],
        "source_pointer": "source:butler:gender_trouble",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "performativity / gender as performance / precarity",
        "extended_definition": "Gender Trouble (1990): gender is performatively constituted, not expressive of a prior essence. Precarity: the differential distribution of vulnerability. Performativity is not voluntary performance but repeated citational practice.",
        "what_it_changes": "Shows that gender is constituted through practice, not biology.",
        "what_it_does_not_mean": "NOT 'gender is just a choice'; NOT identity as computable; NOT 'everything is performance'",
        "translation_to_MILK": "identity as performed, not classified; precarity as differential vulnerability",
        "translation_limits": "Butler's performativity is citational, not voluntary; must not be reduced",
    },
    "person:carol_gilligan": {
        "canonical_name": "Carol Gilligan",
        "roles": ["psychologist", "ethicist"],
        "source_pointer": "source:gilligan:in_a_different_voice",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "ethics of care / different voice / relational morality",
        "extended_definition": "In a Different Voice (1982): challenged Kohlberg's universalist moral development. Ethics of care: morality grounded in relationships and care, not abstract principles. Different voice: not gender-essentialist but challenges universalist assumptions.",
        "what_it_changes": "Shows that moral reasoning is relational, not only abstract.",
        "what_it_does_not_mean": "NOT 'women think differently'; NOT gender essentialism; NOT anti-principle",
        "translation_to_MILK": "care as relational practice, not as scoring people",
        "translation_limits": "Gilligan's work has been criticized for gender essentialism; must be used carefully",
    },
    "person:nel_noddings": {
        "canonical_name": "Nel Noddings",
        "roles": ["philosopher of education"],
        "source_pointer": "source:noddings:caring",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "caring / relational ethics / receptivity",
        "extended_definition": "Caring (1984): ethics rooted in receptivity and relation. The one-caring and the cared-for. Not sentimentality but an ethical relation of attention.",
        "what_it_changes": "Reframes ethics as relational attention, not abstract duty.",
        "what_it_does_not_mean": "NOT 'care is always good'; NOT sentimentality; NOT 'women are naturally caring'",
        "translation_to_MILK": "care as attention without invasion; receptivity without classification",
        "translation_limits": "Noddings' ethics is relational, not universalist",
    },
    "person:joan_tronto": {
        "canonical_name": "Joan Tronto",
        "roles": ["political theorist"],
        "source_pointer": "source:tronto:moral_boundaries",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "care as political practice / democratic care / privilege of care",
        "extended_definition": "Moral Boundaries (1993): care is political, not private. Democratic care: care distributed through democratic process. The privilege of not caring: those in power can delegate care to others.",
        "what_it_changes": "Shows that care is a political practice, not a private virtue.",
        "what_it_does_not_mean": "NOT 'care is only political'; NOT sentimentality; NOT 'all care is good'",
        "translation_to_MILK": "care as political attention to territory; who cares and who doesn't",
        "translation_limits": "Tronto's framework is political; must not be depoliticized",
    },
    "person:frantz_fanon": {
        "canonical_name": "Frantz Fanon",
        "roles": ["psychiatrist", "philosopher", "anti-colonial thinker"],
        "source_pointer": "source:fanon:wretched_of_the_earth",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "colonial psychology / violence of decolonization / the wretched of the earth",
        "extended_definition": "The Wretched of the Earth (1961): colonialism produces psychological damage. Decolonization is necessarily violent because colonialism is violence. The colonized subject's body is marked by colonial relations.",
        "what_it_changes": "Shows that colonialism is psychological, not only economic.",
        "what_it_does_not_mean": "NOT 'violence is always good'; NOT romantic violence; NOT diagnosis of individuals",
        "translation_to_MILK": "colonial marking of territorial bodies; decolonization as counter-conduct",
        "translation_limits": "Fanon's context is specific (Algeria, France); must not be universalized without care",
        "cultural_specificity": "Algerian colonial context; North African; French colonial psychiatry",
    },
    "person:bell_hooks": {
        "canonical_name": "bell hooks",
        "roles": ["feminist theorist", "cultural critic"],
        "source_pointer": "source:hooks:feminist_theory",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "intersectionality / love as practice / margin as site of resistance",
        "extended_definition": "Feminist Theory: From Margin to Center (1984): feminism must center race and class. Love as practice: not sentimentality but active commitment. The margin as a site of radical possibility, not only exclusion.",
        "what_it_changes": "Shows that oppression is intersectional, not additive; margins are sites of knowledge.",
        "what_it_does_not_mean": "NOT 'identity is intersection'; NOT generic 'love'; NOT margin as romantic",
        "translation_to_MILK": "margin as site of knowledge; love as practice without invasion",
        "translation_limits": "hooks' lowercase name is intentional; must preserve",
    },
    "person:margaret_mead": {
        "canonical_name": "Margaret Mead",
        "roles": ["anthropologist"],
        "source_pointer": "source:mead:coming_of_age_in_samoa",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "cultural relativity / adolescence / gender roles",
        "extended_definition": "Coming of Age in Samoa (1928): adolescence is not universally turbulent; it is shaped by culture. Gender roles are culturally variable, not biologically fixed. Criticized (Freeman, 1983) for methodological issues; the critique itself is contested.",
        "what_it_changes": "Shows that what seems natural is often cultural.",
        "what_it_does_not_mean": "NOT 'all behavior is cultural'; NOT uncritical relativism; NOT free from controversy",
        "translation_to_MILK": "what seems natural in territorial life may be cultural; defamiliarization",
        "translation_limits": "Mead's Samoa work is contested; must cite controversy",
    },
    "person:miranda_fricker": {
        "canonical_name": "Miranda Fricker",
        "roles": ["philosopher"],
        "source_pointer": "source:fricker:epistemic_injustice",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "epistemic injustice / testimonial injustice / hermeneutical injustice",
        "extended_definition": "Epistemic Injustice (2007): testimonial injustice: a speaker's credibility is reduced due to identity prejudice. Hermeneutical injustice: a gap in collective interpretive resources puts someone at an unfair disadvantage in making sense of their experience.",
        "what_it_changes": "Shows that injustice operates at the level of knowledge and interpretation.",
        "what_it_does_not_mean": "NOT 'all disagreement is epistemic injustice'; NOT diagnosis of individuals",
        "translation_to_MILK": "whose testimony is not heard; whose experience has no interpretive resources; epistemic gap",
        "translation_limits": "Fricker's framework is philosophical; must not be used to diagnose individuals",
    },
    "person:max_gluckman": {
        "canonical_name": "Max Gluckman",
        "roles": ["social anthropologist"],
        "source_pointer": "source:gluckman:custom_and_conflict",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "rituals of rebellion / custom and conflict / situational analysis",
        "extended_definition": "Rituals of rebellion (1954): rituals that temporarily invert hierarchies actually maintain social order. Custom and Conflict (1955): conflict is not always pathological; it can be constitutive. The Manchester School: situational analysis.",
        "what_it_changes": "Shows that conflict can be constitutive, not only destructive.",
        "what_it_does_not_mean": "NOT 'all conflict is good'; NOT 'rituals are always conservative'; NOT romantic rebellion",
        "translation_to_MILK": "rituals of rebellion in curatorial practice; conflict as constitutive",
        "translation_limits": "Gluckman's Manchester School is specific; not all conflict is constitutive",
    },
    "person:erving_goffman": {
        "canonical_name": "Erving Goffman",
        "roles": ["sociologist"],
        "source_pointer": "source:goffman:presentation_of_self",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "presentation of self / dramaturgy / stigma / total institutions",
        "extended_definition": "The Presentation of Self in Everyday Life (1959): social life as theatrical performance. Front stage/back stage. Stigma (1963): the management of spoiled identity. Total institutions: institutions that control all aspects of life.",
        "what_it_changes": "Shows that social life is performative; identity is managed, not given.",
        "what_it_does_not_mean": "NOT 'everyone is faking'; NOT cynicism; NOT 'identity is just performance'",
        "translation_to_MILK": "front/back stage in curatorial presence; stigma as imposed legibility",
        "translation_limits": "Goffman's dramaturgy is analytical, not ontological",
    },
    "person:george_herbert_mead": {
        "canonical_name": "George Herbert Mead",
        "roles": ["philosopher", "sociologist"],
        "source_pointer": "source:mead:mind_self_society",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "symbolic interactionism / self as social / I and me",
        "extended_definition": "Mind, Self, and Society (1934): the self is constituted through social interaction. The 'I' is the spontaneous response; the 'me' is the internalized other. Symbolic interactionism: meaning emerges in interaction.",
        "what_it_changes": "Shows that the self is social, not pre-given.",
        "what_it_does_not_mean": "NOT 'identity is just social'; NOT reduction to interaction; NOT 'self is only performance'",
        "translation_to_MILK": "self-modulation as relation between I and me; meaning emerges in interaction",
        "translation_limits": "Mead's framework is pragmatic; must not be ontologized",
    },
    "person:clarice_lispector": {
        "canonical_name": "Clarice Lispector",
        "roles": ["writer", "philosopher of literature"],
        "source_pointer": "source:clarice:hora_estrela",
        "epistemic_status": "SOURCE",
        "conceptual_nucleus": "pre-conceptual event / strangeness / thing / language rupture",
        "extended_definition": "A Hora da Estrela (1977): literature as pre-conceptual event, not representation. Strangeness: the unfamiliar within the familiar. The thing: reality before language. Language rupture: when language fails to capture experience.",
        "what_it_changes": "Shows that literature can approach experience before conceptualization.",
        "what_it_does_not_mean": "NOT 'epiphany' (reduction); NOT mysticism; NOT 'literature is beyond thought'",
        "translation_to_MILK": "pre-conceptual territorial experience; strangeness as method; METHOD_TRANSLATION",
        "translation_limits": "Clarice is literature, not theory; METHOD_TRANSLATION only when supported by the work",
    },
}


def load_canoodle_delta(graph) -> dict:
    """Load the CANooDlE micelial delta into the existing hypergraph.

    Adds:
      - New person nodes with depth profiles
      - Resistance/creation nodes
      - Micelial relation edges
      - Extended COSMICOXES grammar
      - Constitutional invariants
    """
    from .hypergraph import HyperNode, HyperEdge
    from .method_repertoire import _addendum_node
    from .depth_profile import cosmicoxes_projection_for

    new_persons = 0
    new_concepts = 0
    new_edges = 0
    profiles_added = 0

    # Add new person nodes
    for person_id, info in NEW_REFERENCES.items():
        if graph.get_node(person_id) is None:
            entry = (
                person_id, info["canonical_name"], "PERSON",
                info["conceptual_nucleus"], "text",
                info["source_pointer"], info["epistemic_status"],
                info["canonical_name"],
                {"aliases": info.get("aliases", []),
                 "roles": info.get("roles", []),
                 "cultural_specificity": info.get("cultural_specificity", ""),
                 "non_diagnostic": info.get("non_diagnostic", False)},
            )
            graph.add_node(_addendum_node(entry))
            new_persons += 1

            # Create depth profile
            dp = ConceptDepthProfile(
                source_pointer=info["source_pointer"],
                source_type="PHILOSOPHY",
                author=info["canonical_name"],
                work=info.get("source_pointer", "").replace("source:", ""),
                epistemic_status=info["epistemic_status"],
                conceptual_nucleus=info["conceptual_nucleus"],
                extended_definition=info["extended_definition"],
                what_it_changes=info.get("what_it_changes", "N/A"),
                what_it_is_not=info.get("what_it_does_not_mean", "N/A"),
                human_validation_required=info.get("human_validation_required", False),
            )
            dp.cosmicoxes_projection = cosmicoxes_projection_for(info["conceptual_nucleus"])
            DEPTH_PROFILES[person_id] = dp
            profiles_added += 1

            # Attach to node
            node = graph.get_node(person_id)
            if node:
                node.metadata["depth_profile"] = dp.to_dict()

    # Add resistance/creation nodes
    for node_id, label, ntype, operation, modality, source_ptr, epistemic, author in RESISTANCE_CREATION_NODES:
        if graph.get_node(node_id) is None:
            entry = (node_id, label, ntype, operation, modality, source_ptr, epistemic, author, {})
            graph.add_node(_addendum_node(entry))
            new_concepts += 1

    # Add micelial edges (key cross-references)
    micelial_edges = [
        # Arendt -> public space / action
        ("person:hannah_arendt", "RELATED_TO", "device:mapping_territorial",
         0.6, "Arendt's public realm resonates with territorial mapping as public action"),
        # Bauman -> territory as liquid
        ("person:zygmunt_bauman", "RELATED_TO", "method:toponymy",
         0.5, "Bauman's liquid modernity: territorial identity is not fixed"),
        # Mbembe -> coloniality of absence
        ("person:achille_mbembe", "RELATED_TO", "concept:silence",
         0.5, "Mbembe's necropolitics: whose absence/death is made invisible"),
        # Fanon -> colonial marking of body
        ("person:frantz_fanon", "RELATED_TO", "method:boal",
         0.5, "Fanon's colonial body resonates with Boal's spect-actor body"),
        # Goldman -> creative disobedience <-> clown
        ("person:emma_goldman", "RELATED_TO", "clown:birth",
         0.5, "Goldman's creative disobedience resonates with clown failure as creation"),
        # Freud -> small differences <-> toponymy
        ("person:freud", "RELATED_TO", "method:toponymy",
         0.4, "narcissism of small differences: territorial identity through tiny distinctions (METHOD_TRANSLATION, non-diagnostic)"),
        # Girard -> mimetic desire <-> curatorial
        ("person:rene_girard", "RELATED_TO", "method:boal",
         0.4, "mimetic desire in collective performance (METHOD_TRANSLATION, non-diagnostic)"),
        # Lacan -> desire structured by the other
        ("person:jacques_lacan", "RELATED_TO", "temporal:protention",
         0.3, "Lacan's desire as lack resonates with protention as openness (METHOD_TRANSLATION, non-diagnostic)"),
        # Butler -> performativity <-> identity_revisable
        ("person:judith_butler", "RELATED_TO", "zine:identity_revisable",
         0.6, "Butler's performativity: identity is performed, not fixed"),
        # Hall -> encoding/decoding <-> territorial reading
        ("person:stuart_hall", "RELATED_TO", "method:freire",
         0.5, "Hall's negotiated meaning resonates with Freire's reading the world"),
        # Fricker -> epistemic injustice <-> research gap
        ("person:miranda_fricker", "RELATED_TO", "concept:silence",
         0.5, "Fricker's hermeneutical injustice: silence as missing interpretive resources"),
        # Gilligan/Noddings/Tronto -> care
        ("person:carol_gilligan", "RELATED_TO", "resist:care",
         0.7, "Gilligan's ethics of care as relational morality"),
        ("person:nel_noddings", "RELATED_TO", "resist:care",
         0.7, "Noddings' caring as relational attention"),
        ("person:joan_tronto", "RELATED_TO", "resist:care",
         0.7, "Tronto's care as political practice"),
        # Goffman -> presentation of self <-> CANooDlE self-modulation
        ("person:erving_goffman", "RELATED_TO", "resist:play",
         0.4, "Goffman's dramaturgy: front/back stage as curatorial presence"),
        # Mead -> self as social <-> CANooDlE
        ("person:george_herbert_mead", "RELATED_TO", "resist:play",
         0.4, "Mead's I and me: self-modulation as internal relation"),
        # Clarice -> pre-conceptual <-> scene_fulgor
        ("person:clarice_lispector", "RELATED_TO", "resist:scene_fulgor",
         0.6, "Clarice's pre-conceptual event resonates with Llansol's cena-fulgor"),
        # Gluckman -> rituals of rebellion <-> carnival
        ("person:max_gluckman", "RELATED_TO", "resist:carnival",
         0.6, "Gluckman's rituals of rebellion: Bakhtin's carnival as constitutive conflict"),
        # Weber -> bureaucracy <-> delay
        ("person:max_weber", "RELATED_TO", "person:jay_wright_forrester",
         0.5, "Weber's rationalization resonates with Forrester's bureaucratic delay"),
        # Miner -> defamiliarization <-> observer
        ("person:horace_miner", "RELATED_TO", "person:heinz_von_foerster",
         0.5, "Miner's defamiliarization: the observer's own culture is not transparent"),
        # hooks -> margin as knowledge <-> research gap
        ("person:bell_hooks", "RELATED_TO", "concept:silence",
         0.4, "hooks: margin as site of radical possibility, not only exclusion"),
        # Laraia -> culture as relational system
        ("person:roque_laraia", "RELATED_TO", "method:toponymy",
         0.5, "Laraia: culture as system of shared meanings about place"),
        # Mosé -> philosophy of the city
        ("person:viviane_mose", "RELATED_TO", "device:mapping_territorial",
         0.5, "Mose: philosophy inhabiting the city, not merely describing it"),
        # Ibn Rushd -> multiple registers of truth
        ("person:ibn_rushd", "RELATED_TO", "person:edgar_morin",
         0.4, "Ibn Rushd's harmony of registers resonates with Morin's dialogical coexistence"),
        # Tupac Amaru II -> resistance
        ("person:tupac_amaru_ii", "RELATED_TO", "resist:counter_conduct",
         0.6, "Tupac Amaru II as colonial counter-conduct (distinguished from Tupac Amaru I)"),
        # Gandhi -> nonviolent resistance
        ("person:gandhi", "RELATED_TO", "resist:refusal",
         0.6, "Gandhi's satyagraha: refusal without violence; swaraj as self-modulation"),
        # Mbembe -> coloniality
        ("person:achille_mbembe", "RELATED_TO", "person:michel_foucault",
         0.5, "Mbembe extends Foucault's biopolitics to necropolitics"),
        # Fanon -> colonial psychology
        ("person:frantz_fanon", "RELATED_TO", "person:achille_mbembe",
         0.5, "Fanon and Mbembe: colonial violence and its afterlives"),
    ]

    for src, etype, tgt, conf, desc in micelial_edges:
        if graph.get_node(src) and graph.get_node(tgt):
            edge_id = f"micelial:{src}->{tgt}"
            graph.add_edge(HyperEdge(
                id=edge_id, source=src, edge_type="RELATED_TO",
                target=tgt, confidence=conf,
                validation_state="validated",
                source_ref=_ADDENDUM,
                metadata={
                    "micelial_relation": desc,
                    "non_equivalence": "METHOD_TRANSLATION or structural resonance; NOT equivalence",
                    "lexical_overlap": 0,
                    "epistemic_status": "METHOD_TRANSLATION",
                }))
            new_edges += 1

    return {
        "new_persons": new_persons,
        "new_concepts": new_concepts,
        "new_edges": new_edges,
        "profiles_added": profiles_added,
        "total_new_references": len(NEW_REFERENCES),
        "resistance_nodes": len(RESISTANCE_CREATION_NODES),
        "micelial_edges": len(micelial_edges),
    }
