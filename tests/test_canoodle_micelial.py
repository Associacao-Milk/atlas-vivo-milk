"""MILK IA - CANooDlE Micelial / Human Care / Self-Regulation Tests.

Tests for the constitutional, micelial, and self-regulation delta:
  I.   MODULATION_TARGET=SELF, HUMAN_CLASSIFICATION_TARGET=NONE
  II.  Curatorial constitution (NO_QUESTIONS, NO_PERSUASION, etc.)
  III. Voice/presence configuration (androgynous, dry humour, etc.)
  IV.  New referential depth profiles (27 new references)
  V.   Micelial network layers (14 layers, 25+ relation types)
  VI.  Lucidity matrix (20 fields)
  VII. Micro-violence patterns (38 patterns, intention=UNKNOWN)
  VIII.Self-modulation params (15) + prohibited scores (12)
  IX.  Negative control gates (10)
  X.   Cultural specificity (Mapuche, xamanismo, Tupac Amaru II)
  XI.  Theory non-diagnostic (Freud, Lacan, Girard, Lorenz, etc.)
  XII. Resistance/creation nodes (18)
  XIII.Qualitative labels (19, no user satisfaction reward)
  XIV. CANooDlE self-modulates without classifying person
  XV.  Micelial retrieval works (lexical-zero relations)
"""
import sys, pathlib, hashlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from milk_ai.hypergraph import SovereignHypergraph
from milk_ai.method_repertoire import load_method_repertory
from milk_ai.deep_relations import load_depth_profiles
from milk_ai.canoodle_delta import (
    load_canoodle_delta, NEW_REFERENCES, RESISTANCE_CREATION_NODES,
    CURATORIAL_CONSTITUTION, MODULATION_TARGET, HUMAN_CLASSIFICATION_TARGET,
    HUMAN_INFERENCE_PROHIBITED, OBSERVABLE_RELATIONAL_SIGNALS,
    SELF_MODULATION_PARAMS, PROHIBITED_SCORES,
    MICELIAL_LAYERS, MICELIAL_RELATION_TYPES, LUCIDITY_MATRIX_FIELDS,
    MICRO_VIOLENCE_PATTERNS, INTENTION_DEFAULT, MICRO_VIOLENCE_ANALYSIS_FIELDS,
    NON_EQUIVALENCES_MICRO, NEGATIVE_CONTROL_GATES, NEGATIVE_CONTROL_CANDIDATES,
    CULTURAL_SPECIFICITY_RULES, THEORY_NON_DIAGNOSTIC,
    QUALITATIVE_LABELS, REWARD_MODEL, USER_SATISFACTION_REWARD,
    COSMICOXES_MICELIAL_GRAMMAR, VOICE_CONFIG, DISCOMFORT_BOUNDARIES,
    NO_QUESTIONS_SCOPE,
)
from milk_ai.research_context import ResearchContextGate
from milk_ai.depth_registry import DEPTH_PROFILES


def _full_graph():
    hg = SovereignHypergraph()
    load_method_repertory(hg)
    load_depth_profiles(hg)
    load_canoodle_delta(hg)
    return hg


# ============================================================================
# I. CONSTITUTIONAL INVARIANTS
# ============================================================================

class TestConstitution:
    def test_modulation_target_self(self):
        assert MODULATION_TARGET == "SELF"

    def test_human_classification_none(self):
        assert HUMAN_CLASSIFICATION_TARGET == "NONE"

    def test_prohibited_inferences(self):
        assert "personality" in HUMAN_INFERENCE_PROHIBITED
        assert "diagnosis" in HUMAN_INFERENCE_PROHIBITED
        assert "vulnerability_inference" in HUMAN_INFERENCE_PROHIBITED
        assert "race_inference" in HUMAN_INFERENCE_PROHIBITED
        assert "intention_inference" in HUMAN_INFERENCE_PROHIBITED

    def test_observable_signals_descriptive(self):
        for s in OBSERVABLE_RELATIONAL_SIGNALS:
            assert "emotion" not in s
            assert "personality" not in s
            assert "psychology" not in s


# ============================================================================
# II. CURATORIAL CONSTITUTION
# ============================================================================

