"""MILK IA — Web Annotation relational engine (W3C REC 2017-02-23).

This module incorporates the W3C Web Annotation Data Model into the MILK
cognitive architecture by reusing existing contracts rather than duplicating
them. The core insight is structural equivalence:

    W3C Annotation  ≡  MILK EvidenceBundle
    ─────────────────────────────────────
    body            →  EvidenceItem (content + content_hash + source)
    target          →  Chunk / SourceMetadata (the annotated resource)
    motivation      →  retrieval_method / reranking + oa:Motivation
    selector        →  text selection within a chunk
    creator/generator → existing agent fields
    @context        →  ontology.jsonld_context (now includes oa: namespace)

The relational engine relates annotations to every other MILK entity
(chunks, sources, evidence, provenance, NGSI-LD) through a single canonical
semantic model. No new ontology, no parallel schema, no duplicate structures.

References:
    W3C Web Annotation Data Model — https://www.w3.org/TR/2017/REC-annotation-model-20170223/
"""
from __future__ import annotations

import hashlib
import uuid as _uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .ontology import (
    ANNO_CONTEXT,
    MOTIVATIONS,
    OA_NS,
    ONTOLOGY_VERSION,
    SELECTOR_CLASSES,
)

_W3C_SCHEMA = "ia_milk.annotation.w3c.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(b: str) -> str:
    return hashlib.sha256(b.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Selectors (W3C §4.2) — reused selector classes, not redefined
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Selector:
    """A W3C Web Annotation Selector (§4.2).

    Selectors describe how to determine a segment of a source resource.
    Reuses the 8 standard selector types; no new selector class is created.
    """
    type: str  # one of SELECTOR_CLASSES
    value: str = ""
    exact: str = ""
    prefix: str = ""
    suffix: str = ""
    start: int | None = None
    end: int | None = None
    conforms_to: str = ""
    refined_by: "Selector | None" = None

    def __post_init__(self):
        if self.type not in SELECTOR_CLASSES:
            raise ValueError(f"invalid selector type: {self.type}")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type}
        if self.value:
            d["value"] = self.value
        if self.exact:
            d["exact"] = self.exact
        if self.prefix:
            d["prefix"] = self.prefix
        if self.suffix:
            d["suffix"] = self.suffix
        if self.start is not None:
            d["start"] = self.start
        if self.end is not None:
            d["end"] = self.end
        if self.conforms_to:
            d["conformsTo"] = self.conforms_to
        if self.refined_by:
            d["refinedBy"] = self.refined_by.to_dict()
        return d

    @classmethod
    def text_quote(cls, exact: str, prefix: str = "", suffix: str = "") -> "Selector":
        """TextQuoteSelector (§4.2.4) — select by quoting text + context."""
        return cls(type="TextQuoteSelector", exact=exact, prefix=prefix, suffix=suffix)

    @classmethod
    def text_position(cls, start: int, end: int) -> "Selector":
        """TextPositionSelector (§4.2.5) — select by character offset."""
        return cls(type="TextPositionSelector", start=start, end=end)

    @classmethod
    def fragment(cls, value: str, conforms_to: str = "") -> "Selector":
        """FragmentSelector (§4.2.1) — reuse media-type fragment syntax."""
        return cls(type="FragmentSelector", value=value, conforms_to=conforms_to)


# ---------------------------------------------------------------------------
# SpecificResource (W3C §4) — source + selector/state/scope
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class SpecificResource:
    """W3C SpecificResource (§4) — a source resource made more specific.

    Reuses Chunk as the source. Carries optional selector, scope, purpose.
    """
    source: str               # IRI or chunk_id of the source resource
    selector: Selector | None = None
    purpose: str = ""          # oa:Motivation for this resource's inclusion
    scope: str = ""            # context resource IRI
    type: str = "SpecificResource"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type, "source": self.source}
        if self.selector:
            d["selector"] = self.selector.to_dict()
        if self.purpose:
            d["purpose"] = self.purpose
        if self.scope:
            d["scope"] = self.scope
        return d


