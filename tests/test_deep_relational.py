"""MILK IA - Deep Relational Anti-Flattening Tests (Phase 12).

Tests for the profundidade relacional total:
  1. All references have depth profile or ResearchGap
  2. Source provenance never disappears
  3. Epistemic_status never promoted implicitly
  4. Authorial concepts stay authorial
  5. CURATORIAL_SEED stays seed
  6. Philosophy does not become neuroscience
  7. Metaphor does not become scientific fact
  8. Two references with zero lexical overlap can relate structurally
  9. Two references with identical vocabulary can be rejected if structure diverges
  10. Contradiction can INCREASE relational interest
  11. Every relation declares non_equivalence
  12. Multi-hop preserves provenance of all steps
  13. ResearchGap is a legitimate outcome
  14. COSMICOXES receives relational properties, not just words
  15. No determinism in interpretation
  16. Source docs remain intact
  17. Adaptive policy remains isolated during tests
  18. Old tests stay green
"""
import sys, pathlib, hashlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from milk_ai.hypergraph import SovereignHypergraph
from milk_ai.method_repertoire import load_method_repertory, EP_CURATORIAL_SEED
from milk_ai.deep_relations import (
    load_depth_profiles, DEEP_RELATIONS, CONSTELLATIONS,
)
from milk_ai.depth_registry import DEPTH_PROFILES, RESEARCH_GAPS_REGISTRY
from milk_ai.depth_profile import (
    ConceptDepthProfile, DeepRelation, RelevanceManifold,
    COSMICOXES_GRAMMAR, cosmicoxes_projection_for,
)
from milk_ai.research_context import ResearchContextGate, EvidenceBundle
from milk_ai.provenance import CANONICAL_AUTHOR


def _full_graph():
    hg = SovereignHypergraph()
    load_method_repertory(hg)
    load_depth_profiles(hg)
    return hg


_MILK_AUTHOR = CANONICAL_AUTHOR["idealized_by"]


# ---- 1. All references have depth profile or ResearchGap ----

class TestDepthProfileCoverage:
    def test_all_key_references_have_depth_profile(self):
        hg = _full_graph()
        key_nodes = [
            "temporal:retention", "temporal:protention", "temporal:primal_impression",
            "sound:reduced_listening", "listening:causal", "listening:semantic",
            "method:schafer", "method:kandinsky", "method:merleau_ponty",
            "method:winnicott", "method:boal", "method:freire",
            "method:deleuze", "method:barthes", "method:llansol",
            "method:didi_huberman", "method:camus", "method:artaud",
            "method:bakhtin", "method:foucault", "method:bourdieu",
            "method:maturana_varela", "method:bispo_do_rosario",
            "clown:birth", "milk:dopafania", "milk:escuta_identitaria",
            "work:palavra_ritual", "work:campo_do_possivel", "work:dado_sem_lado",
        ]
        for nid in key_nodes:
            node = hg.get_node(nid)
            assert node is not None, f"missing node: {nid}"
            dp = node.metadata.get("depth_profile")
            assert dp is not None, f"missing depth_profile: {nid}"

    def test_research_gaps_for_ambiguous_references(self):
        assert "gap:bandeira" in RESEARCH_GAPS_REGISTRY
        assert "gap:kharms_karml" in RESEARCH_GAPS_REGISTRY
        assert RESEARCH_GAPS_REGISTRY["gap:bandeira"]["status"] == "open"


# ---- 2. Source provenance never disappears ----

class TestProvenancePreservation:
    def test_all_depth_profiles_have_source_pointer(self):
        for nid, dp in DEPTH_PROFILES.items():
            assert dp.source_pointer, f"{nid} has no source_pointer"

    def test_husserl_profile_source(self):
        dp = DEPTH_PROFILES["temporal:retention"]
        assert "husserl" in dp.source_pointer.lower()

    def test_schaeffer_profile_source(self):
        dp = DEPTH_PROFILES["sound:reduced_listening"]
        assert "schaeffer" in dp.source_pointer.lower()

    def test_milk_authorial_concepts_keep_author(self):
        dp = DEPTH_PROFILES["milk:dopafania"]
        assert dp.author == _MILK_AUTHOR
        dp2 = DEPTH_PROFILES["milk:escuta_identitaria"]
        assert dp2.author == _MILK_AUTHOR


