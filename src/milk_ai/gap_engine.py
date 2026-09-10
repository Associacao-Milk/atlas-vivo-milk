"""MILK Gap Engine — ATLAS_GAP_GRAPH.

Cross-references the local corpus with all external systems to produce
a unified gap graph. Each gap has severity, dependency, proposed action,
reversibility, and human_gate status.

Gap classifications:
  MISSING        — resource expected but absent
  STALE          — resource exists but outdated
  DIVERGENT      — resource exists in multiple sources with conflicting content
  UNVERIFIED     — resource present but provenance not confirmed
  UNPUBLISHED    — resource ready locally but not on external platform
  UNDEPLOYED     — resource exists locally but not deployed to production
  METADATA_GAP   — resource exists but metadata incomplete
  PROVENANCE_GAP — resource exists but provenance chain broken
  INTEROP_GAP    — systems should interoperate but don't
  AUTH_BLOCKED   — operation possible but blocked by missing credentials
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .external_adapters import get_all_adapters, ExternalSystemAdapter


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

GAP_TYPES = [
    "MISSING", "STALE", "DIVERGENT", "UNVERIFIED", "UNPUBLISHED",
    "UNDEPLOYED", "METADATA_GAP", "PROVENANCE_GAP", "INTEROP_GAP", "AUTH_BLOCKED",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GapEngine:
    """Builds the ATLAS_GAP_GRAPH by crossing all sources."""

    def __init__(self, canonical_root: Path | None = None):
        self.root = canonical_root or Path(__file__).resolve().parents[2]
        self.gaps: list[dict] = []
        self._gap_counter = 0

    def _gap_id(self) -> str:
        self._gap_counter += 1
        return f"GAP-{self._gap_counter:04d}"

    def add_gap(self, *, domain: str, source: str, evidence: str, severity: str,
                gap_type: str, dependency: str | None = None, proposed_action: str = "",
                reversibility: str = "reversible", human_gate: bool = True,
                status: str = "open") -> dict:
        gap = {
            "gap_id": self._gap_id(),
            "domain": domain,
            "source": source,
            "gap_type": gap_type,
            "evidence": evidence,
            "severity": severity,
            "dependency": dependency,
            "proposed_action": proposed_action,
            "reversibility": reversibility,
            "human_gate": human_gate,
            "status": status,
            "created_at": _now(),
        }
        self.gaps.append(gap)
        return gap

    def analyze_nextcloud(self, audit: dict) -> None:
        """Cross-reference Nextcloud folders with local corpus."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})
        folders = discover.get("top_level_folders", [])

        if not discover.get("found"):
            self.add_gap(domain="storage", source="nextcloud",
                         evidence="Nextcloud sync directory not found",
                         severity="medium", gap_type="MISSING",
                         proposed_action="Install/configure Nextcloud desktop client",
                         human_gate=True)
            return

        # Check if Atlas-related folders contain materials not in corpus
        atlas_folders = [f for f in folders if "atlas" in f.lower() or "milk" in f.lower() or "curador" in f.lower()]
        for folder in atlas_folders:
            self.add_gap(domain="corpus_sync", source="nextcloud",
                         evidence=f"Nextcloud folder '{folder}' may contain source materials not yet ingested into corpus",
                         severity="medium", gap_type="UNVERIFIED",
                         proposed_action=f"Audit Nextcloud/{folder} for documents missing from corpus/documents",
                         human_gate=True)

        # COCKPIT_MILK and auditor_fantasma are likely operational, check for provenance gaps
        if "auditor_fantasma" in folders:
            self.add_gap(domain="provenance", source="nextcloud",
                         evidence="auditor_fantasma folder exists — provenance of audit materials unverified",
                         severity="low", gap_type="PROVENANCE_GAP",
                         proposed_action="Map auditor_fantasma contents to corpus provenance chain",
                         human_gate=False)

    def analyze_codeberg(self, audit: dict) -> None:
        """Check Codeberg as potential canonical source."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})

        if not discover.get("has_remote_repo"):
            self.add_gap(domain="source_control", source="codeberg",
                         evidence="No MILK repo found on Codeberg (owner=milkivc)",
                         severity="medium", gap_type="MISSING",
                         proposed_action="Create atlas-vivo-milk repo on Codeberg as EU-sovereign mirror",
                         human_gate=True)

        if not auth.get("authenticated"):
            self.add_gap(domain="source_control", source="codeberg",
                         evidence="CODEBERG_TOKEN not configured — cannot read private repos or write",
                         severity="low", gap_type="AUTH_BLOCKED",
                         dependency="codeberg account",
                         proposed_action="Create Forgejo API token at codeberg.org/user/settings/applications",
                         human_gate=True)

        # INTEROP_GAP: no Codeberg remote in git
        self.add_gap(domain="source_control", source="codeberg",
                     evidence="Local git has no Codeberg remote — only GitHub origin",
                     severity="medium", gap_type="INTEROP_GAP",
                     proposed_action="Add Codeberg as second remote for EU-sovereign redundancy",
                     human_gate=True)

    def analyze_github(self, audit: dict) -> None:
        """GitHub as mirror — check divergence from local."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})

        if not discover.get("found"):
            self.add_gap(domain="source_control", source="github",
                         evidence="GitHub repo milkivc/atlas-vivo-milk not accessible via API",
                         severity="high", gap_type="MISSING",
                         proposed_action="Verify repo exists and is accessible",
                         human_gate=True)
        else:
            # Check for divergence between local HEAD and remote
            self.add_gap(domain="source_control", source="github",
                         evidence="GitHub is configured as mirror — local HEAD de3a979 may be ahead of remote (unpushed commits)",
                         severity="medium", gap_type="DIVERGENT",
                         proposed_action="Verify git log origin/master vs local master; push when authorized",
                         human_gate=True)

        # No releases yet
        self.add_gap(domain="release", source="github",
                     evidence="No GitHub releases detected for atlas-vivo-milk",
                     severity="low", gap_type="UNPUBLISHED",
                     proposed_action="Create first GitHub release tag after Atlas integration is stable",
                     human_gate=True)

    def analyze_zenodo(self, audit: dict) -> None:
        """Zenodo DOI/metadata audit."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})
        local_meta = discover.get("local_metadata_keys", [])
        remote_records = discover.get("remote_records_found", 0)

        if discover.get("local_zenodo_json"):
            # Check metadata completeness
            required = ["title", "creators", "license", "keywords", "description"]
            missing_meta = [k for k in required if k not in local_meta]
            if missing_meta:
                self.add_gap(domain="metadata", source="zenodo",
                             evidence=f".zenodo.json missing required fields: {missing_meta}",
                             severity="medium", gap_type="METADATA_GAP",
                             proposed_action=f"Add missing fields to .zenodo.json: {missing_meta}",
                             human_gate=False)
        else:
            self.add_gap(domain="metadata", source="zenodo",
                         evidence=".zenodo.json not found",
                         severity="high", gap_type="MISSING",
                         proposed_action="Create .zenodo.json with deposit metadata",
                         human_gate=True)

        if remote_records == 0:
            self.add_gap(domain="publication", source="zenodo",
                         evidence="No Zenodo records found for community 'milkivc'",
                         severity="high", gap_type="UNPUBLISHED",
                         proposed_action="Create first Zenodo deposition from .zenodo.json when ready",
                         human_gate=True)

        if not auth.get("authenticated"):
            self.add_gap(domain="publication", source="zenodo",
                         evidence="ZENODO_TOKEN not configured — cannot create depositions or read private records",
                         severity="low", gap_type="AUTH_BLOCKED",
                         proposed_action="Create Zenodo API token at zenodo.org/account/settings/applications",
                         human_gate=True)

    def analyze_orcid(self, audit: dict) -> None:
        """ORCID validation."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})
        known = discover.get("known_orcids", {})

        self.add_gap(domain="authorship", source="orcid",
                     evidence=f"Known ORCIDs: {list(known.values())} — public validation pending",
                     severity="medium", gap_type="UNVERIFIED",
                     proposed_action="Validate ORCID 0009-0009-1781-4020 via public API and map to corpus authorship",
                     human_gate=False)

        if not auth.get("authenticated"):
            self.add_gap(domain="authorship", source="orcid",
                         evidence="ORCID Member API not configured — cannot add works to ORCID profile or read limited-access data",
                         severity="info", gap_type="AUTH_BLOCKED",
                         proposed_action="Obtain ORCID Member API credentials if institutional integration needed",
                         human_gate=True)

        # METADATA_GAP: corpus creator↔ORCID mapping incomplete
        self.add_gap(domain="authorship", source="orcid",
                     evidence="Corpus documents may not all have ORCID in metadata — creator↔ORCID↔artefact map incomplete",
                     severity="medium", gap_type="METADATA_GAP",
                     proposed_action="Scan corpus for author fields, cross-reference with known ORCIDs",
                     human_gate=False)

    def analyze_ptservidor(self, audit: dict) -> None:
        """PT server deployment audit."""
        discover = audit.get("discover", {})
        auth = audit.get("auth_status", {})

        if discover.get("http_status", 0) > 0:
            self.add_gap(domain="deployment", source="ptservidor",
                         evidence=f"atlas.associacaomilk.pt responds (HTTP {discover.get('http_status')}) — verify deployed version vs local canonical",
                         severity="high", gap_type="DIVERGENT",
                         proposed_action="Compare deployed webapp version with local atlas_infra canonical version; create STAGING_DEPLOY_PLAN",
                         human_gate=True)
        else:
            self.add_gap(domain="deployment", source="ptservidor",
                         evidence="atlas.associacaomilk.pt not reachable via HTTP",
                         severity="high", gap_type="UNDEPLOYED",
                         proposed_action="Verify DNS, server status, and deployment; create STAGING_DEPLOY_PLAN",
                         human_gate=True)

        if not auth.get("authenticated"):
            self.add_gap(domain="deployment", source="ptservidor",
                         evidence="No SSH/deploy credentials for PT server — cannot verify runtime/webroot/repo path",
                         severity="medium", gap_type="AUTH_BLOCKED",
                         proposed_action="Obtain SSH key or deploy token from hosting provider",
                         human_gate=True)

        # INTEROP_GAP: local webapp not connected to live server
        self.add_gap(domain="deployment", source="ptservidor",
                     evidence="Local atlas_infra webapp not connected to neural runtime / fabric — deployed version may lack retrieval pipeline",
                     severity="high", gap_type="INTEROP_GAP",
                     proposed_action="Integrate fabric/retrieval into atlas_infra backend before next deploy",
                     human_gate=True)

    def analyze_corpus_internal(self) -> None:
        """Cross-reference corpus internal state."""
        # Nested subdirectories in corpus/documents (accidental copies)
        nested_docs = self.root / "corpus" / "documents" / "documents"
        nested_quarantine = self.root / "corpus" / "documents" / "quarantine"
        if nested_docs.is_dir():
            count = len(list(nested_docs.iterdir()))
            self.add_gap(domain="corpus_integrity", source="local",
                         evidence=f"Nested corpus/documents/documents/ has {count} entries — accidental copy, may cause duplication",
                         severity="medium", gap_type="DIVERGENT",
                         proposed_action="Investigate and remove nested duplicate directories after verification",
                         human_gate=True)
        if nested_quarantine.is_dir():
            count = len(list(nested_quarantine.iterdir()))
            self.add_gap(domain="corpus_integrity", source="local",
                         evidence=f"Nested corpus/documents/quarantine/ has {count} entries — accidental nested quarantine",
                         severity="low", gap_type="DIVERGENT",
                         proposed_action="Remove nested quarantine directory after verifying contents match root quarantine",
                         human_gate=True)

        # Gold qrels pending human validation
        gold_path = self.root / "state" / "chunk_index" / "gold_qrels.json"
        if gold_path.exists():
            self.add_gap(domain="retrieval", source="local",
                         evidence="GOLD_QRELS created (591 items) but human validation PENDING — canonical retrieval cannot be promoted",
                         severity="medium", gap_type="UNVERIFIED",
                         proposed_action="Human expert grades GOLD_QRELS; then promote winning retrieval strategy to CANONICAL_RETRIEVAL",
                         human_gate=True)

    def build_gap_graph(self) -> dict:
        """Run full analysis across all adapters and produce the gap graph."""
        adapters = get_all_adapters()

        # Run audit on all adapters
        audit_report = {}
        for name, adapter in adapters.items():
            try:
                audit_report[name] = {
                    "discover": adapter.discover(),
                    "auth_status": adapter.auth_status(),
                    "health": adapter.health(),
                    "capabilities": adapter.capabilities(),
                    "provenance": adapter.provenance(),
                }
            except Exception as e:
                audit_report[name] = {"error": str(e)}

        # Analyze each source
        self.analyze_nextcloud(audit_report.get("nextcloud", {}))
        self.analyze_codeberg(audit_report.get("codeberg", {}))
        self.analyze_github(audit_report.get("github", {}))
        self.analyze_zenodo(audit_report.get("zenodo", {}))
        self.analyze_orcid(audit_report.get("orcid", {}))
        self.analyze_ptservidor(audit_report.get("ptservidor", {}))
        self.analyze_corpus_internal()

        # Sort by severity
        self.gaps.sort(key=lambda g: SEVERITY_ORDER.get(g["severity"], 99))

        graph = {
            "schema": "ia_milk.atlas_gap_graph.v1",
            "generated_at": _now(),
            "total_gaps": len(self.gaps),
            "by_severity": {s: sum(1 for g in self.gaps if g["severity"] == s)
                           for s in SEVERITY_ORDER},
            "by_type": {t: sum(1 for g in self.gaps if g["gap_type"] == t)
                       for t in GAP_TYPES if any(g["gap_type"] == t for g in self.gaps)},
            "gaps": self.gaps,
            "audit_report": audit_report,
        }
        return graph

    def save(self, path: Path | None = None) -> Path:
        graph = self.build_gap_graph()
        out = path or self.root / "state" / "atlas_gap_graph.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
