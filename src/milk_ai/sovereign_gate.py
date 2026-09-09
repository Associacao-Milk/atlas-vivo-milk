"""MILK IA — SOVEREIGN CORE GATE.

Single entry point that certifies the core runs without Mistral, OpenAI,
Google, Anthropic, MCP or Internet. It performs three checks:

1. Import sovereignty: scan loaded modules for forbidden SDKs.
2. Provider fallback: ``select_provider(None)`` returns a working LocalAdapter.
3. Offline query: execute a real corpus query with network blocked and
   no provider credentials, returning a grounded answer.

The gate is self-contained and is the proof artifact for sovereignty.
"""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .provider_adapter import (
    LocalAdapter, ProviderAdapter, assert_core_sovereign, select_provider,
)
from .compliance import assess_all, PROFILE_REGISTRY
from .ontology import jsonld_context, shacl_shapes, turtle, ONTOLOGY_VERSION
from .export_ngsi import export_source_ngsi, export_source_cnmd


class NetworkDisabledError(RuntimeError):
    """Raised when code unexpectedly tries network while the gate blocks it."""


@dataclass(slots=True)
class SovereignGateReport:
    import_sovereignty_ok: bool
    forbidden_modules: list[str]
    fallback_provider_ok: bool
    fallback_provider_name: str
    offline_query_ok: bool
    offline_answer_citations: int
    compliance_profiles_count: int
    ontology_version: str
    ngsi_ld_export_ok: bool
    shacl_shapes_ok: bool
    details: dict[str, Any] = field(default_factory=dict)


def _block_network() -> None:
    """Replace socket.connect so any network call raises immediately."""
    _orig_connect = socket.socket.connect

    def _blocked_connect(self, address):  # noqa: ANN001
        raise NetworkDisabledError(f"network blocked by SOVEREIGN_CORE_GATE: {address}")

    socket.socket.connect = _blocked_connect  # type: ignore[method-assign]


def run_gate(core_query_fn: Any | None = None, loaded_modules: set[str] | None = None) -> SovereignGateReport:
    """Execute the sovereignty gate. ``core_query_fn`` is an optional callable
    that performs a real corpus query (question -> Answer dict) and is called
    with network blocked. If None, only import/fallback checks run."""
    loaded = loaded_modules if loaded_modules is not None else set()
    forbidden = assert_core_sovereign(loaded)
    import_ok = len(forbidden) == 0

    fallback = select_provider(None)
    fallback_ok = fallback.is_local and fallback.available()
    fallback_name = fallback.name

    offline_ok = False
    citations = 0
    offline_details: dict[str, Any] = {}
    if core_query_fn is not None:
        _block_network()
        try:
            answer = core_query_fn()
            offline_ok = bool(answer) and len(answer.get("citations", [])) > 0
            citations = len(answer.get("citations", []))
            offline_details = {
                "answer_text": (answer.get("text") or "")[:120],
                "citations": answer.get("citations", []),
                "confidence": answer.get("confidence"),
                "warnings": answer.get("warnings", []),
                "model": answer.get("model"),
            }
        except Exception as exc:  # noqa: BLE001
            offline_details = {"error": f"{type(exc).__name__}: {exc}"}

    # compliance profiles present
    compliance_count = len(PROFILE_REGISTRY)

    # ontology artifacts generated
    ctx = jsonld_context()
    ttl = turtle()
    shapes = shacl_shapes()
    onto_ok = ctx.get("@version") == ONTOLOGY_VERSION and "@prefix milk:" in ttl and "@graph" in shapes

    # ngsi-ld export smoke test
    sample_meta = {
        "source_id": "gate-smoke", "sha256": "a" * 64,
        "visibility": "publica", "epistemic_state": "analisado",
        "responsible_entity": "Associacao MILK", "municipality": "Moura",
        "document_type": "relatorio", "rgpd_status": "validado",
        "consent_status": "validado", "human_validated": True,
    }
    ngsi = export_source_ngsi(sample_meta)
    cnmd = export_source_cnmd(sample_meta)
    ngsi_ok = ngsi.get("id", "").startswith("urn:milk:Source:") and cnmd.get("origem") == "MILK_IA"

    return SovereignGateReport(
        import_sovereignty_ok=import_ok,
        forbidden_modules=forbidden,
        fallback_provider_ok=fallback_ok,
        fallback_provider_name=fallback_name,
        offline_query_ok=offline_ok,
        offline_answer_citations=citations,
        compliance_profiles_count=compliance_count,
        ontology_version=ONTOLOGY_VERSION,
        ngsi_ld_export_ok=ngsi_ok,
        shacl_shapes_ok=onto_ok,
        details={"offline_query": offline_details,
                 "compliance_profiles": list(PROFILE_REGISTRY.keys()),
                 "ngsi_sample_id": ngsi.get("id")},
    )


def report_to_dict(r: SovereignGateReport) -> dict[str, Any]:
    return {
        "schema": "ia_milk.sovereign_gate.v1",
        "import_sovereignty_ok": r.import_sovereignty_ok,
        "forbidden_modules": r.forbidden_modules,
        "fallback_provider_ok": r.fallback_provider_ok,
        "fallback_provider_name": r.fallback_provider_name,
        "offline_query_ok": r.offline_query_ok,
        "offline_answer_citations": r.offline_answer_citations,
        "compliance_profiles_count": r.compliance_profiles_count,
        "ontology_version": r.ontology_version,
        "ngsi_ld_export_ok": r.ngsi_ld_export_ok,
        "shacl_shapes_ok": r.shacl_shapes_ok,
        "details": r.details,
        "overall_ok": (r.import_sovereignty_ok and r.fallback_provider_ok
                       and r.offline_query_ok and r.ngsi_ld_export_ok and r.shacl_shapes_ok),
    }