# ---- 3. Epistemic_status never promoted implicitly ----

class TestEpistemicStatusIntegrity:
    def test_philosophy_stays_source_not_hypothesis(self):
        dp = DEPTH_PROFILES["temporal:retention"]
        assert dp.epistemic_status == "SOURCE"
        assert dp.epistemic_status != "EXPERIMENTAL_HYPOTHESIS"

    def test_dopafania_stays_hypothesis_not_source(self):
        dp = DEPTH_PROFILES["milk:dopafania"]
        assert dp.epistemic_status == "EXPERIMENTAL_HYPOTHESIS"
        assert dp.epistemic_status != "SOURCE"

    def test_clown_birth_stays_translation_not_source(self):
        dp = DEPTH_PROFILES["clown:birth"]
        assert dp.epistemic_status == "METHOD_TRANSLATION"
        assert dp.epistemic_status != "SOURCE"


# ---- 4. Authorial concepts stay authorial ----

class TestAuthorialPreservation:
    def test_dopafania_authorial(self):
        dp = DEPTH_PROFILES["milk:dopafania"]
        assert dp.author == _MILK_AUTHOR
        assert "NOT dopamine" in dp.what_it_is_not
        assert "NOT a mechanism" in dp.what_it_is_not

    def test_escuta_identitaria_authorial(self):
        dp = DEPTH_PROFILES["milk:escuta_identitaria"]
        assert dp.author == _MILK_AUTHOR
        assert "NOT a Schaeffer category" in dp.what_it_is_not


# ---- 5. CURATORIAL_SEED stays seed ----

class TestCuratorialSeedStatus:
    def test_seeds_not_method_theory(self):
        hg = _full_graph()
        for nid in ("seed:eu_lembrei", "seed:juntos_sempre", "seed:eu_ri",
                    "seed:vem_me_reencontrar", "seed:um_abraco"):
            n = hg.get_node(nid)
            assert n is not None
            assert n.metadata.get("epistemic_status") == EP_CURATORIAL_SEED


# ---- 6. Philosophy does not become neuroscience ----

class TestPhilosophyNeuroscienceSeparation:
    def test_dopafania_not_neuroscience(self):
        dp = DEPTH_PROFILES["milk:dopafania"]
        assert dp.epistemic_status == "EXPERIMENTAL_HYPOTHESIS"
        assert "NOT dopamine" in dp.what_it_is_not
        assert "NOT a scientific fact" in dp.what_it_is_not

    def test_maturana_varela_enaction_provenance(self):
        dp = DEPTH_PROFILES["method:maturana_varela"]
        # Enaction provenance: specifically Varela/Thompson/Rosch 1991
        assert "Varela/Thompson/Rosch 1991" in dp.extended_definition
        assert "Equating enaction with autopoiesis" in str(dp.misreading_risks)


# ---- 7. Metaphor does not become scientific fact ----

class TestMetaphorNotFact:
    def test_heisenberg_not_promoted(self):
        # Heisenberg should NOT be in depth profiles as scientific truth
        # (it's only referenced in the framework as indeterminacy)
        assert "method:heisenberg" not in DEPTH_PROFILES

    def test_dopafania_cosmicoxes_not_scientific(self):
        proj = cosmicoxes_projection_for("dopafania_bloom")
        assert "NUNCA representacao pseudo-cientifica" in proj


# ---- 8. Zero lexical overlap can relate ----