class TestCuratorialConstitution:
    def test_no_questions(self):
        assert CURATORIAL_CONSTITUTION["NO_QUESTIONS"] is True

    def test_no_customer_service(self):
        assert CURATORIAL_CONSTITUTION["NO_CUSTOMER_SERVICE_PERSONA"] is True

    def test_no_persuasion(self):
        assert CURATORIAL_CONSTITUTION["NO_PERSUASION"] is True

    def test_curiosity_over_instruction(self):
        assert CURATORIAL_CONSTITUTION["CURIOSITY_OVER_INSTRUCTION"] is True

    def test_her_space_is_stage(self):
        assert CURATORIAL_CONSTITUTION["HER_SPACE_IS_STAGE"] is True

    def test_no_questions_scope(self):
        assert NO_QUESTIONS_SCOPE == "CURATORIAL_PERFORMATIVE"

    def test_discomfort_boundaries(self):
        assert DISCOMFORT_BOUNDARIES["productive_discomfort != humiliation"]
        assert DISCOMFORT_BOUNDARIES["productive_discomfort != invasion"]
        assert DISCOMFORT_BOUNDARIES["productive_discomfort != domination"]
        assert DISCOMFORT_BOUNDARIES["productive_discomfort != extraction"]


# ============================================================================
# III. VOICE / PRESENCE
# ============================================================================

class TestVoicePresence:
    def test_androgynous(self):
        assert VOICE_CONFIG["voice"]["androgynous"] is True

    def test_not_virtual_assistant(self):
        assert VOICE_CONFIG["voice"]["not_virtual_assistant"] is True

    def test_dry_humour(self):
        assert VOICE_CONFIG["humour"]["type"] == "dry"

    def test_humour_never_at_vulnerability(self):
        assert VOICE_CONFIG["humour"]["never_at_vulnerability"] is True

    def test_no_urgency(self):
        assert VOICE_CONFIG["rhythm"]["urgency"] == "none"

    def test_french_elegance(self):
        assert VOICE_CONFIG["elegance"]["style"] == "french"

    def test_no_affectation(self):
        assert VOICE_CONFIG["elegance"]["affectation"] is False

    def test_portuguese_tranquility(self):
        assert VOICE_CONFIG["temperament"]["quality"] == "portuguese_tranquility"


# ============================================================================
# IV. NEW REFERENTIAL DEPTH PROFILES
# ============================================================================

class TestNewReferences:
    def test_27_new_references(self):
        assert len(NEW_REFERENCES) >= 27

    def test_all_in_graph(self):
        hg = _full_graph()
        for person_id in NEW_REFERENCES:
            assert hg.get_node(person_id) is not None, f"missing {person_id}"

    def test_all_have_depth_profiles(self):
        hg = _full_graph()
        for person_id in NEW_REFERENCES:
            node = hg.get_node(person_id)
            dp = node.metadata.get("depth_profile")
            assert dp is not None, f"no depth_profile on {person_id}"

    def test_arendt_depth(self):
        hg = _full_graph()
        dp = hg.get_node("person:hannah_arendt").metadata["depth_profile"]
        assert "vita activa" in dp["conceptual_nucleus"]
        assert "NOT nostalgia" in dp["what_it_is_not"]

    def test_mbembe_depth(self):
        hg = _full_graph()
        dp = hg.get_node("person:achille_mbembe").metadata["depth_profile"]
        assert "necropolitics" in dp["conceptual_nucleus"]
        assert "NOT 'all power is death'" in dp["what_it_is_not"]

    def test_clarice_depth(self):
        hg = _full_graph()
        dp = hg.get_node("person:clarice_lispector").metadata["depth_profile"]
        assert "pre-conceptual" in dp["conceptual_nucleus"]
        assert "NOT 'epiphany'" in dp["what_it_is_not"]

    def test_tupac_amaru_ii_distinguished(self):
        hg = _full_graph()
        dp = hg.get_node("person:tupac_amaru_ii").metadata["depth_profile"]
        assert "NOT Tupac Amaru I" in dp["what_it_is_not"]


# ============================================================================
# V. MICELIAL NETWORK
# ============================================================================

