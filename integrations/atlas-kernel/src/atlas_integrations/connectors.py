from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from urllib.parse import quote

from .http import SafeHttpClient
from .models import AtlasRecord, ExecutionReceipt


def _digest(data: Any) -> str:
    return sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _receipt(name: str, operation: str, data: Any, execute: bool, status: str,
             external_id: str | None = None, detail: dict[str, Any] | None = None) -> ExecutionReceipt:
    return ExecutionReceipt(connector=name, operation=operation, executed=execute,
                            dry_run=not execute, status=status, request_hash=_digest(data),
                            external_id=external_id, detail=detail or {})


class RORConnector:
    BASE = "https://api.ror.org/v2/organizations"

    def __init__(self, client_id: str | None = None):
        self.client = SafeHttpClient({"api.ror.org"})
        self.client_id = client_id

    def search(self, query: str) -> dict[str, Any]:
        headers = {"Client-Id": self.client_id} if self.client_id else {}
        return self.client.request("GET", self.BASE, params={"query": query}, headers=headers).body

    def match_affiliation(self, affiliation: str) -> dict[str, Any]:
        headers = {"Client-Id": self.client_id} if self.client_id else {}
        return self.client.request("GET", self.BASE, params={"affiliation": affiliation}, headers=headers).body


class ZenodoConnector:
    def __init__(self, token: str | None = None, sandbox: bool = True):
        self.host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
        self.base = f"https://{self.host}/api"
        self.client = SafeHttpClient({self.host})
        self.token = token

    def search_records(self, query: str) -> Any:
        return self.client.request("GET", f"{self.base}/records", params={"q": query}).body

    def create_draft(self, record: AtlasRecord, *, execute: bool = False) -> ExecutionReceipt:
        payload = {"metadata": {"title": record.title, "description": record.description,
                   "upload_type": "dataset", "creators": [{"name": c} for c in record.creators],
                   "license": record.licence}}
        if not execute:
            return _receipt("zenodo", "create_draft", payload, False, "VALIDADO_SEM_EXECUTAR")
        if not self.token:
            raise ValueError("ZENODO_TOKEN em falta")
        body = self.client.request("POST", f"{self.base}/deposit/depositions",
                                   params={"access_token": self.token}, json_body=payload).body
        return _receipt("zenodo", "create_draft", payload, True, "RASCUNHO_CRIADO", str(body.get("id")), body)


class ORCIDConnector:
    def __init__(self, token: str | None = None, sandbox: bool = True):
        self.host = "api.sandbox.orcid.org" if sandbox else "api.orcid.org"
        self.base = f"https://{self.host}/v3.0"
        self.client = SafeHttpClient({self.host})
        self.token = token

    def read_record(self, orcid_id: str) -> Any:
        headers = {"Accept": "application/vnd.orcid+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return self.client.request("GET", f"{self.base}/{quote(orcid_id)}/record", headers=headers).body


class DataCiteConnector:
    def __init__(self, repository_id: str | None = None, password: str | None = None, sandbox: bool = True):
        self.host = "api.test.datacite.org" if sandbox else "api.datacite.org"
        self.base = f"https://{self.host}"
        self.client = SafeHttpClient({self.host})
        self.repository_id, self.password = repository_id, password

    def get_doi(self, doi: str) -> Any:
        return self.client.request("GET", f"{self.base}/dois/{quote(doi, safe='')}").body

    def validate_draft(self, record: AtlasRecord, prefix: str, suffix: str) -> ExecutionReceipt:
        payload = {"data": {"type": "dois", "attributes": {"doi": f"{prefix}/{suffix}",
            "event": "draft", "creators": [{"name": c} for c in record.creators],
            "titles": [{"title": record.title}], "publisher": "Associação MILK",
            "publicationYear": 2026, "types": {"resourceTypeGeneral": "Dataset"},
            "url": "https://atlas.associacaomilk.pt"}}}
        return _receipt("datacite", "validate_draft", payload, False, "VALIDADO_SEM_REGISTAR", detail=payload)


class ForgejoConnector:
    def __init__(self, base_url: str, token: str | None = None):
        self.base = base_url.rstrip("/")
        host = self.base.removeprefix("https://").split("/")[0]
        self.client = SafeHttpClient({host})
        self.token = token

    def repo(self, owner: str, repo: str) -> Any:
        headers = {"Authorization": f"token {self.token}"} if self.token else {}
        return self.client.request("GET", f"{self.base}/api/v1/repos/{quote(owner)}/{quote(repo)}", headers=headers).body


class FIWAREConnector:
    def __init__(self, broker_url: str, token: str | None = None):
        self.base = broker_url.rstrip("/")
        host = self.base.removeprefix("https://").split("/")[0]
        self.client = SafeHttpClient({host})
        self.token = token

    def entity_payload(self, record: AtlasRecord) -> dict[str, Any]:
        return {"id": f"urn:ngsi-ld:AtlasRecord:{record.record_id}", "type": "AtlasRecord",
                "title": {"type": "Property", "value": record.title},
                "classification": {"type": "Property", "value": record.classification.value},
                "provenanceHash": {"type": "Property", "value": record.canonical_hash()},
                "@context": ["https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"]}

    def create_entity(self, record: AtlasRecord, *, execute: bool = False) -> ExecutionReceipt:
        payload = self.entity_payload(record)
        if not execute:
            return _receipt("fiware", "create_entity", payload, False, "VALIDADO_SEM_EXECUTAR")
        headers = {"Link": '<https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"'}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.client.request("POST", f"{self.base}/ngsi-ld/v1/entities", json_body=payload, headers=headers)
        return _receipt("fiware", "create_entity", payload, True, f"HTTP_{response.status}")


class ManualAuthorityGate:
    """IGAC/WIPO: não inventa API nem número de registo; produz dossiê verificável."""
    def dossier(self, authority: str, record: AtlasRecord) -> ExecutionReceipt:
        payload = {"authority": authority.upper(), "title": record.title,
                   "creators": record.creators, "licence": record.licence,
                   "provenance_sha256": record.provenance.sha256,
                   "record_hash": record.canonical_hash(), "status": "REVISAO_HUMANA_OBRIGATORIA"}
        return _receipt(authority.lower(), "prepare_dossier", payload, False, "DOSSIER_PREPARADO", detail=payload)

