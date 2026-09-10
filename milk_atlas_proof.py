#!/usr/bin/env python3
"""MILK Atlas Operational Proof — Phase 5.

Runs real READ operations on each authenticable adapter, executes a MILK
query that uses evidence from at least one external source, demonstrates
provenance end-to-end, and saves results for /milk-live.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.external_adapters import get_all_adapters, Evidence
from milk_ai.gap_engine import GapEngine


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    print("=" * 70)
    print("MILK ATLAS OPERATIONAL PROOF — READ/AUDIT")
    print("=" * 70)

    results = {
        "schema": "ia_milk.atlas_operational_proof.v1",
        "timestamp": now(),
        "real_reads": {},
        "external_evidence_query": {},
        "provenance_chain": [],
    }

    adapters = get_all_adapters()

    # ---- REAL READS on each authenticable adapter ----
    print("\n[1] REAL READ OPERATIONS")
    for name, adapter in adapters.items():
        auth = adapter.auth_status()
        health = adapter.health()
        can_read = auth.get("authenticated", False) or auth.get("public_read_available", False) \
                   or auth.get("http_read_available", False)
        if not can_read and not health.get("healthy", False):
            print(f"  {name}: SKIPPED (not authenticable / not healthy)")
            results["real_reads"][name] = {"status": "skipped",
                                           "reason": "not authenticable or not healthy",
                                           "auth": auth}
            continue

        try:
            if name == "nextcloud":
                # Real: list top-level + read one Atlas folder
                listing = adapter.list_resources()
                print(f"  nextcloud: LISTED {listing.get('count', 0)} top-level items")
                # Read the "Atlas Vivo MILK" folder
                atlas_read = adapter.read_resource("Atlas Vivo MILK")
                results["real_reads"][name] = {
                    "status": "ok",
                    "listing_count": listing.get("count"),
                    "sample_read": {"source_id": atlas_read.get("source_id"),
                                    "content_hash": atlas_read.get("content_hash", "")[:16],
                                    "metadata": atlas_read.get("metadata", {})},
                    "auth": {k: v for k, v in auth.items() if k != "status"},
                }
                print(f"    -> read 'Atlas Vivo MILK' folder: {atlas_read.get('metadata', {}).get('item_count', '?')} items")

            elif name == "github":
                # Real: list branches + read repo info
                resources = adapter.list_resources()
                branches = resources.get("branches", [])
                print(f"  github: LISTED {len(branches)} branches")
                repo_read = adapter.read_resource("repo")
                results["real_reads"][name] = {
                    "status": "ok",
                    "branches": [b["name"] for b in branches],
                    "releases": [r.get("tag") for r in resources.get("releases", [])],
                    "open_issues": len(resources.get("open_issues", [])),
                    "sample_read_hash": repo_read.get("content_hash", "")[:16] if isinstance(repo_read, dict) else None,
                    "auth": {k: v for k, v in auth.items() if k != "status"},
                }
                print(f"    -> releases: {[r.get('tag') for r in resources.get('releases', [])]}")

            elif name == "codeberg":
                # Real: check if repo exists
                discover = adapter.discover()
                print(f"  codeberg: discovered (has_repo={discover.get('has_remote_repo')})")
                results["real_reads"][name] = {
                    "status": "ok" if discover.get("has_remote_repo") else "no_repo_found",
                    "discover": discover,
                    "auth": {k: v for k, v in auth.items() if k != "status"},
                }

            elif name == "zenodo":
                # Real: search community records (public, no auth needed)
                discover = adapter.discover()
                resources = adapter.list_resources()
                print(f"  zenodo: found {discover.get('remote_records_found', 0)} remote records, local .zenodo.json={discover.get('local_zenodo_json')}")
                results["real_reads"][name] = {
                    "status": "ok",
                    "local_zenodo_json": discover.get("local_zenodo_json"),
                    "remote_records": discover.get("remote_records", []),
                    "resource_count": resources.get("count", 0),
                    "auth": {k: v for k, v in auth.items() if k != "status"},
                }

            elif name == "orcid":
                # Real: validate ORCID via public API
                orcid_id = "0009-0007-6892-6570"  # Eduardo's ORCID
                orcid_read = adapter.read_resource(orcid_id)
                if "error" not in orcid_read:
                    meta = orcid_read.get("metadata", {})
                    print(f"  orcid: validated {orcid_id} -> {meta.get('full_name', '?')}, works={meta.get('works_count', '?')}")
                    results["real_reads"][name] = {
                        "status": "ok",
                        "orcid": orcid_id,
                        "full_name": meta.get("full_name"),
                        "works_count": meta.get("works_count"),
                        "content_hash": orcid_read.get("content_hash", "")[:16],
                        "auth": {k: v for k, v in auth.items() if k != "status"},
                    }
                else:
                    print(f"  orcid: validation returned {orcid_read.get('error')}")
                    results["real_reads"][name] = {
                        "status": "api_error",
                        "orcid": orcid_id,
                        "error": orcid_read.get("error"),
                        "auth": {k: v for k, v in auth.items() if k != "status"},
                    }

            elif name == "ptservidor":
                # Real: HTTP probe the domain
                discover = adapter.discover()
                resources = adapter.list_resources()
                print(f"  ptservidor: HTTP probe atlas.associacaomilk.pt status={discover.get('http_status')}")
                results["real_reads"][name] = {
                    "status": "ok" if discover.get("reachable") else "unreachable",
                    "domain": discover.get("domain"),
                    "http_status": discover.get("http_status"),
                    "endpoints": resources.get("resources", {}),
                    "auth": {k: v for k, v in auth.items() if k != "status"},
                }

        except Exception as e:
            print(f"  {name}: ERROR {e}")
            results["real_reads"][name] = {"status": "error", "error": str(e)}

    # ---- EXTERNAL-EVIDENCE QUERY ----
    # Query: "What cultural materials about Atlas Vivo MILK exist in external sources?"
    # Uses evidence from Nextcloud + GitHub + ORCID to build a provenance chain
    print("\n[2] EXTERNAL-EVIDENCE QUERY")
    provenance_chain = []

    # Evidence 1: Nextcloud folder listing
    nc = adapters["nextcloud"]
    nc_read = nc.read_resource("Atlas Vivo MILK")
    if "content_hash" in nc_read:
        provenance_chain.append({
            "step": 1,
            "source": "nextcloud",
            "source_id": "Atlas Vivo MILK",
            "evidence_hash": nc_read["content_hash"][:16],
            "retrieved_at": nc_read["retrieved_at"],
            "provenance": nc_read["provenance"],
            "summary": f"Nextcloud folder contains {nc_read['metadata'].get('item_count', '?')} items",
        })

    # Evidence 2: GitHub repo
    gh = adapters["github"]
    gh_read = gh.read_resource("repo")
    if "content_hash" in gh_read:
        provenance_chain.append({
            "step": 2,
            "source": "github",
            "source_id": "milkivc/atlas-vivo-milk",
            "evidence_hash": gh_read["content_hash"][:16],
            "retrieved_at": gh_read["retrieved_at"],
            "provenance": gh_read["provenance"],
            "summary": "GitHub repo metadata (mirror, not canonical)",
        })

    # Evidence 3: ORCID
    orc = adapters["orcid"]
    orc_read = orc.read_resource("0009-0007-6892-6570")
    if "content_hash" in orc_read:
        provenance_chain.append({
            "step": 3,
            "source": "orcid",
            "source_id": "0009-0007-6892-6570",
            "evidence_hash": orc_read["content_hash"][:16],
            "retrieved_at": orc_read["retrieved_at"],
            "provenance": orc_read["provenance"],
            "summary": f"ORCID validated: {orc_read['metadata'].get('full_name', '?')}, {orc_read['metadata'].get('works_count', '?')} works",
        })

    # Evidence 4: Zenodo local metadata
    zen = adapters["zenodo"]
    zen_discover = zen.discover()
    if zen_discover.get("local_zenodo_json"):
        provenance_chain.append({
            "step": 4,
            "source": "zenodo",
            "source_id": ".zenodo.json",
            "evidence_hash": "local_metadata",
            "retrieved_at": now(),
            "provenance": {"method": "local_file_read", "path": ".zenodo.json"},
            "summary": f"Local .zenodo.json metadata: {zen_discover.get('local_metadata_keys', [])}",
        })

    results["external_evidence_query"] = {
        "query": "What cultural materials and provenance exist for Atlas Vivo MILK across external sources?",
        "evidence_sources": len(provenance_chain),
        "provenance_chain": provenance_chain,
        "end_to_end_provenance": all("evidence_hash" in p and "retrieved_at" in p for p in provenance_chain),
    }
    print(f"  Provenance chain: {len(provenance_chain)} evidence sources")
    for p in provenance_chain:
        print(f"    [{p['step']}] {p['source']}:{p['source_id']} hash={p['evidence_hash']}")

    # ---- GAP GRAPH ----
    print("\n[3] ATLAS GAP GRAPH")
    engine = GapEngine(ROOT)
    gap_path = engine.save()
    graph = json.loads(gap_path.read_text(encoding="utf-8"))
    results["gap_graph"] = {
        "path": str(gap_path),
        "total_gaps": graph["total_gaps"],
        "by_severity": graph["by_severity"],
        "by_type": graph["by_type"],
    }
    print(f"  Total gaps: {graph['total_gaps']}")
    print(f"  By severity: {graph['by_severity']}")
    print(f"  By type: {graph['by_type']}")

    # ---- SAVE ----
    out_path = ROOT / "state" / "atlas_operational_proof.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[4] SAVED: {out_path}")
    print("=" * 70)
    print("OPERATIONAL PROOF COMPLETE")
    print("=" * 70)
    return results


if __name__ == "__main__":
    main()
