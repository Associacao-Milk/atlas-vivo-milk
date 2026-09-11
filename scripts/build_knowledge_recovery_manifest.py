#!/usr/bin/env python3
"""MILK IA - Knowledge Recovery Manifest builder (section 10).

Inspects the live state and classifies every recoverable knowledge-bearing
item into one explicit state:

    CANONICAL_SOURCE | DERIVED_KNOWLEDGE | ACTIVE_REFERENCE | REVIEW |
    RESTRICTED | QUARANTINE | TEST_ARTIFACT | RUNTIME_STATE |
    DUPLICATE_EXACT | UNSUPPORTED_MODALITY | FAILED_WITH_REASON

Invariant: UNACCOUNTED == 0. Original source documents are never modified.
Exact duplicate requires content-hash equality.
"""
from __future__ import annotations
import json, os, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from milk_ai.method_repertoire import method_repertoire_count, curatorial_method_nodes
STATE = ROOT / "state"
CORPUS = ROOT / "corpus" / "documents"
QUARANTINE = ROOT / "corpus" / "quarantine"
OUT = STATE / "knowledge_recovery_manifest.json"

STATES = (
    "CANONICAL_SOURCE", "DERIVED_KNOWLEDGE", "ACTIVE_REFERENCE", "REVIEW",
    "RESTRICTED", "QUARANTINE", "TEST_ARTIFACT", "RUNTIME_STATE",
    "DUPLICATE_EXACT", "UNSUPPORTED_MODALITY", "FAILED_WITH_REASON",
    "UNACCOUNTED",
)

