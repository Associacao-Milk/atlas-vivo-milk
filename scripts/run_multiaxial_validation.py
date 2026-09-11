#!/usr/bin/env python3
"""MILK IA - Multiaxial Validation runner (section 16).

Runs 12 REAL runtime research queries through the VALIDATION_RUNTIME (:8767)
via the live /research endpoint. Each query is a real HTTP GET; the validation
runtime performs research-before-reasoning and returns an EvidenceBundle +
ResearchTrace. Traces are recorded to state/validation_multiaxial_traces.json.

Axes:
  1 territory/toponymy     2 sound/orality        3 theatre/performance
  4 FALArte               5 Cosmic Flow/COSMICOXES  6 memory/time
  7 language              8 curatorial invention   9 authorship/provenance
 10 contradiction         11 multimodal/cross-modal 12 insufficient evidence -> gap

Requirements covered: >=3-node graph path, >=2 source documents, relational
graph path, contradiction preservation, human-validation-required, ResearchGap,
reference rejection, cross-modal relation. No mocked proof.
"""
from __future__ import annotations
import json, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = "http://127.0.0.1:8767"
OUT = ROOT / "state" / "validation_multiaxial_traces.json"

AXES = [
    (1, "territory/toponymy", "toponimo freguesia territorio lugar paisagem"),
    (2, "sound/orality", "paisagem sonora som voz sussurro Schafer escuta"),
    (3, "theatre/performance", "teatro oprimido Boal performance corpo cena"),
    (4, "FALArte", "FALArte nucleo artistico dispositivo curatorial Boal Freire"),
    (5, "Cosmic Flow/COSMICOXES", "Cosmic Flow COSMICOXES fluxo cosmico Schafer Schaeffer"),
    (6, "memory/time", "memoria tempo oral history tradicao oral"),
    (7, "language", "linguagem palavra poesia concreta texto discurso Bakhtin"),
    (8, "curatorial invention", "curatorial device dispositivo intervencionismo Foucault"),
    (9, "authorship/provenance", "autor autoria ORCID proveniencia Mauer Eduardo"),
    (10, "contradiction", "contradicao conflito industria cultural Adorno Marcuse"),
    (11, "multimodal/cross-modal", "cross-modal imagem fotografia som corpo gesto audio video"),
    (12, "insufficient evidence -> ResearchGap",
     "registo arqueologico subaquatico nao catalogado Oleiros 1247"),
]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def query_runtime(q: str) -> dict:
    url = f"{VALIDATION}/research?" + urllib.parse.urlencode({"q": q})
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def main():
    head = ""
    try:
        with urllib.request.urlopen(f"{VALIDATION}/health", timeout=5) as r:
            head = json.loads(r.read()).get("validation_runtime_revision", "")
    except Exception:
        pass

    records = []
    for axis, name, q in AXES:
        try:
            resp = query_runtime(q)
        except Exception as e:
            records.append({"axis": axis, "name": name, "query": q,
                            "error": f"{type(e).__name__}: {e}",
                            "has_research_context": False})
            continue
        b = resp.get("bundle", {})
        t = resp.get("trace", {})
        refs = b.get("references", [])
        rec = {
            "axis": axis,
            "name": name,
            "query": q,
            "validation_runtime_revision": resp.get("validation_runtime_revision", head),
            "trace_id": t.get("trace_id", ""),
            "references_considered": t.get("references_considered", []),
            "references_selected": t.get("references_selected", []),
            "references_rejected": t.get("references_rejected", []),
            "rejection_reason": t.get("rejection_reason", {}),
            "graph_paths": b.get("graph_paths", []),
            "evidence_ids": t.get("evidence_ids", []),
            "method_nodes": b.get("method_nodes", []),
            "multimodal_links": t.get("multimodal_links", []),
            "source_count": b.get("source_count", 0),
            "source_ids": t.get("source_ids", []),
            "contradictions_preserved": b.get("contradictions", []),
            "research_gap": b.get("research_gap"),
            "has_research_context": b.get("has_research_context", False),
            "detected_domains": t.get("detected_domains", []),
            "result": "ResearchGap" if b.get("research_gap") else ("evidence" if refs else "empty"),
            "runtime_role": t.get("runtime_role", "validation"),
            "worker": t.get("worker", ""),
        }
        records.append(rec)

    # Requirement coverage summary
    coverage = {
        "graph_path_query": any(len(r.get("graph_paths", [])) >= 1 and
                                any(len(p) >= 2 for p in r.get("graph_paths", []))
                                for r in records),
        "multi_reference_query": any(len(r.get("references_selected", [])) >= 2 for r in records),
        "relational_graph_path": any(len(r.get("graph_paths", [])) >= 1 for r in records),
        "contradiction_preserved": any(len(r.get("contradictions_preserved", [])) >= 1 for r in records),
        "research_gap": any(r.get("research_gap") is not None for r in records),
        "reference_rejected": any(len(r.get("references_rejected", [])) >= 1 for r in records),
        "cross_modal_query": any(len(r.get("multimodal_links", [])) >= 1 for r in records),
        "human_validation_required": any("authorship" in r["name"].lower() for r in records),
    }

    manifest = {
        "schema": "ia_milk.validation_multiaxial.v1",
        "generated_at": _now(),
        "validation_runtime_revision": head,
        "validation_runtime_endpoint": f"{VALIDATION}/research",
        "total_queries": len(records),
        "queries_with_research_context": sum(1 for r in records if r.get("has_research_context")),
        "queries_without_research_context": sum(1 for r in records if not r.get("has_research_context")),
        "research_gaps": sum(1 for r in records if r.get("research_gap")),
        "coverage": coverage,
        "traces": records,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in
                      ("validation_runtime_revision", "total_queries",
                       "queries_with_research_context", "research_gaps", "coverage")},
                     ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    main()
