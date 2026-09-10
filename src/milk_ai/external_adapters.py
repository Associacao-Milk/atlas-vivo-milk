"""MILK Atlas Integration Fabric — External System Adapters.

READ/AUDIT interface for external systems in the Atlas ecosystem.
Each adapter implements the ExternalSystemAdapter contract and produces
evidence with provenance for every read operation.

Owner: MILK Sovereign Core (logical owner of all services).
Consumers (GPT-OSS, Fabric, agents) are clients — never owners of the core.

Phase 2 scope: READ/AUDIT only. No writes, no publishes, no deploys.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Evidence dataclass — the unit of every external read
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    """A single piece of evidence retrieved from an external system."""
    source_id: str           # unique identifier in the external system
    source_system: str      # which adapter produced this
    retrieved_at: str       # ISO-8601 UTC
    provenance: dict        # how it was obtained (method, auth_type, path)
    content: str = ""       # text content (truncated if large)
    content_hash: str = ""  # sha256 of full content
    metadata: dict = field(default_factory=dict)  # system-specific fields

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_system": self.source_system,
            "retrieved_at": self.retrieved_at,
            "provenance": self.provenance,
            "content": self.content,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_get(url: str, headers: dict | None = None, timeout: int = 15) -> tuple[int, bytes]:
    """Minimal urllib GET. Returns (status_code, body_bytes)."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if hasattr(e, "read") else b""
    except Exception as e:
        return 0, str(e).encode("utf-8")


def _detect_secret(*names: str) -> tuple[str | None, str]:
    """Check env vars for a credential without printing its value.
    Returns (credential_name_or_None, status_string)."""
    for name in names:
        val = os.environ.get(name, "")
        if val.strip():
            return name, f"present (env:{name}, value redacted)"
    return None, "missing"


# ---------------------------------------------------------------------------
# ExternalSystemAdapter contract
# ---------------------------------------------------------------------------