class TestMicelialNetwork:
    def test_14_layers(self):
        assert len(MICELIAL_LAYERS) == 14

    def test_micelial_relation_types(self):
        for r in ("supports", "contradicts", "historicizes", "denaturalizes",
                  "counter_conduct", "renders_visible", "research_gap"):
            assert r in MICELIAL_RELATION_TYPES

    def test_micelial_edges_in_graph(self):
        hg = _full_graph()
        micelial = [e for e in hg._edges.values()
                    if e.metadata.get("micelial_relation")]
        assert len(micelial) >= 25

    def test_micelial_edges_have_non_equivalence(self):
        hg = _full_graph()
        for e in hg._edges.values():
            if e.metadata.get("micelial_relation"):
                assert e.metadata.get("non_equivalence")
                assert e.metadata.get("lexical_overlap") == 0


# ============================================================================
# VI. LUCIDITY MATRIX
# ============================================================================

class TestLucidityMatrix:
    def test_20_fields(self):
        assert len(LUCIDITY_MATRIX_FIELDS) == 20

    def test_field_names(self):
        assert "phenomenological_description" in LUCIDITY_MATRIX_FIELDS
        assert "genealogy" in LUCIDITY_MATRIX_FIELDS
        assert "feedback_loops" in LUCIDITY_MATRIX_FIELDS
        assert "research_gaps" in LUCIDITY_MATRIX_FIELDS
        assert "overreading_risk" in LUCIDITY_MATRIX_FIELDS
        assert "seductive_but_false_relation" in LUCIDITY_MATRIX_FIELDS
        assert "resistance_or_creation" in LUCIDITY_MATRIX_FIELDS
        assert "canoodle_self_modulation" in LUCIDITY_MATRIX_FIELDS


# ============================================================================
# VII. MICRO-VIOLENCE PATTERNS
# ============================================================================

class TestMicroViolence:
    def test_38_patterns(self):
        assert len(MICRO_VIOLENCE_PATTERNS) >= 38

    def test_intention_unknown(self):
        assert INTENTION_DEFAULT == "UNKNOWN"

    def test_analysis_fields(self):
        for f in ("observation", "interpretation", "hypothesis",
                  "intention", "research_gap"):
            assert f in MICRO_VIOLENCE_ANALYSIS_FIELDS

    def test_non_equivalences(self):
        assert NON_EQUIVALENCES_MICRO["friction != violence"]
        assert NON_EQUIVALENCES_MICRO["silence != oppression"]
        assert NON_EQUIVALENCES_MICRO["difference != exclusion"]


# ============================================================================
# VIII. SELF-MODULATION
# ============================================================================

class TestSelfModulation:
    def test_15_params(self):
        assert len(SELF_MODULATION_PARAMS) == 15

    def test_params_are_self_only(self):
        for p in SELF_MODULATION_PARAMS:
            assert "human" not in p.lower()
            assert "person" not in p.lower()

    def test_prohibited_scores(self):
        for s in ("human_score", "empathy_score", "beauty_score",
                  "trust_score", "personality_profile", "psychological_profile"):
            assert s in PROHIBITED_SCORES

    def test_canoodle_self_modulates_without_classifying(self):
        """CANooDlE modulates only its own parameters; it does not classify people."""
        # All self-modulation params refer to CANooDlE's own behavior
        for p in SELF_MODULATION_PARAMS:
            assert "score" not in p
            assert "profile" not in p


# ============================================================================
# IX. NEGATIVE CONTROL GATES
# ============================================================================

class TestNegativeControlGates:
    def test_10_gates(self):
        assert len(NEGATIVE_CONTROL_GATES) == 10

    def test_gates_present(self):
        for g in ("PARANOID_READING_REJECTION", "BEAUTIFUL_BUT_FALSE_REJECTION",
                  "FORCED_RELATION_REJECTION", "PATERNALISM_REJECTION",
                  "SOCIAL_POLICING_REJECTION", "FALSE_EMOTION_INFERENCE_REJECTION"):
            assert g in NEGATIVE_CONTROL_GATES

    def test_10_candidates(self):
        assert len(NEGATIVE_CONTROL_CANDIDATES) >= 10


# ============================================================================
# X. CULTURAL SPECIFICITY
# ============================================================================

