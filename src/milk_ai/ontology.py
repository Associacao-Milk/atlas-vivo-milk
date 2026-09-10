"""MILK IA — Minimal versioned ontology (JSON-LD context + RDF/Turtle + SHACL).

The internal MILK model is plain dataclasses. This module emits the semantic
projection of that model as three artifacts WITHOUT altering the internal
representation:

- JSON-LD context  (``jsonld_context``)  — compact term mapping
- RDF/Turtle       (``turtle``)          — ontology classes/properties
- SHACL shapes     (``shacl_shapes``)    — validation constraints

Versioned via ``ONTOLOGY_VERSION``. All artifacts are deterministic strings
generated from a single term table, so they stay in sync.
"""
from __future__ import annotations

from typing import Any

ONTOLOGY_VERSION = "1.1.0"
MILK_NS = "https://associacaomilk.pt/ontology/milk#"
MILK_IRI = "https://associacaomilk.pt/ontology/milk"
OA_NS = "http://www.w3.org/ns/oa#"
ANNO_CONTEXT = "http://www.w3.org/ns/anno.jsonld"

# term -> (rdf:type, range, sh:datatype, required)
TERMS: dict[str, dict[str, Any]] = {
    "sourceId":        {"rdf": "milk:sourceId",        "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "sha256":          {"rdf": "milk:sha256",           "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "chunkId":         {"rdf": "milk:chunkId",          "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "text":            {"rdf": "milk:text",             "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 0, "max": 1},
    "visibility":      {"rdf": "milk:visibility",      "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "epistemicState":  {"rdf": "milk:epistemicState",   "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "responsibleEntity":{"rdf": "milk:responsibleEntity","type":"owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "municipality":    {"rdf": "milk:municipality",    "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 0, "max": 1},
    "parish":          {"rdf": "milk:parish",           "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 0, "max": 1},
    "documentType":    {"rdf": "milk:documentType",    "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 0, "max": 1},
    "rgpdStatus":      {"rdf": "milk:rgpdStatus",       "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 1, "max": 1},
    "consentStatus":   {"rdf": "milk:consentStatus",    "type": "owl:DatatypeProperty", "range": "xsd:string", "min": 1, "max": 1},
    "humanValidated":  {"rdf": "milk:humanValidated",   "type": "owl:DatatypeProperty", "range": "xsd:boolean", "min": 1, "max": 1},
    "aiRiskLevel":     {"rdf": "milk:aiRiskLevel",     "type": "owl:DatatypeProperty", "range": "xsd:string",  "min": 0, "max": 1},
    "citations":       {"rdf": "milk:hasCitation",     "type": "owl:ObjectProperty",   "range": "milk:Chunk",  "min": 0, "max": -1},
    # --- W3C Web Annotation Data Model (REC 2017-02-23) ---
    # These terms are the semantic bridge between MILK Evidence/Chunk
    # structures and the W3C Web Annotation vocabulary. They reuse the oa:
    # namespace and the standard anno.jsonld context. No new ontology is
    # created — the Annotation class is a projection of EvidenceBundle.
    "body":            {"rdf": "oa:hasBody",            "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": -1},
    "target":          {"rdf": "oa:hasTarget",          "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 1, "max": -1},
    "motivation":      {"rdf": "oa:motivatedBy",       "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": -1},
    "purpose":         {"rdf": "oa:hasPurpose",        "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": -1},
    "selector":        {"rdf": "oa:hasSelector",       "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": -1},
    "source":          {"rdf": "oa:hasSource",         "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 1, "max": 1},
    "creator":         {"rdf": "dcterms:creator",      "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": 1},
    "created":         {"rdf": "dcterms:created",       "type": "owl:DatatypeProperty", "range": "xsd:dateTime","min": 0, "max": 1},
    "generator":       {"rdf": "prov:wasGeneratedBy",  "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": 1},
    "generated":       {"rdf": "prov:generatedAtTime", "type": "owl:DatatypeProperty", "range": "xsd:dateTime","min": 0, "max": 1},
    "canonical":       {"rdf": "oa:canonical",          "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": 1},
    "via":             {"rdf": "oa:via",                "type": "owl:ObjectProperty",   "range": "xsd:string",  "min": 0, "max": -1},
}

CLASSES = {
    "Source":     "milk:Source",
    "Chunk":      "milk:Chunk",
    "Answer":      "milk:Answer",
    "Annotation":  "oa:Annotation",
    "SpecificResource": "oa:SpecificResource",
    "TextualBody": "oa:TextualBody",
}

# W3C Web Annotation Selector classes (§4.2) — reused, not redefined.
SELECTOR_CLASSES = (
    "FragmentSelector", "CssSelector", "XPathSelector",
    "TextQuoteSelector", "TextPositionSelector", "DataPositionSelector",
    "SvgSelector", "RangeSelector",
)

# W3C Web Annotation Motivation instances (§3.3.5) — reused, not redefined.
MOTIVATIONS = (
    "assessing", "bookmarking", "classifying", "commenting",
    "describing", "editing", "highlighting", "identifying",
    "linking", "moderating", "questioning", "replying", "tagging",
)


def jsonld_context() -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "milk": MILK_NS,
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "sh":  "http://www.w3.org/ns/shacl#",
        "oa":  OA_NS,
        "anno": ANNO_CONTEXT,
        "dcterms": "http://purl.org/dc/terms/",
        "prov": "http://www.w3.org/ns/prov#",
    }
    for term, meta in TERMS.items():
        ctx[term] = {"@id": meta["rdf"], "@type": meta["range"]}
    for cls, iri in CLASSES.items():
        ctx[cls] = iri
    return {"@context": ctx, "@version": ONTOLOGY_VERSION}


def turtle() -> str:
    lines = [
        f"@prefix milk: <{MILK_NS}>.",
        f"@prefix oa: <{OA_NS}>.",
        "@prefix owl: <http://www.w3.org/2002/07/owl#>.",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.",
        "@prefix dcterms: <http://purl.org/dc/terms/>.",
        "@prefix prov: <http://www.w3.org/ns/prov#.",
        "",
        f"<{MILK_IRI}> a owl:Ontology ;",
        f"    rdfs:label \"MILK Ontology\" ;",
        f"    owl:versionInfo \"{ONTOLOGY_VERSION}\" ;",
        f"    owl:imports <{OA_NS}> .",
        "",
    ]
    for cls, iri in CLASSES.items():
        lines.append(f"{iri} a owl:Class ; rdfs:label \"{cls}\" .")
    lines.append("")
    for term, meta in TERMS.items():
        lines.append(f"{meta['rdf']} a {meta['type']} ; rdfs:range {meta['range']} .")
    return "\n".join(lines) + "\n"


def shacl_shapes() -> dict[str, Any]:
    prefixes = {
        "sh": "http://www.w3.org/ns/shacl#",
        "milk": MILK_NS,
        "oa": OA_NS,
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "dcterms": "http://purl.org/dc/terms/",
        "prov": "http://www.w3.org/ns/prov#",
    }
    shapes: list[dict[str, Any]] = []
    for cls, iri in CLASSES.items():
        props: list[dict[str, Any]] = []
        for term, meta in TERMS.items():
            constraint: dict[str, Any] = {
                "sh:path": {"@id": meta["rdf"]},
                "sh:datatype": {"@id": meta["range"]} if meta["type"] == "owl:DatatypeProperty" else {"@id": meta["range"]},
            }
            if meta["min"] == 1:
                constraint["sh:minCount"] = 1
            if meta["max"] == 1:
                constraint["sh:maxCount"] = 1
            props.append(constraint)
        shapes.append({
            "@id": f"milk:{cls}Shape",
            "@type": "sh:NodeShape",
            "sh:targetClass": {"@id": iri},
            "sh:property": props,
        })
    return {"@context": prefixes, "@graph": shapes, "milk:ontologyVersion": ONTOLOGY_VERSION}