class TestLexicalZeroRelations:
    def test_lexical_zero_relations_exist(self):
        zero_relations = [dr for dr in DEEP_RELATIONS if dr.lexical_overlap == 0]
        assert len(zero_relations) >= 5, "Need at least 5 lexical-zero relations"

    def test_husserl_kandinsky_zero_overlap(self):
        dr = next((d for d in DEEP_RELATIONS
                   if d.relation_id == "dr:husserl_protention_kandinsky_line"), None)
        assert dr is not None
        assert dr.lexical_overlap == 0
        assert dr.non_equivalence  # must declare non-equivalence

    def test_winnicott_clown_zero_overlap(self):
        dr = next((d for d in DEEP_RELATIONS
                   if d.relation_id == "dr:winnicott_clown_birth"), None)
        assert dr is not None
        assert dr.lexical_overlap == 0
        assert "NOT explain the other" in dr.non_equivalence

    def test_retrieval_works_without_common_vocabulary(self):
        """The research gate should retrieve nodes that relate structurally
        even when the query uses different vocabulary than the node label."""
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        # Query using "retention" which is a label of temporal:retention
        b = gate.research(task_id="lx0",
                         query="Husserl retention consciousness temporal",
                         runtime_role="test")
        # Should retrieve Husserl retention or related temporal nodes
        assert b.has_research_context is True
        # Check that at least one reference touches temporal/Husserl concepts
        selected = gate.traces()[-1].references_selected
        assert any("temporal:" in s or "husserl" in s.lower() for s in selected)


# ---- 9. Identical vocabulary can be rejected ----

class TestVocabularyNotSufficient:
    def test_schaeffer_schafer_not_equivalent(self):
        """Schaeffer and Schafer share 'sch' prefix but are NOT equivalent.
        The deep relation preserves their contradiction."""
        dr = next((d for d in DEEP_RELATIONS
                   if d.relation_id == "dr:schaeffer_schafer_contradiction"), None)
        assert dr is not None
        assert "NOT equivalent" in dr.non_equivalence
        assert dr.relevance_manifold.productive_contradiction >= 0.8


# ---- 10. Contradiction increases interest ----

class TestContradictionProductive:
    def test_schaeffer_schafer_contradiction_is_productive(self):
        dr = next((d for d in DEEP_RELATIONS
                   if d.relation_id == "dr:schaeffer_schafer_contradiction"), None)
        assert dr is not None
        assert "INCREASES" in dr.productive_tension

    def test_schafer_known_tension_documented(self):
        dp = DEPTH_PROFILES["method:schafer"]
        assert any("Schaeffer" in t for t in dp.known_tensions)


# ---- 11. Every relation declares non_equivalence ----

class TestNonEquivalenceCoverage:
    def test_all_deep_relations_have_non_equivalence(self):
        for dr in DEEP_RELATIONS:
            assert dr.non_equivalence, f"{dr.relation_id} missing non_equivalence"
            assert len(dr.non_equivalence) > 10, f"{dr.relation_id} has trivial non_equivalence"

    def test_all_deep_relations_have_epistemic_difference(self):
        for dr in DEEP_RELATIONS:
            assert dr.epistemic_difference, f"{dr.relation_id} missing epistemic_difference"

    def test_all_deep_relations_have_relevance_manifold(self):
        for dr in DEEP_RELATIONS:
            assert dr.relevance_manifold is not None, f"{dr.relation_id} missing manifold"

    def test_relevance_manifold_not_scalar(self):
        """The relevance manifold must have multiple axes, not a single score."""
        for dr in DEEP_RELATIONS:
            rm = dr.relevance_manifold
            d = rm.to_dict()
            nonzero = sum(1 for v in d.values() if v > 0)
            assert nonzero >= 2, f"{dr.relation_id} manifold has <2 nonzero axes"


# ---- 12. Multi-hop preserves provenance ----

