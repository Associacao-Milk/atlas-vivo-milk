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

ONTOLOGY_VERSION = "1.0.0"
MILK_NS = "https://associacaomilk.pt/ontology/milk#"
MILK_IRI = "https://associacaomilk.pt/ontology/milk"

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
}

CLASSES = {
    "Source":  "milk:Source",
    "Chunk":   "milk:Chunk",
    "Answer":  "milk:Answer",
}


def jsonld_context() -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "milk": MILK_NS,
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "sh":  "http://www.w3.org/ns/shacl#",
    }
    for term, meta in TERMS.items():
        ctx[term] = {"@id": meta["rdf"], "@type": meta["range"]}
    for cls, iri in CLASSES.items():
        ctx[cls] = iri
    return {"@context": ctx, "@version": ONTOLOGY_VERSION}


def turtle() -> str:
    lines = [
        f"@prefix milk: <{MILK_NS}>.",
        "@prefix owl: <http://www.w3.org/2002/07/owl#>.",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.",
        "",
        f"<{MILK_IRI}> a owl:Ontology ;",
        f"    rdfs:label \"MILK Ontology\" ;",
        f"    owl:versionInfo \"{ONTOLOGY_VERSION}\" .",
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
        "xsd": "http://www.w3.org/2001/XMLSchema#",
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