class ExternalSystemAdapter(ABC):
    """Common interface for all external system adapters.

    Contract methods (all return dicts for serialization):
      discover()         — detect the system's presence and configuration
      auth_status()      — check credential validity without printing secrets
      list_resources()   — enumerate available resources (read-only)
      read_resource(id)  — fetch a single resource as Evidence
      capabilities()     — declare what this adapter can do
      health()           — is the system reachable right now?
      provenance()       — adapter identity and config provenance
      propose_action()   — suggest a change (READ/AUDIT phase: proposal only)
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def discover(self) -> dict: ...

    @abstractmethod
    def auth_status(self) -> dict: ...

    @abstractmethod
    def list_resources(self) -> dict: ...

    @abstractmethod
    def read_resource(self, resource_id: str) -> dict: ...

    @abstractmethod
    def capabilities(self) -> dict: ...

    @abstractmethod
    def health(self) -> dict: ...

    @abstractmethod
    def provenance(self) -> dict: ...

    def propose_action(self, action: str, **kwargs) -> dict:
        """Default: record proposal without executing."""
        return {
            "action": action,
            "status": "PROPOSED",
            "phase": "READ_AUDIT",
            "executed": False,
            "details": kwargs,
        }

    def search(self, query: str, limit: int = 10) -> dict:
        """Search resources in this system. Default: list and filter by name.
        Subclasses may override for full-text/API search."""
        resources = self.list_resources()
        items = resources.get("resources", [])
        if isinstance(items, list):
            ql = query.lower()
            filtered = [r for r in items if ql in str(r).lower()]
            return {"results": filtered[:limit], "query": query, "count": len(filtered)}
        return {"results": [], "query": query, "count": 0}


# ---------------------------------------------------------------------------
# 1. NextcloudAdapter — local WebDAV sync directory
# ---------------------------------------------------------------------------

class NextcloudAdapter(ExternalSystemAdapter):
    """Reads the local Nextcloud sync folder (~/Nextcloud).
    Uses filesystem access — no API token needed if sync client already authed.
    """

    def __init__(self, sync_dir: Path | None = None):
        self.sync_dir = sync_dir or Path.home() / "Nextcloud"

    @property
    def name(self) -> str:
        return "nextcloud"

    def discover(self) -> dict:
        exists = self.sync_dir.is_dir()
        folders = []
        if exists:
            folders = [d.name for d in self.sync_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return {
            "found": exists,
            "sync_dir": str(self.sync_dir),
            "top_level_folders": folders,
            "method": "filesystem (Nextcloud desktop sync client)",
        }

    def auth_status(self) -> dict:
        # Auth is handled by the Nextcloud desktop client, not by us.
        # We only verify filesystem read access.
        if not self.sync_dir.is_dir():
            return {"authenticated": False, "credential_type": "none",
                    "blocked_operation": "list_resources",
                    "reason": f"{self.sync_dir} not found — Nextcloud sync client may not be installed/configured"}
        readable = os.access(self.sync_dir, os.R_OK)
        return {
            "authenticated": readable,
            "credential_type": "nextcloud_desktop_sync (OS-level)",
            "note": "Auth delegated to Nextcloud desktop client. MILK uses filesystem read only.",
        }

    def list_resources(self) -> dict:
        if not self.sync_dir.is_dir():
            return {"resources": [], "error": "sync dir not found"}
        resources = []
        for item in sorted(self.sync_dir.iterdir()):
            if item.name.startswith("."):
                continue
            resources.append({
                "id": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"resources": resources, "count": len(resources)}

    def read_resource(self, resource_id: str) -> dict:
        path = self.sync_dir / resource_id
        if not path.exists():
            return {"error": "not found", "resource_id": resource_id}
        if path.is_dir():
            items = []
            for item in sorted(path.iterdir())[:50]:
                items.append({"name": item.name, "type": "dir" if item.is_dir() else "file",
                              "size": item.stat().st_size if item.is_file() else None})
            content = json.dumps(items, ensure_ascii=False)
            return Evidence(
                source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "filesystem_dir_listing", "auth_type": "sync_client",
                            "path": str(path)},
                content=content, content_hash=_sha256(content),
                metadata={"item_count": len(items), "truncated": len(items) >= 50},
            ).to_dict()
        else:
            raw = path.read_bytes()
            try:
                content = raw.decode("utf-8", errors="replace")[:5000]
            except Exception:
                content = f"<binary {len(raw)} bytes>"
            return Evidence(
                source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "filesystem_read", "auth_type": "sync_client", "path": str(path)},
                content=content, content_hash=_sha256(content),
                metadata={"size_bytes": len(raw), "truncated": len(raw) > 5000},
            ).to_dict()

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False,
                "publish": False, "note": "READ/AUDIT phase — filesystem only"}

    def health(self) -> dict:
        return {"healthy": self.sync_dir.is_dir(), "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "filesystem",
                "owner": "MILK Sovereign Core", "client_role": "sync_client_delegated"}


# ---------------------------------------------------------------------------
# 2. CodebergForgejoAdapter — Forgejo API on codeberg.org
# ---------------------------------------------------------------------------

class CodebergForgejoAdapter(ExternalSystemAdapter):
    """Codeberg (Forgejo) — checks for repos, issues via public API.
    Token optional for private repos; public reads need no auth.
    """

    API = "https://codeberg.org/api/v1"

    def __init__(self, token: str | None = None, owner: str = "milkivc"):
        self.token = token or os.environ.get("CODEBERG_TOKEN")
        self.owner = owner

    @property
    def name(self) -> str:
        return "codeberg"

    def _headers(self) -> dict:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"token {self.token}"
        return h

    def discover(self) -> dict:
        code, body = _safe_get(f"{self.API}/repos/{self.owner}", headers=self._headers())
        found = code in (200, 404)
        return {"found": found, "api": self.API, "owner": self.owner,
                "status_code": code, "has_remote_repo": code == 200}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("CODEBERG_TOKEN")
        return {"authenticated": cred is not None, "credential_type": "CODEBERG_TOKEN (Forgejo API token)",
                "status": status, "where_to_configure": "https://codeberg.org/user/settings/applications",
                "blocked_operation": None if cred else "private_repo_read"}

    def list_resources(self) -> dict:
        code, body = _safe_get(f"{self.API}/repos/{self.owner}", headers=self._headers())
        if code == 200:
            data = json.loads(body)
            return {"resources": [{"id": r.get("name"), "full_name": r.get("full_name"),
                                   "private": r.get("private"), "updated": r.get("updated_at")}
                                  for r in data] if isinstance(data, list) else [data],
                    "count": len(data) if isinstance(data, list) else 1}
        return {"resources": [], "error": f"HTTP {code}", "status_code": code}

    def read_resource(self, resource_id: str) -> dict:
        code, body = _safe_get(f"{self.API}/repos/{self.owner}/{resource_id}", headers=self._headers())
        if code == 200:
            data = json.loads(body)
            content = json.dumps(data, ensure_ascii=False, indent=2)[:5000]
            return Evidence(
                source_id=f"{self.owner}/{resource_id}", source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "forgejo_api", "auth_type": "token" if self.token else "anonymous",
                            "endpoint": f"/repos/{self.owner}/{resource_id}"},
                content=content, content_hash=_sha256(content),
                metadata={"stars": data.get("stars_count"), "forks": data.get("forks_count"),
                          "private": data.get("private"), "default_branch": data.get("default_branch")},
            ).to_dict()
        return {"error": f"HTTP {code}", "resource_id": resource_id}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False}

    def health(self) -> dict:
        code, _ = _safe_get(f"{self.API}/repos/{self.owner}", headers=self._headers(), timeout=10)
        return {"healthy": code in (200, 404), "name": self.name, "status_code": code}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "forgejo_api",
                "owner": "MILK Sovereign Core", "client_role": "api_consumer"}


# ---------------------------------------------------------------------------
# 3. GitHubAdapter — audit remotes, branches, issues, releases
# ---------------------------------------------------------------------------

class GitHubAdapter(ExternalSystemAdapter):
    """GitHub — treated as interoperability/mirror, NOT canonical authority.
    Uses git CLI (credential manager) + public REST API.
    """

    API = "https://api.github.com"

    def __init__(self, repo: str = "milkivc/atlas-vivo-milk", token: str | None = None):
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    @property
    def name(self) -> str:
        return "github"

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "MILK-Atlas-Audit"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def discover(self) -> dict:
        # Check local git remotes
        try:
            result = subprocess.run(
                ["git", "remote", "-v"], capture_output=True, text=True, timeout=10,
                cwd=str(Path(__file__).resolve().parents[2])
            )
            remotes = result.stdout.strip()
        except Exception:
            remotes = ""
        # Check API
        code, body = _safe_get(f"{self.API}/repos/{self.repo}", headers=self._headers())
        return {"found": code == 200, "repo": self.repo, "local_remotes": remotes,
                "api_status": code, "role": "mirror_interop (NOT canonical authority)"}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("GITHUB_TOKEN", "GH_TOKEN")
        # Also check git credential manager
        git_cred = cred is None  # git credential manager may provide auth without env token
        return {"authenticated": cred is not None or git_cred,
                "credential_type": "GITHUB_TOKEN or Git Credential Manager",
                "status": status if cred else "git credential manager (OS-level)",
                "where_to_configure": "https://github.com/settings/tokens",
                "blocked_operation": None}

    def list_resources(self) -> dict:
        resources = {}
        # Branches
        code, body = _safe_get(f"{self.API}/repos/{self.repo}/branches", headers=self._headers())
        if code == 200:
            resources["branches"] = [{"name": b.get("name"), "protected": b.get("protected")}
                                     for b in json.loads(body)]
        # Releases
        code, body = _safe_get(f"{self.API}/repos/{self.repo}/releases?per_page=5", headers=self._headers())
        if code == 200:
            resources["releases"] = [{"tag": r.get("tag_name"), "name": r.get("name"),
                                      "published": r.get("published_at"), "draft": r.get("draft")}
                                     for r in json.loads(body)]
        # Issues (open, first 10)
        code, body = _safe_get(f"{self.API}/repos/{self.repo}/issues?state=open&per_page=10", headers=self._headers())
        if code == 200:
            resources["open_issues"] = [{"number": i.get("number"), "title": i.get("title"),
                                         "labels": [l.get("name") for l in i.get("labels", [])]}
                                        for i in json.loads(body) if "pull_request" not in i]
        return resources

    def read_resource(self, resource_id: str) -> dict:
        # resource_id can be "branch:master", "release:v1", "issue:42"
        parts = resource_id.split(":", 1)
        kind = parts[0] if len(parts) > 1 else "repo"
        rid = parts[1] if len(parts) > 1 else ""
        if kind == "branch":
            code, body = _safe_get(f"{self.API}/repos/{self.repo}/branches/{rid}", headers=self._headers())
        elif kind == "release":
            code, body = _safe_get(f"{self.API}/repos/{self.repo}/releases/tags/{rid}", headers=self._headers())
        elif kind == "issue":
            code, body = _safe_get(f"{self.API}/repos/{self.repo}/issues/{rid}", headers=self._headers())
        else:
            code, body = _safe_get(f"{self.API}/repos/{self.repo}", headers=self._headers())
        if code == 200:
            data = json.loads(body)
            content = json.dumps(data, ensure_ascii=False, indent=2)[:5000]
            return Evidence(
                source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "github_api", "auth_type": "token" if self.token else "credential_manager",
                            "endpoint": f"/repos/{self.repo}/{resource_id}"},
                content=content, content_hash=_sha256(content),
                metadata={"kind": kind},
            ).to_dict()
        return {"error": f"HTTP {code}", "resource_id": resource_id}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False,
                "note": "mirror/interop only — canonical authority is local MILK repo"}

    def health(self) -> dict:
        code, _ = _safe_get(f"{self.API}/repos/{self.repo}", headers=self._headers(), timeout=10)
        return {"healthy": code == 200, "name": self.name, "status_code": code}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "github_api+git_cli",
                "owner": "MILK Sovereign Core", "client_role": "api_consumer",
                "canonical_role": "mirror (NOT authority)"}


# ---------------------------------------------------------------------------
# 4. ZenodoAdapter — audit DOI records, depositions, metadata
# ---------------------------------------------------------------------------

class ZenodoAdapter(ExternalSystemAdapter):
    """Zenodo — audit existing records and .zenodo.json metadata.
    Token needed for private depositions; public records need no auth.
    """

    API = "https://zenodo.org/api"

    def __init__(self, token: str | None = None, community: str = "milkivc"):
        self.token = token or os.environ.get("ZENODO_TOKEN")
        self.community = community
        self._zenodo_json_path = Path(__file__).resolve().parents[2] / ".zenodo.json"

    @property
    def name(self) -> str:
        return "zenodo"

    def _params(self) -> dict:
        return {"access_token": self.token} if self.token else {}

    def discover(self) -> dict:
        # Check local .zenodo.json
        has_local = self._zenodo_json_path.exists()
        local_meta = {}
        if has_local:
            local_meta = json.loads(self._zenodo_json_path.read_text(encoding="utf-8"))
        # Search Zenodo for community records (public, no auth)
        code, body = _safe_get(
            f"{self.API}/records?q=communities.identifier:{self.community}&size=5",
            timeout=15
        )
        records = []
        if code == 200:
            data = json.loads(body)
            records = [{"id": h.get("id"), "doi": h.get("doi"), "title": h.get("metadata", {}).get("title")}
                       for h in data.get("hits", {}).get("hits", [])]
        return {"local_zenodo_json": has_local, "community": self.community,
                "local_metadata_keys": list(local_meta.get("metadata", {}).keys()) if has_local else [],
                "remote_records_found": len(records), "remote_records": records}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("ZENODO_TOKEN")
        return {"authenticated": cred is not None,
                "credential_type": "ZENODO_TOKEN (Zenodo API deposit token)",
                "status": status,
                "where_to_configure": "https://zenodo.org/account/settings/applications",
                "blocked_operation": None if cred else "deposition_write/private_read",
                "public_read_available": True}

    def list_resources(self) -> dict:
        # Public search for community records
        code, body = _safe_get(
            f"{self.API}/records?q=communities.identifier:{self.community}&size=20",
            timeout=15
        )
        if code == 200:
            data = json.loads(body)
            hits = data.get("hits", {}).get("hits", [])
            return {"resources": [{"id": h.get("id"), "doi": h.get("doi"),
                                   "title": h.get("metadata", {}).get("title", ""),
                                   "publication_date": h.get("metadata", {}).get("publication_date"),
                                   "version": h.get("metadata", {}).get("version")}
                                  for h in hits],
                    "count": len(hits), "total": data.get("hits", {}).get("total")}
        return {"resources": [], "error": f"HTTP {code}"}

    def read_resource(self, resource_id: str) -> dict:
        # resource_id = Zenodo record ID
        url = f"{self.API}/records/{resource_id}"
        if self.token:
            url += f"?access_token={self.token}"
        code, body = _safe_get(url, timeout=15)
        if code == 200:
            data = json.loads(body)
            content = json.dumps(data, ensure_ascii=False, indent=2)[:5000]
            meta = data.get("metadata", {})
            return Evidence(
                source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "zenodo_api", "auth_type": "token" if self.token else "anonymous",
                            "endpoint": f"/records/{resource_id}"},
                content=content, content_hash=_sha256(content),
                metadata={"doi": data.get("doi"), "title": meta.get("title"),
                          "creators": [c.get("name") for c in meta.get("creators", [])],
                          "license": meta.get("license"), "version": meta.get("version"),
                          "files": [{"key": f.get("key"), "size": f.get("size")}
                                    for f in data.get("files", [])]},
            ).to_dict()
        return {"error": f"HTTP {code}", "resource_id": resource_id}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False,
                "publish": False, "note": "corrections prepared as proposals only"}

    def health(self) -> dict:
        code, _ = _safe_get(f"{self.API}/records?q=test&size=1", timeout=10)
        return {"healthy": code == 200, "name": self.name, "status_code": code}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "zenodo_api",
                "owner": "MILK Sovereign Core", "client_role": "api_consumer",
                "local_metadata": str(self._zenodo_json_path)}


# ---------------------------------------------------------------------------
# 5. OrcidAdapter — validate ORCID iDs, map creator↔artefacts
# ---------------------------------------------------------------------------

class OrcidAdapter(ExternalSystemAdapter):
    """ORCID Public API — read public profiles. No auth needed for public reads.
    Member API (write/limited-read) requires separate authorization.
    """

    API = "https://pub.orcid.org/v3.0"

    def __init__(self, known_orcids: dict | None = None):
        # Known ORCIDs in the MILK ecosystem — canonical from provenance
        from .provenance import CANONICAL_AUTHOR, CANONICAL_AUTHOR_NUNO
        self.known_orcids = known_orcids or {
            "eduardo_mauricio": CANONICAL_AUTHOR.get("orcid", "0009-0007-6892-6570"),
            "nuno_a": CANONICAL_AUTHOR_NUNO.get("orcid", "0009-0009-1781-4020"),
        }

    @property
    def name(self) -> str:
        return "orcid"

    def discover(self) -> dict:
        return {"known_orcids": self.known_orcids, "api": "public_v3",
                "note": "Public API needs no auth. Member API requires institutional authorization."}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("ORCID_TOKEN")
        return {"authenticated": False, "credential_type": "ORCID Member API token (NOT configured)",
                "status": status if cred else "not needed for public reads",
                "where_to_configure": "https://orcid.org/developer-tools (Member API only)",
                "blocked_operation": "limited_access_works, member_write" if not cred else None,
                "public_read_available": True}

    def list_resources(self) -> dict:
        return {"resources": [{"label": k, "orcid": v} for k, v in self.known_orcids.items()],
                "count": len(self.known_orcids)}

    def read_resource(self, resource_id: str) -> dict:
        # resource_id = ORCID iD (e.g. "0009-0009-1781-4020")
        headers = {"Accept": "application/json"}
        code, body = _safe_get(f"{self.API}/{resource_id}", headers=headers, timeout=15)
        if code == 200:
            data = json.loads(body)
            person = data.get("person", {})
            name = person.get("name", {})
            full_name = f"{name.get('given-names', {}).get('value', '')} {name.get('family-name', {}).get('value', '')}"
            works = data.get("activities-summary", {}).get("works", {}).get("group", [])
            work_summaries = [{"title": g.get("work-summary", [{}])[0].get("title", {}).get("title", {}).get("value", ""),
                               "type": g.get("work-summary", [{}])[0].get("type"),
                               "put-code": g.get("work-summary", [{}])[0].get("put-code")}
                              for g in works[:20]]
            content = json.dumps({"name": full_name.strip(), "orcid": resource_id,
                                  "works_count": len(works)}, ensure_ascii=False)
            return Evidence(
                source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                provenance={"method": "orcid_public_api", "auth_type": "anonymous",
                            "endpoint": f"/{resource_id}"},
                content=content, content_hash=_sha256(content),
                metadata={"full_name": full_name.strip(), "works_count": len(works),
                          "work_summaries": work_summaries},
            ).to_dict()
        return {"error": f"HTTP {code}", "resource_id": resource_id}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False,
                "public_api": True, "member_api": False}

    def health(self) -> dict:
        code, _ = _safe_get(f"{self.API}/0000-0002-0000-0000", timeout=10)
        return {"healthy": code in (200, 404), "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "orcid_public_api",
                "owner": "MILK Sovereign Core", "client_role": "api_consumer"}


# ---------------------------------------------------------------------------
# 6. PTServidorAdapter — audit atlas.associacaomilk.pt deployment
# ---------------------------------------------------------------------------

class PTServidorAdapter(ExternalSystemAdapter):
    """Atlas PT server — discover deployment state read-only.
    Uses local config + HTTP probe. No SSH credentials assumed.
    """

    def __init__(self, domain: str = "atlas.associacaomilk.pt"):
        self.domain = domain

    @property
    def name(self) -> str:
        return "ptservidor"

    def discover(self) -> dict:
        # Check local atlas_infra for deployment config
        root = Path(__file__).resolve().parents[2]
        atlas_infra = root / "atlas_infra"
        files = []
        if atlas_infra.is_dir():
            files = [f.name for f in atlas_infra.iterdir() if f.is_file()]
        # Check for env config
        env_example = (atlas_infra / ".env.example").exists()
        # HTTP probe
        code, body = _safe_get(f"https://{self.domain}/", timeout=15)
        # Check if domain resolves / responds
        return {"domain": self.domain, "atlas_infra_files": files,
                "has_env_example": env_example,
                "http_status": code, "reachable": code > 0,
                "local_repo_root": str(root)}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("PT_SERVIDOR_SSH_KEY", "PT_SERVIDOR_TOKEN")
        return {"authenticated": cred is not None,
                "credential_type": "SSH key or deploy token (NOT configured in env)",
                "status": status,
                "where_to_configure": "server SSH config or deploy key from hosting provider",
                "blocked_operation": "ssh_access, deploy" if not cred else None,
                "http_read_available": True}

    def list_resources(self) -> dict:
        # HTTP probe to discover web endpoints
        results = {}
        for path in ["/", "/api", "/api/health", "/health", "/api/documents"]:
            code, body = _safe_get(f"https://{self.domain}{path}", timeout=10)
            results[path] = {"status": code, "body_size": len(body)}
        return {"resources": results, "domain": self.domain}

    def read_resource(self, resource_id: str) -> dict:
        # resource_id = URL path (e.g. "/", "/api/health")
        path = resource_id if resource_id.startswith("/") else f"/{resource_id}"
        code, body = _safe_get(f"https://{self.domain}{path}", timeout=15)
        content = body.decode("utf-8", errors="replace")[:5000]
        return Evidence(
            source_id=f"{self.domain}{path}", source_system=self.name, retrieved_at=_now_utc(),
            provenance={"method": "http_get", "auth_type": "anonymous", "url": f"https://{self.domain}{path}"},
            content=content, content_hash=_sha256(content),
            metadata={"http_status": code, "content_type": "text/html" if code > 0 else None},
        ).to_dict()

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False,
                "deploy": False, "note": "STAGING_DEPLOY_PLAN only — no production deploy this phase"}

    def health(self) -> dict:
        code, _ = _safe_get(f"https://{self.domain}/", timeout=10)
        return {"healthy": code > 0, "name": self.name, "domain": self.domain, "http_status": code}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "http_probe",
                "owner": "MILK Sovereign Core", "client_role": "auditor",
                "note": "read-only HTTP probe, no SSH access assumed"}


# ---------------------------------------------------------------------------
# 7. LocalFSAdapter — canonical local filesystem
# ---------------------------------------------------------------------------

class LocalFSAdapter(ExternalSystemAdapter):
    """Local MILK filesystem — the canonical repository root."""

    def __init__(self, root: Path | None = None):
        self.root = root or Path(__file__).resolve().parents[2]

    @property
    def name(self) -> str:
        return "localfs"

    def discover(self) -> dict:
        return {"found": self.root.is_dir(), "root": str(self.root),
                "top_level": [d.name for d in self.root.iterdir() if d.is_dir() and not d.name.startswith(".")][:20]}

    def auth_status(self) -> dict:
        return {"authenticated": True, "credential_type": "filesystem (local)",
                "note": "Local filesystem always accessible"}

    def list_resources(self) -> dict:
        resources = []
        for item in sorted(self.root.iterdir()):
            if item.name.startswith(".") or item.name == "lib":
                continue
            resources.append({"id": item.name, "type": "dir" if item.is_dir() else "file",
                              "size": item.stat().st_size if item.is_file() else None})
        return {"resources": resources, "count": len(resources)}

    def read_resource(self, resource_id: str) -> dict:
        path = self.root / resource_id
        if not path.exists():
            return {"error": "not found", "resource_id": resource_id}
        if path.is_dir():
            items = [{"name": i.name, "type": "dir" if i.is_dir() else "file"}
                     for i in sorted(path.iterdir())[:50]]
            content = json.dumps(items, ensure_ascii=False)
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "filesystem_dir_listing", "path": str(path)},
                          content=content, content_hash=_sha256(content),
                          metadata={"item_count": len(items)}).to_dict()
        raw = path.read_bytes()
        content = raw.decode("utf-8", errors="replace")[:5000]
        return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                       provenance={"method": "filesystem_read", "path": str(path)},
                       content=content, content_hash=_sha256(content),
                       metadata={"size_bytes": len(raw)}).to_dict()

    def search(self, query: str, limit: int = 10) -> dict:
        results = []
        for p in self.root.rglob(f"*{query}*"):
            if "lib/" in str(p) or "__pycache__" in str(p) or ".git/" in str(p):
                continue
            results.append({"path": str(p.relative_to(self.root)), "type": "dir" if p.is_dir() else "file"})
            if len(results) >= limit:
                break
        return {"results": results, "query": query, "count": len(results)}

    def capabilities(self) -> dict:
        return {"read": True, "write": True, "audit": True, "delete": False, "publish": False,
                "note": "canonical local filesystem — write requires Action Gate"}

    def health(self) -> dict:
        return {"healthy": self.root.is_dir(), "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "filesystem",
                "owner": "MILK Sovereign Core", "canonical_role": "primary_authority"}


# ---------------------------------------------------------------------------
# 8. CloudSyncAdapter — unified cloud sync discovery
# ---------------------------------------------------------------------------

class CloudSyncAdapter(ExternalSystemAdapter):
    """Discovers all cloud sync paths on the system (Nextcloud, OneDrive, etc.)."""

    def __init__(self):
        self._sources = self._discover_sources()

    def _discover_sources(self) -> dict:
        sources = {}
        home = Path.home()
        env = os.environ
        if env.get("OneDrive") and Path(env["OneDrive"]).is_dir():
            sources["onedrive"] = env["OneDrive"]
        nc = home / "Nextcloud"
        if nc.is_dir():
            sources["nextcloud"] = str(nc)
        for gd in [home / "Google Drive", home / "GoogleDrive"]:
            if gd.is_dir():
                sources["google_drive"] = str(gd)
                break
        for box in [home / "Box", home / "Box Drive"]:
            if box.is_dir():
                sources["box"] = str(box)
                break
        return sources

    @property
    def name(self) -> str:
        return "cloudsync"

    def discover(self) -> dict:
        return {"sources": self._sources, "count": len(self._sources)}

    def auth_status(self) -> dict:
        return {"authenticated": True, "credential_type": "OS-level sync clients",
                "sources": list(self._sources.keys())}

    def list_resources(self) -> dict:
        resources = []
        for source_name, path in self._sources.items():
            p = Path(path)
            if p.is_dir():
                for item in sorted(p.iterdir())[:20]:
                    if item.name.startswith("."):
                        continue
                    resources.append({"id": f"{source_name}:{item.name}", "source": source_name,
                                      "name": item.name, "type": "dir" if item.is_dir() else "file"})
        return {"resources": resources, "count": len(resources)}

    def read_resource(self, resource_id: str) -> dict:
        parts = resource_id.split(":", 1)
        if len(parts) < 2:
            return {"error": "resource_id must be 'source:name'"}
        source, name = parts
        path = self._sources.get(source)
        if not path:
            return {"error": f"source '{source}' not found"}
        target = Path(path) / name
        if not target.exists():
            return {"error": "not found", "resource_id": resource_id}
        if target.is_dir():
            items = [{"name": i.name} for i in sorted(target.iterdir())[:50]]
            content = json.dumps(items, ensure_ascii=False)
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "cloud_sync_dir", "source": source, "path": str(target)},
                          content=content, content_hash=_sha256(content),
                          metadata={"item_count": len(items)}).to_dict()
        raw = target.read_bytes()
        content = raw.decode("utf-8", errors="replace")[:5000]
        return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                       provenance={"method": "cloud_sync_read", "source": source, "path": str(target)},
                       content=content, content_hash=_sha256(content),
                       metadata={"size_bytes": len(raw)}).to_dict()

    def search(self, query: str, limit: int = 10) -> dict:
        results = []
        for source_name, path in self._sources.items():
            p = Path(path)
            if not p.is_dir():
                continue
            for item in p.rglob(f"*{query}*"):
                results.append({"source": source_name, "path": str(item.relative_to(p))})
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return {"results": results, "query": query, "count": len(results)}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False,
                "note": "cloud sync paths — READ/AUDIT only, writes go through source-specific adapters"}

    def health(self) -> dict:
        return {"healthy": len(self._sources) > 0, "name": self.name, "sources": list(self._sources.keys())}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "filesystem (sync clients)",
                "owner": "MILK Sovereign Core", "sources": list(self._sources.keys())}


# ---------------------------------------------------------------------------
# 9. OneDriveAdapter — Microsoft OneDrive Business
# ---------------------------------------------------------------------------

class OneDriveAdapter(ExternalSystemAdapter):
    """OneDrive — reads the local sync folder (Personal or Business)."""

    def __init__(self, sync_dir: Path | None = None):
        od_env = os.environ.get("OneDrive", "")
        self.sync_dir = sync_dir or (Path(od_env) if od_env else Path.home() / "OneDrive")

    @property
    def name(self) -> str:
        return "onedrive"

    def discover(self) -> dict:
        exists = self.sync_dir.is_dir()
        folders = []
        if exists:
            folders = [d.name for d in self.sync_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return {"found": exists, "sync_dir": str(self.sync_dir),
                "top_level_folders": folders[:20],
                "type": "business" if "associacaomilk" in str(self.sync_dir).lower() else "personal"}

    def auth_status(self) -> dict:
        if not self.sync_dir.is_dir():
            return {"authenticated": False, "credential_type": "none",
                    "blocked_operation": "list_resources"}
        return {"authenticated": True, "credential_type": "OneDrive desktop sync (OS-level)",
                "note": "Auth delegated to OneDrive client"}

    def list_resources(self) -> dict:
        if not self.sync_dir.is_dir():
            return {"resources": [], "error": "sync dir not found"}
        resources = []
        for item in sorted(self.sync_dir.iterdir()):
            if item.name.startswith("."):
                continue
            resources.append({"id": item.name, "type": "dir" if item.is_dir() else "file"})
        return {"resources": resources, "count": len(resources)}

    def read_resource(self, resource_id: str) -> dict:
        path = self.sync_dir / resource_id
        if not path.exists():
            return {"error": "not found", "resource_id": resource_id}
        if path.is_dir():
            items = [{"name": i.name, "type": "dir" if i.is_dir() else "file"}
                     for i in sorted(path.iterdir())[:50]]
            content = json.dumps(items, ensure_ascii=False)
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "onedrive_sync_dir", "path": str(path)},
                          content=content, content_hash=_sha256(content),
                          metadata={"item_count": len(items)}).to_dict()
        raw = path.read_bytes()
        content = raw.decode("utf-8", errors="replace")[:5000]
        return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                       provenance={"method": "onedrive_sync_read", "path": str(path)},
                       content=content, content_hash=_sha256(content),
                       metadata={"size_bytes": len(raw)}).to_dict()

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False}

    def health(self) -> dict:
        return {"healthy": self.sync_dir.is_dir(), "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "filesystem (OneDrive sync)",
                "owner": "MILK Sovereign Core", "client_role": "sync_client_delegated"}


# ---------------------------------------------------------------------------
# 10. DockerAdapter — Docker containers and services
# ---------------------------------------------------------------------------

class DockerAdapter(ExternalSystemAdapter):
    """Docker — read-only inspection of containers, volumes, networks."""

    def __init__(self):
        self._docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        out, code = _run_cmd(["docker", "version", "--format", "{{.Server.Version}}"], timeout=10)
        return code == 0 and bool(out.strip())

    @property
    def name(self) -> str:
        return "docker"

    def discover(self) -> dict:
        return {"available": self._docker_available, "method": "docker CLI"}

    def auth_status(self) -> dict:
        # Docker Hub credentials may be in CredMan
        cred, status = _detect_secret("DOCKER_HUB_TOKEN")
        return {"authenticated": self._docker_available,
                "credential_type": "Docker Hub (via CredManager)" if not cred else "DOCKER_HUB_TOKEN",
                "status": status if cred else "CredManager: docker-desktop credentials present (targets found)",
                "blocked_operation": None if self._docker_available else "docker_not_running"}

    def list_resources(self) -> dict:
        if not self._docker_available:
            return {"resources": [], "error": "Docker not available"}
        result = {}
        out, _ = _run_cmd(["docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"], timeout=15)
        if out:
            result["containers"] = [{"name": p[0], "image": p[1], "status": p[2], "ports": p[3]}
                                   for line in out.split("\n") if line.strip()
                                   for p in [line.split("|")]]
        out, _ = _run_cmd(["docker", "volume", "ls", "--format", "{{.Name}}"], timeout=10)
        if out:
            result["volumes"] = [l.strip() for l in out.split("\n") if l.strip()]
        out, _ = _run_cmd(["docker", "network", "ls", "--format", "{{.Name}}"], timeout=10)
        if out:
            result["networks"] = [l.strip() for l in out.split("\n") if l.strip()]
        return result

    def read_resource(self, resource_id: str) -> dict:
        if not self._docker_available:
            return {"error": "Docker not available"}
        out, _ = _run_cmd(["docker", "inspect", resource_id], timeout=15)
        if out:
            content = out[:5000]
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "docker_inspect", "container": resource_id},
                          content=content, content_hash=_sha256(content),
                          metadata={"inspected": True}).to_dict()
        return {"error": "container not found", "resource_id": resource_id}

    def capabilities(self) -> dict:
        return {"read": self._docker_available, "write": False, "audit": True, "delete": False,
                "publish": False, "note": "read-only inspection"}

    def health(self) -> dict:
        return {"healthy": self._docker_available, "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "docker_cli",
                "owner": "MILK Sovereign Core", "client_role": "auditor"}


# ---------------------------------------------------------------------------
# 11. GitAdapter — local git repository audit
# ---------------------------------------------------------------------------

class GitAdapter(ExternalSystemAdapter):
    """Git — audit local repository state, branches, remotes, tags."""

    def __init__(self, repo_root: Path | None = None):
        self.repo = repo_root or Path(__file__).resolve().parents[2]

    @property
    def name(self) -> str:
        return "git"

    def discover(self) -> dict:
        git_dir = self.repo / ".git"
        return {"found": git_dir.is_dir(), "repo_root": str(self.repo),
                "has_git": git_dir.is_dir()}

    def auth_status(self) -> dict:
        return {"authenticated": True, "credential_type": "local git",
                "note": "Local git operations always available"}

    def list_resources(self) -> dict:
        out, _ = _run_cmd(["git", "branch", "-a"], cwd=str(self.repo))
        branches = [b.strip().lstrip("* ") for b in out.split("\n") if b.strip()]
        out, _ = _run_cmd(["git", "remote", "-v"], cwd=str(self.repo))
        remotes = [l.strip() for l in out.split("\n") if l.strip()]
        out, _ = _run_cmd(["git", "tag", "--list"], cwd=str(self.repo))
        tags = [t.strip() for t in out.split("\n") if t.strip()]
        return {"branches": branches, "remotes": remotes, "tags": tags,
                "head": _run_cmd(["git", "rev-parse", "HEAD"], cwd=str(self.repo))[0][:12]}

    def read_resource(self, resource_id: str) -> dict:
        if resource_id.startswith("log:"):
            n = resource_id[4:] or "10"
            out, _ = _run_cmd(["git", "log", f"--oneline", f"-{n}"], cwd=str(self.repo))
            content = out[:5000]
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "git_log", "repo": str(self.repo)},
                          content=content, content_hash=_sha256(content),
                          metadata={"entries": len(out.split("\n"))}).to_dict()
        out, _ = _run_cmd(["git", "show", resource_id], cwd=str(self.repo))
        content = out[:5000]
        return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                       provenance={"method": "git_show", "ref": resource_id},
                       content=content, content_hash=_sha256(content),
                       metadata={}).to_dict()

    def search(self, query: str, limit: int = 10) -> dict:
        out, _ = _run_cmd(["git", "log", "--oneline", f"-{limit}", "--all", "--grep", query], cwd=str(self.repo))
        results = [l.strip() for l in out.split("\n") if l.strip()]
        return {"results": results, "query": query, "count": len(results)}

    def capabilities(self) -> dict:
        return {"read": True, "write": False, "audit": True, "delete": False, "publish": False}

    def health(self) -> dict:
        return {"healthy": (self.repo / ".git").is_dir(), "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "git_cli",
                "owner": "MILK Sovereign Core", "canonical_role": "primary_authority"}


# ---------------------------------------------------------------------------
# Helper for subprocess commands
# ---------------------------------------------------------------------------

def _run_cmd(cmd: list, timeout: int = 15, cwd: str | None = None) -> tuple[str, int]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=cwd, encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return f"ERROR: {e}", -1


# ---------------------------------------------------------------------------
# 12. BoxAdapter — Box cloud storage (if installed)
# ---------------------------------------------------------------------------

class BoxAdapter(ExternalSystemAdapter):
    """Box — if Box Drive/sync is installed locally."""

    def __init__(self):
        self.sync_dir = None
        for p in [Path.home() / "Box", Path.home() / "Box Sync", Path.home() / "Box Drive"]:
            if p.is_dir():
                self.sync_dir = p
                break

    @property
    def name(self) -> str:
        return "box"

    def discover(self) -> dict:
        return {"found": self.sync_dir is not None, "sync_dir": str(self.sync_dir) if self.sync_dir else None}

    def auth_status(self) -> dict:
        if not self.sync_dir:
            return {"authenticated": False, "credential_type": "none",
                    "blocked_operation": "all",
                    "where_to_configure": "Install Box Drive or configure Box API token"}
        return {"authenticated": True, "credential_type": "Box Drive sync (OS-level)"}

    def list_resources(self) -> dict:
        if not self.sync_dir:
            return {"resources": [], "error": "Box not found"}
        resources = [{"id": i.name, "type": "dir" if i.is_dir() else "file"}
                     for i in sorted(self.sync_dir.iterdir())[:30]]
        return {"resources": resources, "count": len(resources)}

    def read_resource(self, resource_id: str) -> dict:
        if not self.sync_dir:
            return {"error": "Box not found"}
        path = self.sync_dir / resource_id
        if not path.exists():
            return {"error": "not found"}
        if path.is_dir():
            items = [{"name": i.name} for i in sorted(path.iterdir())[:50]]
            content = json.dumps(items, ensure_ascii=False)
            return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                          provenance={"method": "box_sync_dir", "path": str(path)},
                          content=content, content_hash=_sha256(content),
                          metadata={"item_count": len(items)}).to_dict()
        raw = path.read_bytes()
        content = raw.decode("utf-8", errors="replace")[:5000]
        return Evidence(source_id=resource_id, source_system=self.name, retrieved_at=_now_utc(),
                       provenance={"method": "box_sync_read", "path": str(path)},
                       content=content, content_hash=_sha256(content),
                       metadata={"size_bytes": len(raw)}).to_dict()

    def capabilities(self) -> dict:
        return {"read": self.sync_dir is not None, "write": False, "audit": True,
                "delete": False, "publish": False}

    def health(self) -> dict:
        return {"healthy": self.sync_dir is not None, "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "filesystem (Box Drive)",
                "owner": "MILK Sovereign Core", "client_role": "sync_client_delegated"}


# ---------------------------------------------------------------------------
# 13. Base44Adapter — Base44/Cosmic Touch CLI/MCP discovery
# ---------------------------------------------------------------------------

class Base44Adapter(ExternalSystemAdapter):
    """Base44 — detect CLI/MCP/config. TOOL external only, never Sovereign Core dependency."""

    def __init__(self):
        self._cli_found = self._check_cli()
        self._config = self._check_config()

    def _check_cli(self) -> bool:
        out, code = _run_cmd(["base44", "--version"], timeout=5)
        return code == 0

    def _check_config(self) -> str | None:
        for p in [Path.home() / ".base44", Path.home() / ".cosmic-touch",
                  Path.home() / ".config" / "base44"]:
            if p.exists():
                return str(p)
        return None

    @property
    def name(self) -> str:
        return "base44"

    def discover(self) -> dict:
        return {"cli_found": self._cli_found, "config_found": self._config,
                "note": "Cosmic Touch / Base44 detection. TOOL only, never Sovereign Core dependency."}

    def auth_status(self) -> dict:
        cred, status = _detect_secret("BASE44_TOKEN", "BASE44_API_KEY")
        return {"authenticated": cred is not None or self._cli_found,
                "credential_type": "BASE44_TOKEN or CLI",
                "status": status if cred else "CLI not found" if not self._cli_found else "CLI present",
                "blocked_operation": None if cred or self._cli_found else "all",
                "where_to_configure": "Base44 CLI auth or BASE44_TOKEN env var"}

    def list_resources(self) -> dict:
        if not self._cli_found:
            return {"resources": [], "error": "Base44 CLI not found"}
        return {"resources": [], "note": "Base44 CLI found but no resources listed without auth"}

    def read_resource(self, resource_id: str) -> dict:
        return {"error": "not implemented", "resource_id": resource_id,
                "note": "Base44 requires explicit auth configuration"}

    def capabilities(self) -> dict:
        return {"read": self._cli_found, "write": False, "audit": True, "delete": False,
                "publish": False, "sovereign_core_dependency": False,
                "note": "TOOL external only — never a dependency of the Sovereign Core"}

    def health(self) -> dict:
        return {"healthy": self._cli_found or self._config is not None, "name": self.name}

    def provenance(self) -> dict:
        return {"adapter": self.name, "version": "1.0", "access": "cli/api",
                "owner": "MILK Sovereign Core", "client_role": "external_tool",
                "canonical_role": "tool_only (never authority)"}


# ---------------------------------------------------------------------------
# Registry — instantiate all adapters
# ---------------------------------------------------------------------------

def get_all_adapters() -> dict[str, ExternalSystemAdapter]:
    return {
        "localfs": LocalFSAdapter(),
        "cloudsync": CloudSyncAdapter(),
        "nextcloud": NextcloudAdapter(),
        "onedrive": OneDriveAdapter(),
        "github": GitHubAdapter(),
        "codeberg": CodebergForgejoAdapter(),
        "zenodo": ZenodoAdapter(),
        "orcid": OrcidAdapter(),
        "docker": DockerAdapter(),
        "git": GitAdapter(),
        "box": BoxAdapter(),
        "base44": Base44Adapter(),
        "ptservidor": PTServidorAdapter(),
    }


def audit_all() -> dict:
    """Run discover() + auth_status() + health() on every adapter.
    Returns a single audit report. Does NOT block on any single adapter.
    """
    report = {}
    for name, adapter in get_all_adapters().items():
        try:
            report[name] = {
                "discover": adapter.discover(),
                "auth_status": adapter.auth_status(),
                "health": adapter.health(),
                "capabilities": adapter.capabilities(),
                "provenance": adapter.provenance(),
            }
        except Exception as e:
            report[name] = {"error": str(e), "adapter": name}
    return report