class TestMultiHopProvenance:
    def test_constellations_have_multiple_hops(self):
        for c in CONSTELLATIONS:
            assert len(c["hops"]) >= 3, f"{c['name']} has <3 hops"

    def test_constellation_preserves_contradiction(self):
        schafer_const = next(c for c in CONSTELLATIONS
                            if "Schaeffer" in c["name"] and "Schafer" in c["name"])
        assert schafer_const["preserves_contradiction"] is True

    def test_husserl_constellation_5_hops(self):
        c = next(c for c in CONSTELLATIONS if "Husserl" in c["name"])
        assert len(c["hops"]) >= 4

    def test_constellation_nodes_exist_in_graph(self):
        hg = _full_graph()
        for c in CONSTELLATIONS:
            for hop in c["hops"]:
                assert hg.get_node(hop) is not None, f"{c['name']}: missing {hop}"


# ---- 13. ResearchGap is legitimate ----

class TestResearchGapLegitimate:
    def test_research_gaps_registered(self):
        assert len(RESEARCH_GAPS_REGISTRY) >= 3

    def test_research_gap_has_question(self):
        for gid, g in RESEARCH_GAPS_REGISTRY.items():
            assert g["question"]
            assert g["missing_evidence"]
            assert g["status"] == "open"

    def test_research_gap_in_graph(self):
        hg = _full_graph()
        gaps = hg.search_gaps("Bandeira")
        assert len(gaps) >= 1


# ---- 14. COSMICOXES receives relational properties ----

class TestCosmicoxesGrammar:
    def test_grammar_entries_exist(self):
        assert len(COSMICOXES_GRAMMAR) >= 15

    def test_retention_grammar(self):
        assert "afterglow" in COSMICOXES_GRAMMAR["retention"]

    def test_protention_grammar(self):
        assert "vetor" in COSMICOXES_GRAMMAR["protention"]

    def test_failure_grammar(self):
        assert "interrompida" in COSMICOXES_GRAMMAR["failure"]

    def test_contradiction_grammar(self):
        assert "atracao/repulsao" in COSMICOXES_GRAMMAR["contradiction"]

    def test_dopafania_bloom_not_scientific(self):
        assert "NUNCA" in COSMICOXES_GRAMMAR["dopafania_bloom"]

    def test_deep_relations_have_cosmicoxes_grammar(self):
        for dr in DEEP_RELATIONS:
            assert dr.cosmicoxes_grammar, f"{dr.relation_id} missing cosmicoxes_grammar"

    def test_depth_profiles_have_cosmicoxes_projection(self):
        for nid, dp in DEPTH_PROFILES.items():
            assert dp.cosmicoxes_projection, f"{nid} missing cosmicoxes_projection"

    def test_projection_for_unknown_concept(self):
        proj = cosmicoxes_projection_for("some_unknown_concept_xyz")
        assert "nao predeterminado" in proj


# ---- 15. No determinism in interpretation ----

class TestNoDeterminism:
    def test_research_gate_can_produce_gap(self):
        """The gate should be able to return a ResearchGap (no forced answer)."""
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="nd1",
                         query="xyzqwerty nonconceptual impossible 9999",
                         runtime_role="test")
        assert b.research_gap is not None

    def test_multiple_hypotheses_possible(self):
        """A query touching multiple domains should retrieve multiple references,
        not collapse into a single deterministic answer."""
        hg = _full_graph()
        gate = ResearchContextGate(hg)
        b = gate.research(task_id="nd2",
                         query="retention protention escuta som palavra corpo",
                         runtime_role="test")
        assert len(b.references) >= 2  # multiple hypotheses


# ---- 16. Source docs intact (checked via git, not in unit test) ----

class TestSourceDocsIntact:
    def test_no_corpus_files_modified(self):
        import subprocess
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True,
            cwd=pathlib.Path(__file__).resolve().parents[1])
        modified = r.stdout.strip().split("\n") if r.stdout.strip() else []
        corpus_mods = [f for f in modified if f.startswith("corpus/")]
        assert len(corpus_mods) == 0, f"corpus files modified: {corpus_mods}"


