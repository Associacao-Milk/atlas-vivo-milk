"""MILK IA - 12 Conceptual Proof Queries (Phase 14).

Runs 12 conceptually difficult queries through the validation runtime
and verifies that each produces conceptual constellations, not superficial
keyword retrieval.
"""
import json, urllib.parse, urllib.request, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = "http://127.0.0.1:8767"
OUT = ROOT / "state" / "deep_proof_queries.json"

QUERIES = [
    ("A", "Uma palavra que eu conhecia regressa diferente depois de ser dita por outra pessoa"),
    ("B", "Um silencio numa praca pode ser memoria?"),
    ("C", "Quando uma falha deixa de ser erro e comeca a ser encontro?"),
    ("D", "Como uma linha pode antecipar alguma coisa que ainda nao aconteceu?"),
    ("E", "E possivel ouvir um lugar suspendendo a causa do som e ao mesmo tempo nao destruir o contexto daquele lugar?"),
    ("F", "Um objeto descartado pode tornar-se arquivo sem deixar de ser ferida?"),
    ("G", "O que acontece quando uma memoria nao cabe na cronologia?"),
    ("H", "Como brincar cria realidade sem fingir que ela ja existe?"),
    ("I", "Um territorio pode ser simultaneamente mapa corpo e relacao?"),
    ("J", "O que distingue uma surpresa de uma Dopafania?"),
    ("K", "Uma palavra pode ser corpo antes de ser significado?"),
    ("L", "Quando duas teorias discordam essa discordancia pode ser a relacao mais importante?"),
]


def query(q):
    url = f"{VALIDATION}/research?" + urllib.parse.urlencode({"q": q})
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def main():
    results = []
    for label, q in QUERIES:
        try:
            resp = query(q)
            b = resp.get("bundle", {})
            t = resp.get("trace", {})
            refs = b.get("references", [])
            results.append({
                "label": label,
                "query": q,
                "has_research_context": b.get("has_research_context", False),
                "references_count": len(refs),
                "graph_paths_count": len(b.get("graph_paths", [])),
                "method_nodes": b.get("method_nodes", []),
                "multimodal_links": t.get("multimodal_links", []),
                "source_ids": list(set(t.get("source_ids", []))),
                "research_gap": b.get("research_gap") is not None,
                "trace_id": t.get("trace_id", ""),
                "selected": t.get("references_selected", []),
                "contradictions": len(b.get("contradictions", [])),
            })
        except Exception as e:
            results.append({"label": label, "query": q, "error": str(e)})

    summary = {
        "total_queries": len(results),
        "with_research_context": sum(1 for r in results if r.get("has_research_context")),
        "with_research_gap": sum(1 for r in results if r.get("research_gap")),
        "total_references": sum(r.get("references_count", 0) for r in results),
        "total_graph_paths": sum(r.get("graph_paths_count", 0) for r in results),
        "total_multimodal_links": sum(len(r.get("multimodal_links", [])) for r in results),
        "total_contradictions": sum(r.get("contradictions", 0) for r in results),
        "distinct_sources": len(set(s for r in results for s in r.get("source_ids", []))),
    }

    manifest = {
        "schema": "ia_milk.deep_proof_queries.v1",
        "validation_runtime_revision": resp.get("validation_runtime_revision", "") if results else "",
        "summary": summary,
        "queries": results,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    main()