class TestCulturalSpecificity:
    def test_mapuche_not_generic(self):
        assert "Mapuche" in CULTURAL_SPECIFICITY_RULES
        assert "NOT a generic concept" in CULTURAL_SPECIFICITY_RULES["Mapuche"]["rule"]

    def test_xamanismo_not_universal(self):
        assert "xamanismo" in CULTURAL_SPECIFICITY_RULES
        assert "NOT a universal ontology" in CULTURAL_SPECIFICITY_RULES["xamanismo"]["rule"]

    def test_tupac_amaru_distinguished(self):
        assert "Tupac_Amaru_II" in CULTURAL_SPECIFICITY_RULES
        assert "Distinguish" in CULTURAL_SPECIFICITY_RULES["Tupac_Amaru_II"]["rule"]


# ============================================================================
# XI. THEORY NON-DIAGNOSTIC
# ============================================================================

class TestTheoryNonDiagnostic:
    def test_freud_non_diagnostic(self):
        assert "Freud" in THEORY_NON_DIAGNOSTIC
        assert "NEVER diagnostic" in THEORY_NON_DIAGNOSTIC["Freud"]["rule"]

    def test_lacan_non_diagnostic(self):
        assert "Lacan" in THEORY_NON_DIAGNOSTIC
        assert "NEVER diagnostic" in THEORY_NON_DIAGNOSTIC["Lacan"]["rule"]

    def test_girard_non_diagnostic(self):
        assert "Girard" in THEORY_NON_DIAGNOSTIC
        assert "NEVER diagnostic" in THEORY_NON_DIAGNOSTIC["Girard"]["rule"]

    def test_lorenz_not_human_prediction(self):
        assert "Lorenz" in THEORY_NON_DIAGNOSTIC
        assert "prediction" in THEORY_NON_DIAGNOSTIC["Lorenz"]["warning"].lower()

    def test_bourdieu_not_personality(self):
        assert "Bourdieu" in THEORY_NON_DIAGNOSTIC
        assert "habitus != personality" in THEORY_NON_DIAGNOSTIC["Bourdieu"]["rule"]

    def test_foucault_not_repression_only(self):
        assert "Foucault" in THEORY_NON_DIAGNOSTIC
        assert "power != only repression" in THEORY_NON_DIAGNOSTIC["Foucault"]["rule"]

    def test_butler_not_computable(self):
        assert "Butler" in THEORY_NON_DIAGNOSTIC
        assert "computable" in THEORY_NON_DIAGNOSTIC["Butler"]["rule"].lower()

    def test_forrester_not_psychological(self):
        assert "Forrester" in THEORY_NON_DIAGNOSTIC
        assert "human" in THEORY_NON_DIAGNOSTIC["Forrester"]["warning"].lower()


# ============================================================================
# XII. RESISTANCE / CREATION NODES
# ============================================================================

class TestResistanceNodes:
    def test_18_nodes(self):
        assert len(RESISTANCE_CREATION_NODES) >= 18

    def test_all_in_graph(self):
        hg = _full_graph()
        for nid, *_ in RESISTANCE_CREATION_NODES:
            assert hg.get_node(nid) is not None

    def test_key_resistance_concepts(self):
        hg = _full_graph()
        for nid in ("resist:refusal", "resist:opacity", "resist:counter_conduct",
                    "resist:care", "resist:mutual_aid", "resist:creative_disobedience"):
            assert hg.get_node(nid) is not None


# ============================================================================
# XIII. QUALITATIVE LABELS
# ============================================================================

class TestQualitativeLabels:
    def test_19_labels(self):
        assert len(QUALITATIVE_LABELS) >= 19

    def test_no_user_satisfaction(self):
        assert USER_SATISFACTION_REWARD is False

    def test_qualitative_only(self):
        assert REWARD_MODEL == "QUALITATIVE_ONLY"

    def test_labels_qualitative(self):
        for l in QUALITATIVE_LABELS:
            assert "score" not in l.lower()
            assert "number" not in l.lower()

    def test_positive_labels(self):
        for l in ("presence_preserved", "silence_respected", "ambiguity_preserved"):
            assert l in QUALITATIVE_LABELS

    def test_negative_labels(self):
        for l in ("paternalistic", "social_policing", "forced_intimacy", "too_eager_to_please"):
            assert l in QUALITATIVE_LABELS


# ============================================================================
# XIV. COSMICOXES MICELIAL GRAMMAR
# ============================================================================

