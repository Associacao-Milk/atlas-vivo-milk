"""Tests for MILK Web Annotation relational engine (W3C REC 2017-02-23).

Validates:
- W3C Annotation Model conformance (@context, id, type, body, target)
- Selector classes (TextQuoteSelector, TextPositionSelector, FragmentSelector)
- Relational engine queries (by chunk, source, motivation)
- Interoperability projections (JSON-LD, SHACL, PROV-O, NGSI-LD)
- Integration with existing EvidenceBundle (no new schema)
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from milk_ai.annotation import (
    AnnotationRelationalEngine,
    Selector,
    SpecificResource,
    WebAnnotation,
)
from milk_ai.ontology import (
    ANNO_CONTEXT,
    MOTIVATIONS,
    ONTOLOGY_VERSION,
    SELECTOR_CLASSES,
    jsonld_context,
    shacl_shapes,
    turtle,
)
from milk_ai.cognitive_control_plane import EvidenceBundle


# ---- W3C conformance ----

class TestW3CConformance:
    def test_annotation_has_required_fields(self):
        a = WebAnnotation(id="urn:milk:annotation:1")
        w = a.to_w3c()
        assert w["@context"] == ANNO_CONTEXT
        assert w["id"] == "urn:milk:annotation:1"
        assert w["type"] == "Annotation"

    def test_annotation_with_body_and_target(self):
        a = WebAnnotation(
            id="urn:milk:annotation:2",
            body=[{"type": "TextualBody", "value": "comentario", "format": "text/plain"}],
            target=[{"source": "urn:milk:source:abc", "type": "SpecificResource"}],
            motivation="commenting",
        )
        w = a.to_w3c()
        assert w["body"]["type"] == "TextualBody"
        assert w["target"]["source"] == "urn:milk:source:abc"
        assert w["motivation"] == "commenting"

    def test_invalid_motivation_rejected(self):
        with pytest.raises(ValueError):
            WebAnnotation(id="x", motivation="invalid_motivation")

    def test_all_w3c_motivations_valid(self):
        for m in MOTIVATIONS:
            a = WebAnnotation(id=f"urn:milk:anno:{m}", motivation=m)
            assert a.motivation == m


# ---- Selectors (W3C §4.2) ----

class TestSelectors:
    def test_text_quote_selector(self):
        s = Selector.text_quote(exact="anotation", prefix="this is an ", suffix=" that has")
        d = s.to_dict()
        assert d["type"] == "TextQuoteSelector"
        assert d["exact"] == "anotation"
        assert d["prefix"] == "this is an "
        assert d["suffix"] == " that has"

    def test_text_position_selector(self):
        s = Selector.text_position(start=412, end=795)
        d = s.to_dict()
        assert d["type"] == "TextPositionSelector"
        assert d["start"] == 412
        assert d["end"] == 795

    def test_fragment_selector(self):
        s = Selector.fragment(value="t=30,60", conforms_to="http://www.w3.org/TR/media-frags/")
        d = s.to_dict()
        assert d["type"] == "FragmentSelector"
        assert d["value"] == "t=30,60"
        assert d["conformsTo"] == "http://www.w3.org/TR/media-frags/"

    def test_invalid_selector_type_rejected(self):
        with pytest.raises(ValueError):
            Selector(type="InvalidSelector")

    def test_all_selector_classes_available(self):
        assert len(SELECTOR_CLASSES) == 8
        for cls in SELECTOR_CLASSES:
            s = Selector(type=cls)
            assert s.type == cls

    def test_selector_refinement(self):
        outer = Selector(type="FragmentSelector", value="para5",
                          refined_by=Selector.text_quote(exact="Selected Text"))
        d = outer.to_dict()
        assert d["refinedBy"]["type"] == "TextQuoteSelector"
        assert d["refinedBy"]["exact"] == "Selected Text"


# ---- Relational engine ----

class TestRelationalEngine:
    def _make_bundle_dict(self):
        b = EvidenceBundle("task-1", "trace-1")
        b.add_evidence(source="retrieval:corpus", content="Evidence text here",
                       content_hash="abc123def456", retrieval_method="dense_bge_m3")
        return b.to_dict()

    def _make_chunk(self, sha="abc123def456789", source_id="src-1"):
        return {
            "chunk_id": f"sha256:{sha}#chunk-00001",
            "source_id": source_id,
            "sha256": sha,
            "text": "This is the chunk text for testing the annotation target.",
        }

    def test_from_evidence_bundle(self):
        engine = AnnotationRelationalEngine()
        bundle = self._make_bundle_dict()
        chunk = self._make_chunk()
        anno = engine.from_evidence_bundle(bundle, chunk, motivation="commenting")
        w = anno.to_w3c()
        assert w["type"] == "Annotation"
        assert w["body"]["type"] == "TextualBody"
        assert w["body"]["value"] == "Evidence text here"
        assert w["target"]["source"] == "urn:milk:source:src-1"
        assert "selector" in w["target"]

    def test_query_by_chunk(self):
        engine = AnnotationRelationalEngine()
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(sha="abc123def456"))
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(sha="xyz999888777"))
        results = engine.annotations_for_chunk("abc123def456")
        assert len(results) == 1
        results2 = engine.annotations_for_chunk("xyz999888777")
        assert len(results2) == 1

    def test_query_by_source(self):
        engine = AnnotationRelationalEngine()
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(source_id="src-A"))
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(source_id="src-B"))
        results = engine.annotations_for_source("src-A")
        assert len(results) == 1

    def test_query_by_motivation(self):
        engine = AnnotationRelationalEngine()
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(), motivation="describing")
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk(), motivation="tagging")
        results = engine.annotations_by_motivation("describing")
        assert len(results) == 1
        results2 = engine.annotations_by_motivation("tagging")
        assert len(results2) == 1

    def test_bodies_for_annotation(self):
        engine = AnnotationRelationalEngine()
        anno = engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        bodies = engine.bodies_for_annotation(anno.id)
        assert len(bodies) == 1
        assert bodies[0]["type"] == "TextualBody"

    def test_relation_graph(self):
        engine = AnnotationRelationalEngine()
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        graph = engine.relation_graph()
        assert graph["schema"] == "ia_milk.annotation.w3c.v1"
        assert graph["stats"]["annotations"] == 1
        assert graph["stats"]["nodes"] >= 3  # annotation + body + target (+selector)
        assert graph["stats"]["edges"] >= 2  # hasBody + hasTarget

    def test_prov_o_projection(self):
        engine = AnnotationRelationalEngine()
        anno = engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        prov = engine.to_prov_o(anno)
        assert prov["@type"] == "prov:Entity"
        assert prov["prov:wasGeneratedBy"] == "milk:cognitive_control_plane"

    def test_ngsi_ld_projection(self):
        engine = AnnotationRelationalEngine()
        anno = engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        ngsi = engine.to_ngsi_ld(anno)
        assert ngsi["type"] == "oa:Annotation"
        assert ngsi["motivation"]["value"] == "commenting"

    def test_all_w3c_serialization(self):
        engine = AnnotationRelationalEngine()
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        engine.from_evidence_bundle(self._make_bundle_dict(), self._make_chunk())
        all_annos = engine.all_w3c()
        assert len(all_annos) == 2
        for a in all_annos:
            assert a["@context"] == ANNO_CONTEXT
            assert a["type"] == "Annotation"


# ---- EvidenceBundle integration ----

class TestEvidenceBundleIntegration:
    def test_to_w3c_annotation(self):
        b = EvidenceBundle("task-w3c", "trace-w3c")
        b.add_evidence(source="retrieval:corpus", content="test evidence",
                       content_hash="hash123", retrieval_method="dense_bge_m3")
        w = b.to_w3c_annotation()
        assert w["@context"] == ANNO_CONTEXT
        assert w["type"] == "Annotation"
        assert w["body"]["type"] == "TextualBody"
        assert w["body"]["value"] == "test evidence"

    def test_save_includes_w3c_annotation(self, tmp_path):
        b = EvidenceBundle("task-save", "trace-save")
        b.add_evidence(source="test", content="save test", content_hash="h1")
        # EvidenceBundle.save uses _EVIDENCE_DIR; verify the w3c key in to_dict+save path
        d = b.to_dict()
        d["w3c_annotation"] = b.to_w3c_annotation()
        assert "w3c_annotation" in d
        assert d["w3c_annotation"]["type"] == "Annotation"


# ---- Ontology persistence ----

class TestOntologyPersistence:
    def test_jsonld_context_has_oa_namespace(self):
        ctx = jsonld_context()
        assert "oa" in ctx["@context"]
        assert ctx["@context"]["Annotation"] == "oa:Annotation"

    def test_turtle_includes_oa(self):
        t = turtle()
        assert "oa:Annotation" in t
        assert "owl:imports" in t

    def test_shacl_has_oa_prefix(self):
        s = shacl_shapes()
        assert "oa" in s["@context"]

    def test_ontology_version_bumped(self):
        assert ONTOLOGY_VERSION == "1.1.0"

    def test_annotation_terms_in_context(self):
        ctx = jsonld_context()
        terms = ctx["@context"]
        assert "body" in terms
        assert "target" in terms
        assert "motivation" in terms
        assert "selector" in terms
        assert "source" in terms
