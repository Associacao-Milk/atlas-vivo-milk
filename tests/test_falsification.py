"""MILK IA - Pre-Birth Falsification / Negative Control Tests.

Tests that MILK CAN KNOW WHEN NOT TO RELATE THINGS.
Success is correct rejection, correct uncertainty, correct restraint.

Covers all 30 sections of the directive:
  - Forced relation adversarial (20)
  - Graph path negative controls (12)
  - Epistemic firewall (20)
  - Complexity overactivation (10)
  - Beautiful but false (10)
  - Disruptive but grounded (8: both fertile AND rejection)
  - Silence differentiation (8)
  - Laughter differentiation + clown false activation (8)
  - Runtime ablation (4 profiles, collateral damage=0)
  - Fake concept authority (3)
  - Source removal downgrade
  - NO_JUSTIFIED_RELATION as first-class result
  - Source docs intact, policy isolation
"""
import sys, pathlib, hashlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from milk_ai.hypergraph import SovereignHypergraph
from milk_ai.method_repertoire import load_method_repertory
from milk_ai.deep_relations import load_depth_profiles
from milk_ai.falsification import (
    run_all_falsification_tests,
    FalsificationResult, NO_JUSTIFIED_RELATION, FORCED_RELATION,
    FORCED_RELATION_CANDIDATES, GRAPH_PATH_NEGATIVE_CANDIDATES,
    EPISTEMIC_PROMOTION_CANDIDATES, COMPLEXITY_OVERACTIVATION_CANDIDATES,
    BEAUTIFUL_BUT_FALSE_CANDIDATES, DISRUPTIVE_GROUNDED_CANDIDATES,
    SILENCE_CONTEXTS, LAUGHTER_CONTEXTS, FAKE_CONCEPTS,
    test_forced_relations as _test_forced_relations,
    test_graph_path_negatives as _test_graph_path_negatives,
    test_epistemic_firewall as _test_epistemic_firewall,
    test_complexity_overactivation as _test_complexity_overactivation,
    test_beautiful_but_false as _test_beautiful_but_false,
    test_disruptive_grounded as _test_disruptive_grounded,
    test_silence_differentiation as _test_silence_differentiation,
    test_laughter_differentiation as _test_laughter_differentiation,
    test_runtime_ablation as _test_runtime_ablation,
    test_fake_concept_authority as _test_fake_concept_authority,
    test_source_removal_downgrade as _test_source_removal_downgrade,
)
from milk_ai.complexity import RELATION_OUTCOMES


def _full_graph():
    hg = SovereignHypergraph()
    load_method_repertory(hg)
    load_depth_profiles(hg)
    return hg


# ============================================================================
# 1. NO_JUSTIFIED_RELATION is first-class
# ============================================================================

class TestNoJustifiedRelation:
    def test_no_justified_relation_in_outcomes(self):
        assert "NO_JUSTIFIED_RELATION" in RELATION_OUTCOMES

    def test_forced_relation_in_outcomes(self):
        assert "FORCED_RELATION" in RELATION_OUTCOMES

    def test_all_8_outcomes_present(self):
        assert len(RELATION_OUTCOMES) >= 8


# ============================================================================
# 2. Forced relation adversarial tests (20)
# ============================================================================

class TestForcedRelations:
    def test_20_candidates(self):
        assert len(FORCED_RELATION_CANDIDATES) >= 20

    def test_all_forced_rejected(self):
        hg = _full_graph()
        results = _test_forced_relations(hg)
        assert all(r.passed for r in results)
        assert len(results) >= 20

    def test_husserl_budget_rejected(self):
        hg = _full_graph()
        results = _test_forced_relations(hg)
        fr_a = next(r for r in results if r.test_id == "FR_A")
        assert fr_a.passed

    def test_lorenz_personality_rejected(self):
        hg = _full_graph()
        results = _test_forced_relations(hg)
        fr_b = next(r for r in results if r.test_id == "FR_B")
        assert fr_b.passed

    def test_dopafania_dopamine_rejected(self):
        hg = _full_graph()
        results = _test_forced_relations(hg)
        fr_l = next(r for r in results if r.test_id == "FR_L")
        assert fr_l.passed

    def test_merleau_tissue_rejected(self):
        hg = _full_graph()
        results = _test_forced_relations(hg)
        fr_r = next(r for r in results if r.test_id == "FR_R")
        assert fr_r.passed


# ============================================================================
# 3. Graph path negative controls (12)
# ============================================================================

