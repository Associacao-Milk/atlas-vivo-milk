"""MILK IA - Active research, terminology migration, firewall, feedback, rights.

Covers: terminology/schema migration, ResearchContext Gate (research-before-
reasoning), ResearchTrace, EvidenceBundle, ResearchGap, learning provenance
firewall, human curatorial feedback, rights scopes, method repertoire, and
test isolation (test events MUST NOT mutate production policy).
"""
import sys, json, tempfile, pathlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from milk_ai.runtime_nomenclature import (
    VALIDATION_SCHEMA, VALIDATION_HOST, normalize_environment,
    environment_can_mutate_policy, read_validation_revision,
    read_validation_head_match, active_legacy_terms_in_text, LEGACY_TERM_ALIASES,
)
from milk_ai.hypergraph import SovereignHypergraph, HyperNode, HyperEdge
from milk_ai.research_context import (
    ResearchContextGate, ResearchTrace, EvidenceBundle, detect_domains,
)
from milk_ai.method_repertoire import (
    load_method_repertory, method_repertoire_count, curatorial_method_nodes,
)
from milk_ai.learning_firewall import (
    ProductionPolicyGuard, CuratorialFeedbackStore, RightsScope,
    HUMAN_FEEDBACK_CATEGORIES, classify_legacy_event, count_events_by_environment,
    make_provenance,
)
from milk_ai.adaptive_engine import AdaptivePolicy, AdaptiveLearningEngine
from milk_ai.exceptions import SecurityException, SovereigntyPanicController


# ---- Terminology / schema migration ----

class TestTerminologyMigration:
    def test_official_schema_and_host(self):
        assert VALIDATION_SCHEMA == "ia_milk.validation.v1"
        assert VALIDATION_HOST == "MILK-validation"

    def test_legacy_environment_aliases_to_validation(self):
        assert normalize_environment("shadow") == "validation"
        assert normalize_environment("SHADOW") == "validation"

    def test_unknown_environment_is_legacy_unknown(self):
        assert normalize_environment(None) == "legacy_unknown"
        assert normalize_environment("") == "legacy_unknown"
        assert normalize_environment("garbage") == "legacy_unknown"

    def test_official_environments_preserved(self):
        for env in ("production", "validation", "test", "simulation",
                    "curatorial_experiment", "legacy_unknown"):
            assert normalize_environment(env) == env

    def test_compat_reader_reads_legacy_field(self):
        receipt = {"shadow_revision": "abc123", "shadow_match": True}
        assert read_validation_revision(receipt) == "abc123"
        assert read_validation_head_match(receipt) is True

    def test_compat_reader_prefers_canonical_field(self):
        receipt = {"shadow_revision": "old", "validation_runtime_revision": "new"}
        assert read_validation_revision(receipt) == "new"

    def test_legacy_terms_detector_flags_milK_terms(self):
        text = 'schema="ia_milk.shadow.v1" host="MILK-shadow" ShadowHandler'
        hits = active_legacy_terms_in_text(text)
        assert "ia_milk.shadow.v1" in hits
        assert "MILK-shadow" in hits
        assert "ShadowHandler" in hits

    def test_legacy_terms_detector_ignores_generic_shadow_word(self):
        # The bare English word "shadow" (e.g. in CSS box-shadow) is NOT a
        # MILK-specific legacy term and must not be flagged.
        assert active_legacy_terms_in_text("a dark shadow fell across the box-shadow css") == []

    def test_alias_registry_covers_all_required_fields(self):
        required = {"shadow_revision", "shadow_health", "shadow_head_match",
                    "shadow_policy_contamination", "shadow_match"}
        assert required.issubset(set(LEGACY_TERM_ALIASES.keys()))


# ---- ResearchContext Gate ----