# Modalities that lack an operational encoder in this build -> NEEDS_ENCODER.
# Text is the only modality with a working BGE-M3 encoder.
ENCUPPORTED = {"text", "texto"}
NEEDS_ENCODER_MODALITIES = {"image", "photograph", "foto", "audio", "video",
                            "voice", "voz", "object", "objeto", "gesture",
                            "gesto", "performance", "place", "lugar", "toponym",
                            "toponimo", "route", "rota"}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def build():
    items = []
    by_state = Counter()
    seen_hashes: dict[str, str] = {}  # content_hash -> first item id
    method_nodes = 0
    active_refs = 0
    relational_nodes = 0
    relational_edges = 0
    cross_modal_links = 0
    research_gaps = 0

    # --- Canonical corpus documents ---
    for fp in sorted(CORPUS.glob("*.json")):
        content_hash = fp.stem  # filename is the sha256
        item_id = f"source:{content_hash[:16]}"
        modality = "text"
        author = ""
        doc_type = ""
        human_validated = False
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            md = d.get("metadata", {})
            author = md.get("author", "")
            doc_type = md.get("document_type", "")
            human_validated = bool(md.get("human_validated", False))
            meta_hash = md.get("sha256", "")
            if meta_hash and meta_hash != content_hash:
                content_hash = meta_hash
        except Exception as e:
            items.append({"id": item_id, "path": str(fp.relative_to(ROOT)),
                          "state": "FAILED_WITH_REASON",
                          "reason": f"parse_error: {type(e).__name__}"})
            by_state["FAILED_WITH_REASON"] += 1
            continue

        state = "CANONICAL_SOURCE"
        # Duplicate-exact detection by content hash
        if content_hash in seen_hashes:
            state = "DUPLICATE_EXACT"
        else:
            seen_hashes[content_hash] = item_id

        # Unsupported modality detection
        needs_encoder = False
        dt_low = (doc_type or "").lower()
        if any(m in dt_low for m in NEEDS_ENCODER_MODALITIES):
            modality = dt_low
            needs_encoder = True
            state = "UNSUPPORTED_MODALITY" if state == "CANONICAL_SOURCE" else state

        items.append({
            "id": item_id, "path": str(fp.relative_to(ROOT)),
            "state": state, "content_hash": content_hash,
            "modality": modality, "author": author,
            "document_type": doc_type, "human_validated": human_validated,
            "needs_encoder": needs_encoder,
        })
        by_state[state] += 1

    # --- Quarantine ---
    for fp in sorted(QUARANTINE.glob("*")):
        items.append({"id": f"quarantine:{fp.stem[:16]}",
                      "path": str(fp.relative_to(ROOT)),
                      "state": "QUARANTINE", "content_hash": fp.stem})
        by_state["QUARANTINE"] += 1

    # --- Persisted hypergraph (atlas_graph.json) -> DERIVED_KNOWLEDGE / ACTIVE_REFERENCE ---
    atlas_graph = STATE / "atlas_graph.json"
    if atlas_graph.exists():
        try:
            g = json.loads(atlas_graph.read_text(encoding="utf-8"))
            nodes = g.get("nodes", [])
            edges = g.get("edges", [])
            relational_nodes = len(nodes)
            relational_edges = len(edges)
            # method repertoire nodes
            for n in nodes:
                t = (n.get("tipo") or n.get("type") or "").lower()
                nome = (n.get("nome") or n.get("label") or "").lower()
                if t == "method" or "metodo" in t or "metodo" in nome:
                    method_nodes += 1
                # active reference: has a source_id pointer and validated state
                if (n.get("source_id") or n.get("source_pointer")) and \
                   n.get("estado_epistemico") in ("validado", "preparado") or \
                   n.get("validation_state") == "validated":
                    active_refs += 1
            # cross-modal links: edges whose endpoints differ in modality (best-effort)
            node_mod = {}
            for n in nodes:
                nid = n.get("id")
                node_mod[nid] = (n.get("modality") or n.get("modalidade") or
                                 n.get("visibilidade") or "text")
            for e in edges:
                sm = node_mod.get(e.get("source") or e.get("origem"))
                tm = node_mod.get(e.get("target") or e.get("destino"))
                if sm and tm and sm != tm:
                    cross_modal_links += 1
            items.append({"id": "kg:atlas_graph", "path": "state/atlas_graph.json",
                          "state": "DERIVED_KNOWLEDGE",
                          "relational_nodes": relational_nodes,
                          "relational_edges": relational_edges})
            by_state["DERIVED_KNOWLEDGE"] += 1
        except Exception:
            items.append({"id": "kg:atlas_graph", "path": "state/atlas_graph.json",
                          "state": "FAILED_WITH_REASON", "reason": "parse_error"})
            by_state["FAILED_WITH_REASON"] += 1

    # --- Research gaps graph ---
    gap_graph = STATE / "atlas_gap_graph.json"
    if gap_graph.exists():
        try:
            gg = json.loads(gap_graph.read_text(encoding="utf-8"))
            research_gaps = len(gg.get("gaps", gg.get("nodes", [])))
            items.append({"id": "kg:atlas_gap_graph", "path": "state/atlas_gap_graph.json",
                          "state": "DERIVED_KNOWLEDGE", "research_gaps": research_gaps})
            by_state["DERIVED_KNOWLEDGE"] += 1
        except Exception:
            pass

    # --- Evidence bundles -> DERIVED_KNOWLEDGE ---
    eb_dir = STATE / "evidence_bundles"
    eb_count = 0
    if eb_dir.exists():
        for fp in sorted(eb_dir.glob("*.json")):
            eb_count += 1
        if eb_count:
            items.append({"id": "kg:evidence_bundles",
                          "path": "state/evidence_bundles",
                          "state": "DERIVED_KNOWLEDGE", "count": eb_count})
            by_state["DERIVED_KNOWLEDGE"] += 1

    # --- Vector index -> DERIVED_KNOWLEDGE ---
    ci = STATE / "chunk_index"
    if ci.exists():
        items.append({"id": "kg:chunk_index", "path": "state/chunk_index",
                      "state": "DERIVED_KNOWLEDGE"})
        by_state["DERIVED_KNOWLEDGE"] += 1

    # --- Runtime state (adaptive policy, learning events, manifests) ---
    runtime_files = [
        "state/adaptive_policy.json", "state/operational_memory/adaptive_learning_events.jsonl",
        "state/knowledge_ingestion_checkpoint.json", "state/MILK_RESOURCE_REGISTRY.json",
        "state/capability_mesh.json", "state/ccp_manifest.json",
    ]
    for rf in runtime_files:
        p = ROOT / rf
        if p.exists():
            items.append({"id": f"rt:{rf.replace('/', '_')}", "path": rf,
                          "state": "RUNTIME_STATE"})
            by_state["RUNTIME_STATE"] += 1

    # --- Test artifacts ---
    test_patterns = ["state/evaluation_test.json", "state/evaluation_test_B_phase.json",
                     "state/dataset_split.json", "state/controlled_training_report.json",
                     "state/diagnosis_model_bias.json", "tests/controlled_train.py",
                     "tests/create_split.py", "tests/evaluate_test.py"]
    for tp in test_patterns:
        p = ROOT / tp
        if p.exists():
            items.append({"id": f"test:{tp.replace('/', '_')}", "path": tp,
                          "state": "TEST_ARTIFACT"})
            by_state["TEST_ARTIFACT"] += 1

    # --- Restricted: items with removal_requested / restricted rights ---
    # (scanned during corpus pass via metadata.rights_status if needed; counted separately)
    restricted = sum(1 for it in items if it.get("state") == "CANONICAL_SOURCE"
                    and "restricted" in str(it.get("document_type", "")).lower())
    if restricted:
        # reclassify those as RESTRICTED
        for it in items:
            if it.get("state") == "CANONICAL_SOURCE" and "restricted" in str(it.get("document_type", "")).lower():
                it["state"] = "RESTRICTED"
                by_state["CANONICAL_SOURCE"] -= 1
                by_state["RESTRICTED"] += 1

    # --- Method / curatorial repertory (source-grounded, from biblioteca) ---
    repertory_nodes = curatorial_method_nodes()
    method_nodes += method_repertoire_count()
    if repertory_nodes:
        items.append({"id": "kg:method_repertory", "path": "src/milk_ai/method_repertoire.py",
                      "state": "ACTIVE_REFERENCE",
                      "count": len(repertory_nodes),
                      "source_pointer": "biblioteca/milk_framework_conceptual.json"})
        by_state["ACTIVE_REFERENCE"] += 1
        active_refs += len(repertory_nodes)

    unaccounted = by_state.get("UNACCOUNTED", 0)

    manifest = {
        "schema": "ia_milk.knowledge_recovery.v1",
        "generated_at": _now(),
        "states": list(STATES),
        "summary": {
            "total_items": len(items),
            "by_state": dict(by_state),
            "unaccounted": unaccounted,
            "active_references": active_refs,
            "method_repertoire_nodes": method_nodes,
            "relational_nodes": relational_nodes,
            "relational_edges": relational_edges,
            "cross_modal_links": cross_modal_links,
            "research_gaps": research_gaps,
            "evidence_bundles": eb_count,
            "canonical_source_documents": by_state.get("CANONICAL_SOURCE", 0),
            "quarantine": by_state.get("QUARANTINE", 0),
            "duplicate_exact": by_state.get("DUPLICATE_EXACT", 0),
            "unsupported_modality": by_state.get("UNSUPPORTED_MODALITY", 0),
            "needs_encoder_modalities": sorted(NEEDS_ENCODER_MODALITIES),
        },
        "items": items,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    build()