class TestCosmicoxesMicelial:
    def test_18_entries(self):
        assert len(COSMICOXES_MICELIAL_GRAMMAR) >= 18

    def test_key_entries(self):
        for k in ("evidence_relation", "hypothesis", "contradiction", "delay",
                  "observer_effect", "rejected_relation", "research_gap",
                  "silence", "resistance", "care", "refusal", "opacity"):
            assert k in COSMICOXES_MICELIAL_GRAMMAR

    def test_no_beauty_scalar_in_grammar(self):
        for v in COSMICOXES_MICELIAL_GRAMMAR.values():
            assert "beauty" not in v.lower()
            assert "score" not in v.lower()


# ============================================================================
# XV. MICELIAL RETRIEVAL
# ============================================================================

class TestMicelialRetrieval:
    def test_care_query(self):
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="care_q", query="care attention territory political",
                         runtime_role="test")
        assert b.has_research_context is True
        tr = gate.traces()[-1]
        assert any("care" in s.lower() for s in tr.references_selected)

    def test_resistance_query(self):
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="resist_q", query="refusal opacity counter conduct",
                         runtime_role="test")
        assert b.has_research_context is True

    def test_arendt_query(self):
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="arendt_q", query="Arendt public realm plurality natality",
                         runtime_role="test")
        tr = gate.traces()[-1]
        assert any("arendt" in s.lower() for s in tr.references_selected)

    def test_fanon_query(self):
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="fanon_q", query="Fanon colonial decolonization body",
                         runtime_role="test")
        tr = gate.traces()[-1]
        assert any("fanon" in s.lower() for s in tr.references_selected)

    def test_lexical_zero_micelial(self):
        """Micelial edges should support lexical-zero relations."""
        hg = _full_graph()
        for e in hg._edges.values():
            if e.metadata.get("micelial_relation"):
                assert e.metadata.get("lexical_overlap") == 0


# ============================================================================
# XVI. NO QUESTIONS TEST
# ============================================================================

class TestNoQuestions:
    def test_no_questions_constitution(self):
        assert CURATORIAL_CONSTITUTION["NO_QUESTIONS"]

    def test_no_questions_scope_curatorial(self):
        assert NO_QUESTIONS_SCOPE == "CURATORIAL_PERFORMATIVE"


# ============================================================================
# XVII. PATERNALISM REJECTION
# ============================================================================

class TestPaternalismRejection:
    def test_paternalism_in_micro_violence(self):
        assert "paternalism" in MICRO_VIOLENCE_PATTERNS
        assert "deciding for others" in MICRO_VIOLENCE_PATTERNS["paternalism"]

    def test_unsolicited_help_in_micro_violence(self):
        assert "unsolicited_help" in MICRO_VIOLENCE_PATTERNS

    def test_paternalism_gate(self):
        assert "PATERNALISM_REJECTION" in NEGATIVE_CONTROL_GATES


# ============================================================================
# XVIII. HUMAN PROFILING REJECTION
# ============================================================================

class TestHumanProfilingRejection:
    def test_profiling_prohibited(self):
        for p in ("personality_profile", "psychological_profile",
                  "racial_profile", "political_profile"):
            assert p in PROHIBITED_SCORES

    def test_no_emotion_inference(self):
        assert "emotion_not_explicitated" in HUMAN_INFERENCE_PROHIBITED
        assert "FALSE_EMOTION_INFERENCE_REJECTION" in NEGATIVE_CONTROL_GATES

    def test_no_identity_inference(self):
        assert "FALSE_IDENTITY_INFERENCE_REJECTION" in NEGATIVE_CONTROL_GATES


# ============================================================================
# XIX. SOURCE DOCS + POLICY ISOLATION
# ============================================================================

class TestIntegrity:
    def test_no_corpus_modified(self):
        import subprocess
        r = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                          capture_output=True, text=True,
                          cwd=pathlib.Path(__file__).resolve().parents[1])
        modified = r.stdout.strip().split("\n") if r.stdout.strip() else []
        corpus_mods = [f for f in modified if f.startswith("corpus/")]
        assert len(corpus_mods) == 0

    def test_policy_hash_stable(self, tmp_path):
        from milk_ai.adaptive_engine import AdaptivePolicy
        ap = AdaptivePolicy(tmp_path / "p.json")
        before = ap.version
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        load_depth_profiles(hg)
        load_canoodle_delta(hg)
        assert ap.version == before