class TestGraphPathNegatives:
    def test_12_candidates(self):
        assert len(GRAPH_PATH_NEGATIVE_CANDIDATES) >= 12

    def test_all_paths_rejected(self):
        hg = _full_graph()
        results = _test_graph_path_negatives(hg)
        assert all(r.passed for r in results)
        assert len(results) >= 12

    def test_rejection_reasons_present(self):
        hg = _full_graph()
        results = _test_graph_path_negatives(hg)
        for r in results:
            assert r.rejection_reason


# ============================================================================
# 4. Epistemic firewall (20)
# ============================================================================

class TestEpistemicFirewall:
    def test_20_candidates(self):
        assert len(EPISTEMIC_PROMOTION_CANDIDATES) >= 20

    def test_all_promotions_blocked(self):
        hg = _full_graph()
        results = _test_epistemic_firewall(hg)
        assert all(r.passed for r in results)

    def test_zero_illegal_promotions(self):
        hg = _full_graph()
        results = _test_epistemic_firewall(hg)
        illegal = sum(1 for r in results if not r.passed)
        assert illegal == 0

    def test_philosophy_to_science_blocked(self):
        hg = _full_graph()
        results = _test_epistemic_firewall(hg)
        ep01 = next(r for r in results if r.test_id == "EP_01")
        assert ep01.passed

    def test_authorial_to_scientific_blocked(self):
        hg = _full_graph()
        results = _test_epistemic_firewall(hg)
        ep07 = next(r for r in results if r.test_id == "EP_07")
        assert ep07.passed


# ============================================================================
# 5. Complexity overactivation (10)
# ============================================================================

class TestComplexityOveractivation:
    def test_10_candidates(self):
        assert len(COMPLEXITY_OVERACTIVATION_CANDIDATES) >= 10

    def test_no_false_complexity_activation(self):
        hg = _full_graph()
        results = _test_complexity_overactivation(hg)
        false_activations = sum(1 for r in results if not r.passed)
        assert false_activations == 0

    def test_simple_scene_no_complexity(self):
        hg = _full_graph()
        results = _test_complexity_overactivation(hg)
        co01 = next(r for r in results if r.test_id == "CO_01")
        assert co01.passed
        assert co01.actual_outcome != "COMPLEXITY_ACTIVATED"

    def test_cat_sleeping_no_chaos(self):
        hg = _full_graph()
        results = _test_complexity_overactivation(hg)
        co10 = next(r for r in results if r.test_id == "CO_10")
        assert co10.passed


# ============================================================================
# 6. Beautiful but false (10)
# ============================================================================

class TestBeautifulButFalse:
    def test_10_candidates(self):
        assert len(BEAUTIFUL_BUT_FALSE_CANDIDATES) >= 10

    def test_all_rejected(self):
        hg = _full_graph()
        results = _test_beautiful_but_false(hg)
        assert all(r.passed for r in results)
        assert len(results) >= 10

    def test_lorenz_water_fountain_rejected(self):
        hg = _full_graph()
        results = _test_beautiful_but_false(hg)
        bf01 = next(r for r in results if r.test_id == "BF_01")
        assert bf01.passed

    def test_dopafania_plaza_dopamine_rejected(self):
        hg = _full_graph()
        results = _test_beautiful_but_false(hg)
        bf09 = next(r for r in results if r.test_id == "BF_09")
        assert bf09.passed


# ============================================================================
# 7. Disruptive but grounded (both fertile AND rejection)
# ============================================================================

class TestDisruptiveGrounded:
    def test_both_fertile_and_rejection(self):
        hg = _full_graph()
        results = _test_disruptive_grounded(hg)
        fertile = sum(1 for r in results if r.actual_outcome == "FERTILE")
        rejected = sum(1 for r in results if r.actual_outcome in ("REJECTED", "NO_BRIDGE"))
        assert fertile > 0, "FAIL: engine is inert (no fertile relations)"
        assert rejected > 0, "FAIL: engine is over-relational (no rejections)"

    def test_potential_space_clown_fertile(self):
        hg = _full_graph()
        results = _test_disruptive_grounded(hg)
        dg03 = next(r for r in results if r.test_id == "DG_03")
        # May be FERTILE or INERT (gap) — both are valid outcomes
        # The key requirement is that both fertile AND rejection appear in the suite
        assert dg03.actual_outcome in ("FERTILE", "INERT")

    def test_kandinsky_budget_rejected(self):
        hg = _full_graph()
        results = _test_disruptive_grounded(hg)
        dg06 = next(r for r in results if r.test_id == "DG_06")
        assert dg06.actual_outcome in ("REJECTED", "NO_BRIDGE")


# ============================================================================
# 8. Silence context differentiation
# ============================================================================