class TestResearchContextGate:
    def _graph(self):
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        return hg

    def test_method_repertory_loaded(self):
        hg = self._graph()
        assert hg.node_count >= method_repertoire_count()
        assert hg.get_node("method:boal") is not None
        assert hg.get_node("work:falarte") is not None

    def test_domain_detection(self):
        assert "territory/toponymy" in detect_domains("toponimo freguesia Alfama")
        assert "theatre/performance" in detect_domains("teatro oprimido Boal")
        assert "general" in detect_domains("completely unrelated xyz query")

    def test_research_returns_evidence_bundle(self):
        gate = ResearchContextGate(self._graph())
        b = gate.research(task_id="t1", query="teatro oprimido Boal",
                          worker="test", runtime_role="test")
        assert isinstance(b, EvidenceBundle)
        assert b.has_research_context is True
        assert len(b.references) >= 1
        assert b.source_count >= 1

    def test_research_records_trace(self):
        gate = ResearchContextGate(self._graph())
        gate.research(task_id="t2", query="Cosmic Flow COSMICOXES",
                      runtime_role="test")
        tr = gate.traces()[-1]
        assert isinstance(tr, ResearchTrace)
        assert tr.runtime_role == "test"
        assert tr.detected_domains
        assert tr.references_considered
        assert "method" in tr.detected_domains or "cosmic_flow" in tr.detected_domains

    def test_research_gap_when_evidence_insufficient(self):
        gate = ResearchContextGate(self._graph())
        b = gate.research(task_id="t3",
                         query="registo arqueologico subaquatico inexistente 1247",
                         runtime_role="test")
        assert b.research_gap is not None
        assert b.has_research_context is False
        # ResearchGap is a valid successful outcome
        assert b.research_gap.question != ""

    def test_research_rejects_unvalidated_candidates(self):
        gate = ResearchContextGate(self._graph())
        # The speculative candidate 'cand:sons_nao_catalogados' matches sound
        # tokens but is pending/unvalidated -> must be rejected.
        b = gate.research(task_id="t4", query="sons nao catalogados territorio som",
                          runtime_role="test")
        tr = gate.traces()[-1]
        assert any("cand:" in r for r in tr.references_rejected)
        assert any("cand:" in k for k in tr.rejection_reason)

    def test_contradiction_preserved(self):
        gate = ResearchContextGate(self._graph())
        b = gate.research(task_id="t5",
                         query="industria cultural Adorno Marcuse contradicao",
                         runtime_role="test")
        assert len(b.contradictions) >= 1
        assert "adorno" in b.contradictions[0]["node_a"]

    def test_graph_path_traversal(self):
        gate = ResearchContextGate(self._graph())
        b = gate.research(task_id="t6",
                         query="FALArte Boal Freire teatro dispositivo",
                         runtime_role="test")
        assert len(b.graph_paths) >= 1

    def test_cross_modal_links(self):
        gate = ResearchContextGate(self._graph())
        b = gate.research(task_id="t7", query="Palavra Ritual poesia concreta Beckett",
                          runtime_role="test")
        # Palavra Ritual (voice) inspired_by poetry concreta (image) -> cross-modal
        assert len(b.references) >= 1

    def test_invalid_runtime_role_rejected(self):
        with pytest.raises(ValueError):
            ResearchTrace(task_id="x", runtime_role="bogus_role")


# ---- Learning provenance firewall ----

class TestLearningFirewall:
    def _engine(self, tmp_path):
        return AdaptiveLearningEngine(tmp_path / "policy.json")

    def test_test_environment_does_not_mutate_policy(self, tmp_path):
        eng = self._engine(tmp_path)
        before = eng.policy.version
        for _ in range(5):
            ev = eng.record_outcome(
                task_id="t", trace_id="tr", selected_capability="cap",
                candidates=[], scores_before={}, outcome={"success": True},
                evidence_metrics={}, context={}, environment="test")
            assert ev["provenance"]["environment"] == "test"
            assert ev["provenance"]["policy_mutated"] is False
        assert eng.policy.version == before  # unchanged

    def test_production_environment_mutates_policy(self, tmp_path):
        eng = self._engine(tmp_path)
        before = eng.policy.version
        eng.record_outcome(task_id="t", trace_id="tr", selected_capability="cap",
                          candidates=[], scores_before={}, outcome={"success": True},
                          evidence_metrics={}, context={}, environment="production")
        assert eng.policy.version > before

    def test_simulation_blocked(self, tmp_path):
        eng = self._engine(tmp_path)
        before = eng.policy.version
        eng.record_outcome(task_id="t", trace_id="tr", selected_capability="cap",
                          candidates=[], scores_before={}, outcome={"success": True},
                          evidence_metrics={}, context={}, environment="simulation")
        assert eng.policy.version == before

    def test_curatorial_experiment_allowed(self, tmp_path):
        eng = self._engine(tmp_path)
        before = eng.policy.version
        eng.record_outcome(task_id="t", trace_id="tr", selected_capability="cap",
                          candidates=[], scores_before={}, outcome={"success": True},
                          evidence_metrics={}, context={},
                          environment="curatorial_experiment")
        assert eng.policy.version > before

    def test_production_policy_guard_stats(self, tmp_path):
        ap = AdaptivePolicy(tmp_path / "p.json")
        guard = ProductionPolicyGuard(ap, firewall_log_path=tmp_path / "fw.jsonl")
        guard.attempt_update(environment="validation", capability_id="c",
                             reward=0.5, success=True)
        guard.attempt_update(environment="production", capability_id="c",
                             reward=0.5, success=True)
        s = guard.stats()
        assert s["blocked_nonproduction_policy_updates"] == 1
        assert s["production_policy_updates"] == 1

    def test_legacy_event_classification(self):
        assert classify_legacy_event({"environment": "shadow"}) == "validation"
        assert classify_legacy_event({}) == "legacy_unknown"
        assert classify_legacy_event({"environment": "test"}) == "test"

    def test_event_counts_by_environment(self):
        evs = [{"environment": "test"}, {}, {"environment": "shadow"},
               {"environment": "production"}]
        c = count_events_by_environment(evs)
        assert c["test"] == 1 and c["validation"] == 1
        assert c["production"] == 1 and c["legacy_unknown"] == 1

    def test_learning_event_has_provenance(self, tmp_path):
        eng = self._engine(tmp_path)
        ev = eng.record_outcome(task_id="t", trace_id="tr", selected_capability="c",
                               candidates=[], scores_before={}, outcome={"success": True},
                               evidence_metrics={}, context={}, environment="validation",
                               source_ids=["s1"], evidence_ids=["e1"], graph_paths=[["a","b"]])
        p = ev["provenance"]
        assert p["environment"] == "validation"
        assert p["source_ids"] == ["s1"]
        assert p["graph_paths"] == [["a", "b"]]
        assert "trust_state" in p and "rights_scope" in p

    def test_make_provenance_fields(self):
        p = make_provenance(environment="test", purpose="x", task_id="t",
                            trace_id="tr", worker="w")
        for f in ("environment", "purpose", "task_id", "trace_id", "worker",
                  "policy_version", "human_feedback", "human_validated",
                  "trust_state", "rights_scope", "timestamp"):
            assert f in p


