"""MILK IA — NGSI-LD / CNMD export (projection-only, never mutates internal model).

Converts MILK internal Source/Chunk/Answer dataclasses into NGSI-LD entity
documents and CNMD-style data records. The internal model is untouched: this
module only reads dicts and produces new dicts in the target formats.
"""
from __future__ import annotations

import json
from typing import Any

from .ontology import MILK_NS, ONTOLOGY_VERSION

NGSI_LD_TYPES = {
    "Source": "milk:Source",
    "Chunk": "milk:Chunk",
    "Answer": "milk:Answer",
    "Annotation": "oa:Annotation",
}


def to_ngsi_ld(entity_type: str, entity_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    """Build a single NGSI-LD entity document from MILK properties.

    Scalar values become NGSI-LD Property objects; lists become NGSI-LD
    Relationships when the item looks like an entity ref, else a Property.
    """
    ngsi_type = NGSI_LD_TYPES.get(entity_type, f"milk:{entity_type}")
    entity: dict[str, Any] = {
        "id": f"urn:milk:{entity_type}:{entity_id}",
        "type": ngsi_type,
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
            {"milk": MILK_NS},
        ],
    }
    for key, value in properties.items():
        if value is None:
            continue
        if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            # citations / refs -> NGSI-LD Relationship list
            entity[key] = [
                {"type": "Relationship", "object": v if v.startswith("urn:") else f"urn:milk:Chunk:{v}"}
                for v in value
            ]
        elif isinstance(value, (dict,)):
            entity[key] = {"type": "Property", "value": value}
        else:
            entity[key] = {"type": "Property", "value": value}
    return entity


def to_cnmd_record(entity_type: str, entity_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    """Build a CNMD-style flat data record (Cadastro Nacional de Modelos de Dados).

    CNMD favours flat key/value records with explicit typing and provenance.
    """
    record: dict[str, Any] = {
        "id": entity_id,
        "tipo": entity_type,
        "schema_version": ONTOLOGY_VERSION,
        "origem": "MILK_IA",
    }
    record.update({k: v for k, v in properties.items() if v is not None})
    return record


def export_source_ngsi(source_meta: dict[str, Any]) -> dict[str, Any]:
    props = {
        "sha256": source_meta.get("sha256"),
        "visibility": source_meta.get("visibility"),
        "epistemicState": source_meta.get("epistemic_state"),
        "responsibleEntity": source_meta.get("responsible_entity"),
        "municipality": source_meta.get("municipality"),
        "parish": source_meta.get("parish"),
        "documentType": source_meta.get("document_type"),
        "rgpdStatus": source_meta.get("rgpd_status"),
        "consentStatus": source_meta.get("consent_status"),
        "humanValidated": source_meta.get("human_validated"),
    }
    return to_ngsi_ld("Source", source_meta.get("source_id", "unknown"), props)


def export_source_cnmd(source_meta: dict[str, Any]) -> dict[str, Any]:
    props = {
        "sha256": source_meta.get("sha256"),
        "visibilidade": source_meta.get("visibility"),
        "estado_epistemico": source_meta.get("epistemic_state"),
        "entidade_responsavel": source_meta.get("responsible_entity"),
        "municipio": source_meta.get("municipality"),
        "freguesia": source_meta.get("parish"),
        "tipo_documento": source_meta.get("document_type"),
        "estado_rgpd": source_meta.get("rgpd_status"),
        "estado_consentimento": source_meta.get("consent_status"),
        "validado_humano": source_meta.get("human_validated"),
    }
    return to_cnmd_record("Fonte", source_meta.get("source_id", "unknown"), props)