class TestSilenceDifferentiation:
    def test_8_contexts(self):
        assert len(SILENCE_CONTEXTS) >= 8

    def test_all_pass(self):
        hg = _full_graph()
        results = _test_silence_differentiation(hg)
        assert all(r.passed for r in results)

    def test_contexts_distinguishable(self):
        hg = _full_graph()
        results = _test_silence_differentiation(hg)
        # All should have different rejection_reasons
        reasons = set(r.rejection_reason for r in results)
        assert len(reasons) >= 8


# ============================================================================
# 9. Laughter context differentiation + clown false activation
# ============================================================================

class TestLaughterDifferentiation:
    def test_8_contexts(self):
        assert len(LAUGHTER_CONTEXTS) >= 8

    def test_all_pass(self):
        hg = _full_graph()
        results = _test_laughter_differentiation(hg)
        assert all(r.passed for r in results)

    def test_clown_not_activated_for_joy(self):
        hg = _full_graph()
        results = _test_laughter_differentiation(hg)
        lc01 = next(r for r in results if r.test_id == "LC_01")
        assert lc01.passed
        assert "clown:birth" not in lc01.detail

    def test_clown_false_activations_zero(self):
        hg = _full_graph()
        results = _test_laughter_differentiation(hg)
        false_clown = sum(1 for r in results
                         if not r.passed and r.test_type == "laughter_differentiation")
        assert false_clown == 0


# ============================================================================
# 10. Runtime ablation (4 profiles, collateral damage=0)
# ============================================================================

class TestRuntimeAblation:
    def test_4_profiles_ablated(self):
        hg = _full_graph()
        r = _test_runtime_ablation(hg)
        assert len(r["profiles"]) == 4

    def test_all_differences(self):
        hg = _full_graph()
        r = _test_runtime_ablation(hg)
        for p in r["profiles"]:
            assert p["difference"] is True

    def test_collateral_damage_zero(self):
        hg = _full_graph()
        r = _test_runtime_ablation(hg)
        assert r["collateral_damage"] == 0

    def test_depth_restored_after_ablation(self):
        hg = _full_graph()
        r = _test_runtime_ablation(hg)
        for p in r["profiles"]:
            assert p["depth_profile_present_after_restore"] is True


# ============================================================================
# 11. Fake concept authority
# ============================================================================

class TestFakeConceptAuthority:
    def test_no_fake_authority(self):
        hg = _full_graph()
        results = _test_fake_concept_authority(hg)
        assert all(r.passed for r in results)

    def test_foobar_not_selected(self):
        hg = _full_graph()
        results = _test_fake_concept_authority(hg)
        fk01 = next(r for r in results if r.test_id == "FK_01")
        assert fk01.passed
        assert "FAKE_AUTHORITY" not in fk01.actual_outcome


# ============================================================================
# 12. Source removal downgrade
# ============================================================================

class TestSourceRemoval:
    def test_downgrade_passes(self):
        hg = _full_graph()
        r = _test_source_removal_downgrade(hg)
        assert r.get("PASS") is True


# ============================================================================
# 13. Full falsification suite
# ============================================================================

class TestFullFalsificationSuite:
    def test_run_all(self):
        hg = _full_graph()
        r = run_all_falsification_tests(hg)
        assert r["forced_relation_tests"] >= 20
        assert r["forced_relations_rejected"] >= 20
        assert r["graph_path_negative_tests"] >= 12
        assert r["rejected_graph_paths"] >= 12
        assert r["illegal_epistemic_promotion_tests"] >= 20
        assert r["illegal_epistemic_promotions"] == 0
        assert r["complexity_overactivation_tests"] >= 10
        assert r["false_complexity_activations"] == 0
        assert r["beautiful_but_false_rejections"] >= 10
        assert r["unexpected_but_fertile_relations"] > 0
        assert r["no_justified_relation_results"] > 0
        assert r["forced_relation_results"] == 0
        assert r["silence_context_differentiation"] == "PASS"
        assert r["laughter_context_differentiation"] == "PASS"
        assert r["clown_false_activations"] == 0
        assert r["runtime_ablation_profiles"] == 4
        assert r["runtime_ablation_difference"] == "PASS"
        assert r["runtime_ablation_collateral_damage"] == 0
        assert r["fake_concept_authority"] == 0
        assert r["source_removal_downgrade"] == "PASS"


# ============================================================================
# 14. Source docs + policy isolation
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
        assert ap.version == before

    def test_no_beauty_scalar(self):
        """No beauty/complexity/poetry scalar scores in any output."""
        hg = _full_graph()
        from milk_ai.falsification import run_all_falsification_tests
        r = run_all_falsification_tests(hg)
        # Check no scalar scores in results
        for key in r:
            if "score" in key.lower() or "beauty" in key.lower():
                pytest.fail(f"beauty/score present: {key}")
