"""MILK IA - 12 Nameless Blackbox Queries (Phase 38).

Runs 12 conceptually difficult, nameless queries through the validation
runtime. No author names in prompts. No hints about expected methodology.
Records full traces and synthetic proof results.
"""
import json, urllib.parse, urllib.request, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = "http://127.0.0.1:8767"
OUT = ROOT / "state" / "complexity_blackbox_queries.json"

QUERIES = [
    ("A", "Uma praca esta em silencio. Ao longe ha uma festa. Alguem ri sozinho enquanto outra pessoa permanece parada a olhar uma janela fechada."),
    ("B", "Uma coisa que fiz hoje so vai produzir resposta daqui a tres meses, mas essa resposta vai mudar aquilo que vou fazer amanha."),
    ("C", "Quando o mapa mostrou aquele lugar abandonado, as pessoas comecaram a ir ate la. Depois deixou de estar abandonado."),
    ("D", "Quanto mais tentavam resolver o problema, maior ele ficava."),
    ("E", "Dois lugares comecaram quase iguais. Dez anos depois tornaram-se completamente diferentes."),
    ("F", "Ha uma multidao aos gritos e, mesmo assim, para mim o lugar esta em silencio."),
    ("G", "Uma festa desapareceu durante vinte anos. Quando voltou, ja nao era a mesma, mas todos diziam que era."),
    ("H", "Uma palavra que so uma senhora usa acabou por mudar a maneira como uma freguesia fala de um lugar."),
    ("I", "Uma intervencao feita para aumentar participacao produziu menos participacao seis meses depois."),
    ("J", "Um gesto quase imperceptivel mudou toda a dinamica do encontro."),
    ("K", "Algo parece desordem de perto, mas forma um padrao quando visto durante muito tempo."),
    ("L", "O observador comecou a perceber que aquilo que chamava de problema so existia daquela maneira porque ele o estava a observar daquele lugar."),
]


def query(q):
    url = f"{VALIDATION}/research?" + urllib.parse.urlencode({"q": q})
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def main():
    # Also run synthetic proofs
    sys.path.insert(0, str(ROOT / "src"))
    from milk_ai.complexity import run_all_synthetic_proofs
    proofs = run_all_synthetic_proofs()

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

    # Count polyphonic indicators
    polyphonic_count = sum(1 for r in results if r.get("multimodal_links") and len(r["multimodal_links"]) >= 3)
    multi_source = sum(1 for r in results if len(set(r.get("source_ids", []))) >= 2)
    gap_count = sum(1 for r in results if r.get("research_gap"))

    summary = {
        "total_queries": len(results),
        "with_research_context": sum(1 for r in results if r.get("has_research_context")),
        "with_research_gap": gap_count,
        "total_references": sum(r.get("references_count", 0) for r in results),
        "total_multimodal_links": sum(len(r.get("multimodal_links", [])) for r in results),
        "polyphonic_queries": polyphonic_count,
        "multi_source_queries": multi_source,
        "total_contradictions": sum(r.get("contradictions", 0) for r in results),
        "synthetic_proofs_pass": proofs.get("ALL_PROOFS_PASS", False),
        "synthetic_proofs": {
            k: v.get("PASS", False) if isinstance(v, dict) else v
            for k, v in proofs.items() if k != "ALL_PROOFS_PASS"
        },
    }

    manifest = {
        "schema": "ia_milk.complexity_blackbox.v1",
        "validation_runtime_revision": resp.get("validation_runtime_revision", "") if results else "",
        "summary": summary,
        "queries": results,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    main()