# ---------------------------------------------------------------------------
# Annotation (W3C §3.1) — projection of EvidenceBundle
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class WebAnnotation:
    """W3C Web Annotation (§3.1) built from existing MILK structures.

    A W3C Annotation is a rooted directed graph with body+target. In MILK,
    this is structurally equivalent to an EvidenceBundle where evidence
    items are bodies and the chunk/source is the target. This class is a
    projection (serializer) — it does not duplicate the EvidenceBundle
    data; it reads from existing dicts and produces W3C-conformant JSON.
    """
    id: str
    body: list[dict[str, Any]] = field(default_factory=list)
    target: list[dict[str, Any]] = field(default_factory=list)
    motivation: str = ""
    creator: str = ""
    created: str = ""
    generator: str = ""
    generated: str = ""
    canonical: str = ""
    via: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.motivation and self.motivation not in MOTIVATIONS:
            raise ValueError(f"invalid motivation: {self.motivation}")

    def to_w3c(self) -> dict[str, Any]:
        """Serialize to W3C-conformant Web Annotation JSON-LD."""
        d: dict[str, Any] = {
            "@context": ANNO_CONTEXT,
            "id": self.id,
            "type": "Annotation",
        }
        if self.body:
            d["body"] = self.body[0] if len(self.body) == 1 else self.body
        if self.target:
            d["target"] = self.target[0] if len(self.target) == 1 else self.target
        if self.motivation:
            d["motivation"] = self.motivation
        if self.creator:
            d["creator"] = self.creator
        if self.created:
            d["created"] = self.created
        if self.generator:
            d["generator"] = self.generator
        if self.generated:
            d["generated"] = self.generated
        if self.canonical:
            d["canonical"] = self.canonical
        if self.via:
            d["via"] = self.via
        return d


# ---------------------------------------------------------------------------
# Relational engine — connects annotations to all MILK entities
# ---------------------------------------------------------------------------