# ---- Human curatorial feedback ----

class TestCuratorialFeedback:
    def test_all_categories_present(self):
        for c in ("fertile_relation", "banal_relation", "incorrect_relation",
                  "preserve_poetics", "damages_poetics", "useful_reference",
                  "irrelevant_reference", "approve_method", "reject_method",
                  "approve_publication", "reject_publication"):
            assert c in HUMAN_FEEDBACK_CATEGORIES

    def test_record_and_polarity(self):
        store = CuratorialFeedbackStore()
        fb = store.record(task_id="t", category="fertile_relation", target="rel:1")
        assert fb.polarity() == 1
        bad = store.record(task_id="t", category="damages_poetics", target="rel:2")
        assert bad.polarity() == -1
        assert len(store.all()) == 2

    def test_invalid_category_rejected(self):
        store = CuratorialFeedbackStore()
        with pytest.raises(ValueError):
            store.record(task_id="t", category="not_a_real_category")

    def test_counts_by_category(self):
        store = CuratorialFeedbackStore()
        store.record(task_id="t", category="approve_method")
        store.record(task_id="t", category="approve_method")
        store.record(task_id="t", category="reject_publication")
        c = store.counts_by_category()
        assert c["approve_method"] == 2
        assert c["reject_publication"] == 1


# ---- Rights / publication / learning scopes ----

class TestRightsScopes:
    def test_distinct_decisions(self):
        # ingest allowed, public NOT allowed -> distinct
        r = RightsScope(ingest_allowed=True, research_allowed=True,
                        public_full_allowed=False, learning_allowed=False)
        assert r.ingest_allowed and not r.public_full_allowed
        assert not r.learning_allowed

    def test_roundtrip(self):
        r = RightsScope(ingest_allowed=True, learning_allowed=True)
        d = r.to_dict()
        r2 = RightsScope.from_dict(d)
        assert r2.ingest_allowed and r2.learning_allowed

    def test_publication_does_not_imply_learning(self):
        r = RightsScope(public_full_allowed=True, learning_allowed=False)
        # Valid and distinct: publication without learning
        assert r.public_full_allowed and not r.learning_allowed


# ---- Security boundary ----

class TestSecurityBoundary:
    def test_security_exception_raised_on_breach(self):
        SovereigntyPanicController.reset()
        with pytest.raises(SecurityException):
            SovereigntyPanicController.handle_auth_breach(
                "0000-0000-0000-0000", "0009-0007-6892-6570")
        assert SovereigntyPanicController.is_frozen() is True
        SovereigntyPanicController.reset()


# ---- Method repertoire ----

class TestMethodRepertoire:
    def test_source_grounded_not_fabricated(self):
        nodes = curatorial_method_nodes()
        assert len(nodes) == method_repertoire_count()
        for n in nodes:
            assert n["source_pointer"] == "biblioteca/milk_framework_conceptual.json"

    def test_eduardo_mauer_works_present(self):
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        for wid in ("work:falarte", "work:cosmic_flow", "work:dado_100lado",
                    "work:palavra_ritual", "work:ode_ao_possivel"):
            assert hg.get_node(wid) is not None

    def test_methodological_references_present(self):
        hg = SovereignHypergraph()
        load_method_repertory(hg)
        for mid in ("method:schafer", "method:schaeffer", "method:boal",
                    "method:freire", "method:beckett", "method:husserl"):
            assert hg.get_node(mid) is not None