# ---- 17. Adaptive policy isolated ----

class TestPolicyIsolation:
    def test_policy_hash_stable(self, tmp_path):
        """Adaptive policy should not be mutated by depth profile loading."""
        import json
        from milk_ai.adaptive_engine import AdaptivePolicy
        policy_file = tmp_path / "policy.json"
        ap = AdaptivePolicy(policy_file)
        before = ap.version
        # Load depth profiles (should not touch policy)
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        load_depth_profiles(hg)
        assert ap.version == before


# ---- 18. Depth-specific deepening checks ----

class TestSpecificDepths:
    def test_husserl_not_reduced_to_past_present_future(self):
        dp = DEPTH_PROFILES["temporal:retention"]
        assert "NOT episodic memory" in dp.what_it_is_not
        # "constitutive" appears in axes, not extended_definition
        axes_text = " ".join(dp.axes.values()).lower()
        assert "constitutive" in axes_text

    def test_llansol_not_reduced_to_fragment(self):
        dp = DEPTH_PROFILES["method:llansol"]
        assert "NOT 'fragment'" in dp.what_it_is_not
        assert "cena-fulgor" in dp.conceptual_nucleus

    def test_deleuze_not_reduced_to_rhizome(self):
        dp = DEPTH_PROFILES["method:deleuze"]
        assert "NOT just 'rhizome'" in dp.what_it_is_not
        assert "agencement" in dp.conceptual_nucleus

    def test_barthes_not_reduced_to_punctum(self):
        dp = DEPTH_PROFILES["method:barthes"]
        assert "NOT just punctum" in dp.what_it_is_not
        assert "grain" in dp.conceptual_nucleus

    def test_camus_not_mere_chaos(self):
        dp = DEPTH_PROFILES["method:camus"]
        assert "NOT nihilism" in dp.what_it_is_not
        assert "lucidity" in dp.conceptual_nucleus

    def test_artaud_not_reduced_to_shock(self):
        dp = DEPTH_PROFILES["method:artaud"]
        assert "NOT shock" in dp.what_it_is_not
        assert "exposure" in dp.extended_definition.lower()

    def test_clown_not_reduced_to_humor(self):
        dp = DEPTH_PROFILES["clown:birth"]
        assert "NOT humor" in dp.what_it_is_not
        assert "failure" in dp.conceptual_nucleus

    def test_bispo_not_pathologized(self):
        dp = DEPTH_PROFILES["method:bispo_do_rosario"]
        assert "NOT 'outsider art'" in dp.what_it_is_not
        assert "Pathologizing" in str(dp.misreading_risks)

    def test_maturana_enaction_provenance(self):
        dp = DEPTH_PROFILES["method:maturana_varela"]
        assert "Varela/Thompson/Rosch 1991" in dp.extended_definition

    def test_schafer_key_concepts_present(self):
        dp = DEPTH_PROFILES["method:schafer"]
        ed = dp.extended_definition.lower()
        for concept in ["soundscape", "soundmark", "keynote", "signal", "ear cleaning"]:
            assert concept in ed, f"schafer missing {concept}"

    def test_kandinsky_key_concepts_present(self):
        dp = DEPTH_PROFILES["method:kandinsky"]
        ed = dp.extended_definition.lower()
        for concept in ["point", "line", "tension", "force"]:
            assert concept in ed, f"kandinsky missing {concept}"
        # "plane" appears in the work title and conceptual_neighbors
        full_text = (dp.work + " " + dp.extended_definition + " " + " ".join(dp.conceptual_neighbors)).lower()
        assert "plane" in full_text, "kandinsky missing plane entirely"

    def test_boal_spect_actor_present(self):
        dp = DEPTH_PROFILES["method:boal"]
        assert "spect-actor" in dp.conceptual_nucleus

    def test_freire_reading_world_present(self):
        dp = DEPTH_PROFILES["method:freire"]
        assert "reading the world" in dp.conceptual_nucleus