class AnnotationRelationalEngine:
    """Motor relacional — relates W3C Annotations to MILK entities.

    Single canonical semantic model connecting:
        Annotation → Body (EvidenceItem) → Target (Chunk) → Source → Provenance → NGSI-LD

    No duplicate memory structures: all relations are computed from existing
    dicts. The engine is stateless and read-only (projection-only, like
    export_ngsi.py).
    """

    def __init__(self):
        self._annotations: list[WebAnnotation] = []

    # -- Construction from existing MILK structures --

    def from_evidence_bundle(self, bundle_dict: dict[str, Any],
                             target_chunk: dict[str, Any] | None = None,
                             motivation: str = "commenting") -> WebAnnotation:
        """Build a W3C Annotation from an existing EvidenceBundle dict.

        Reuses EvidenceBundle.to_dict() output — no new schema. Evidence
        items become TextualBody bodies; the target chunk becomes the target.
        """
        items = bundle_dict.get("items", [])
        bodies: list[dict[str, Any]] = []
        for item in items:
            body: dict[str, Any] = {
                "type": "TextualBody",
                "value": item.get("content", ""),
                "format": "text/plain",
            }
            if item.get("content_hash"):
                body["id"] = f"urn:milk:evidence:{item['content_hash'][:16]}"
            if item.get("retrieval_method"):
                body["purpose"] = self._map_method_to_purpose(item.get("retrieval_method", ""))
            if item.get("reranking"):
                body["format"] = "text/plain"
            bodies.append(body)

        targets: list[dict[str, Any]] = []
        if target_chunk:
            target = self._chunk_to_target(target_chunk)
            targets.append(target)

        anno_id = f"urn:milk:annotation:{bundle_dict.get('task_id', _uuid.uuid4().hex[:16])}"
        anno = WebAnnotation(
            id=anno_id,
            body=bodies,
            target=targets,
            motivation=motivation if motivation in MOTIVATIONS else "commenting",
            creator=bundle_dict.get("task_id", ""),
            created=bundle_dict.get("created_at", _now()),
            generator="milk:cognitive_control_plane",
            generated=bundle_dict.get("created_at", _now()),
            canonical=bundle_dict.get("hash_chain", ""),
        )
        self._annotations.append(anno)
        return anno

    def _map_method_to_purpose(self, method: str) -> str:
        """Map MILK retrieval_method to W3C Motivation (purpose)."""
        mapping = {
            "dense_bge_m3": "describing",
            "candidate_canonical": "describing",
            "sparse_search": "identifying",
            "adapter_read": "linking",
            "gap_engine": "questioning",
        }
        return mapping.get(method, "describing")

    def _chunk_to_target(self, chunk: dict[str, Any]) -> dict[str, Any]:
        """Build a W3C Target from a MILK Chunk dict.

        Reuses chunk_id and sha256. If the chunk has text, a TextQuoteSelector
        is derived from the first 200 chars for W3C §4.2.4 compliance.
        """
        source_id = chunk.get("source_id", "")
        chunk_id = chunk.get("chunk_id", "")
        text = chunk.get("text", "")

        target: dict[str, Any] = {
            "source": f"urn:milk:source:{source_id}" if source_id else chunk_id,
            "type": "SpecificResource",
        }
        if chunk.get("sha256"):
            target["id"] = f"urn:milk:chunk:{chunk['sha256'][:16]}"
        if text:
            preview = text[:200]
            target["selector"] = Selector.text_quote(
                exact=preview, prefix="", suffix=""
            ).to_dict()
        return target

    # -- Relational queries --

    def annotations_for_chunk(self, chunk_sha256: str) -> list[WebAnnotation]:
        """Query: which annotations target this chunk?"""
        ref = chunk_sha256[:16]
        return [a for a in self._annotations
                if any(ref in str(t.get("id", "")) for t in a.target)]

    def annotations_for_source(self, source_id: str) -> list[WebAnnotation]:
        """Query: which annotations target chunks from this source?"""
        ref = f"urn:milk:source:{source_id}"
        return [a for a in self._annotations
                if any(ref in str(t.get("source", "")) for t in a.target)]

    def bodies_for_annotation(self, anno_id: str) -> list[dict[str, Any]]:
        """Query: what bodies (evidence) does this annotation have?"""
        for a in self._annotations:
            if a.id == anno_id:
                return a.body
        return []

    def annotations_by_motivation(self, motivation: str) -> list[WebAnnotation]:
        """Query: which annotations have this motivation?"""
        if motivation not in MOTIVATIONS:
            return []
        return [a for a in self._annotations if a.motivation == motivation]

    def relation_graph(self) -> dict[str, Any]:
        """Build the full relation graph: Annotation → Body → Target → Source.

        Returns a single canonical graph connecting all W3C and MILK entities.
        This is the relational engine output — every annotation, its bodies,
        targets, selectors, motivations, and source links in one structure.
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        for a in self._annotations:
            nodes.append({"id": a.id, "type": "Annotation", "motivation": a.motivation})
            for body in a.body:
                bid = body.get("id", f"urn:milk:body:{_sha256(str(body))[:16]}")
                nodes.append({"id": bid, "type": "TextualBody",
                              "purpose": body.get("purpose", "")})
                edges.append({"source": a.id, "relation": "hasBody", "target": bid})
            for target in a.target:
                tid = target.get("id", target.get("source", ""))
                nodes.append({"id": tid, "type": "SpecificResource",
                              "source": target.get("source", "")})
                edges.append({"source": a.id, "relation": "hasTarget", "target": tid})
                if "selector" in target:
                    sel = target["selector"]
                    sid = f"{tid}#selector"
                    nodes.append({"id": sid, "type": sel.get("type", "Selector")})
                    edges.append({"source": tid, "relation": "hasSelector", "target": sid})
        return {
            "schema": _W3C_SCHEMA,
            "ontology_version": ONTOLOGY_VERSION,
            "w3c_spec": "https://www.w3.org/TR/2017/REC-annotation-model-20170223/",
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "annotations": len(self._annotations),
                "nodes": len(nodes),
                "edges": len(edges),
            },
        }

    # -- Projections to existing interoperability layers --

    def to_prov_o(self, anno: WebAnnotation) -> dict[str, Any]:
        """Project a W3C Annotation to PROV-O (reuses EvidenceBundle pattern)."""
        return {
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "@id": anno.id,
            "@type": "prov:Entity",
            "prov:wasGeneratedBy": anno.generator or "milk:cognitive_control_plane",
            "prov:generatedAtTime": anno.generated or _now(),
            "prov:wasAttributedTo": anno.creator,
        }

    def to_ngsi_ld(self, anno: WebAnnotation) -> dict[str, Any]:
        """Project a W3C Annotation to NGSI-LD (reuses export_ngsi pattern)."""
        from .export_ngsi import to_ngsi_ld
        props = {
            "motivation": anno.motivation,
            "body": [b.get("id", _sha256(str(b))) for b in anno.body],
            "target": [t.get("id", t.get("source", "")) for t in anno.target],
            "creator": anno.creator,
            "created": anno.created,
        }
        return to_ngsi_ld("Annotation", anno.id.split(":")[-1], props)

    def all_w3c(self) -> list[dict[str, Any]]:
        """Serialize all annotations to W3C-conformant JSON-LD."""
        return [a.to_w3c() for a in self._annotations]

    @property
    def count(self) -> int:
        return len(self._annotations)
