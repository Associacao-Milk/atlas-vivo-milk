from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchHit:
    title: str
    authors: list[str]
    year: int | None
    url: str | None
    source: str
    kind: str
    abstract: str | None
    annotation: str
    identifier: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "titulo": self.title,
            "autores": self.authors,
            "ano": self.year,
            "url": self.url,
            "fonte": self.source,
            "tipo": self.kind,
            "resumo": self.abstract,
            "anotacao": self.annotation,
            "identificador": self.identifier,
        }


def _request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "MILK-AI-Research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _year(value: Any) -> int | None:
    if isinstance(value, list) and value and isinstance(value[0], list) and value[0]:
        value = value[0][0]
    if isinstance(value, list) and value:
        value = value[0]
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def _authors(items: Any) -> list[str]:
    result: list[str] = []
    for item in items or []:
        name = item.get("author", {}).get("display_name") or item.get("family")
        if name:
            result.append(str(name))
    return result[:12]


def search_openalex(query: str, limit: int) -> list[ResearchHit]:
    params = urllib.parse.urlencode({"search": query, "per-page": limit, "select": "id,title,authorships,publication_year,doi,open_access,abstract_inverted_index"})
    data = _request_json(f"https://api.openalex.org/works?{params}")
    hits: list[ResearchHit] = []
    for item in data.get("results", []):
        inverted = item.get("abstract_inverted_index") or {}
        words: list[tuple[int, str]] = []
        for word, positions in inverted.items():
            words.extend((position, word) for position in positions)
        abstract = " ".join(word for _position, word in sorted(words)) or None
        identifier = item.get("doi") or item.get("id")
        hits.append(ResearchHit(
            title=item.get("title") or "Sem título",
            authors=_authors(item.get("authorships")),
            year=item.get("publication_year"),
            url=item.get("doi") or item.get("id"),
            source="OpenAlex",
            kind="artigo/pesquisa",
            abstract=abstract,
            annotation="Resultado OpenAlex; verificar texto integral, método, amostra e validade antes de citar.",
            identifier=identifier,
        ))
    return hits


def search_crossref(query: str, limit: int) -> list[ResearchHit]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": limit, "select": "DOI,title,author,published,URL,type,abstract"})
    data = _request_json(f"https://api.crossref.org/works?{params}")
    hits: list[ResearchHit] = []
    for item in data.get("message", {}).get("items", []):
        titles = item.get("title") or []
        if not titles:
            continue
        hits.append(ResearchHit(
            title=titles[0],
            authors=[f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get("author", []) if a.get("family")][:12],
            year=_year(item.get("published")),
            url=item.get("URL"),
            source="Crossref",
            kind=item.get("type", "publicação"),
            abstract=re.sub(r"<[^>]+>", "", item.get("abstract", "")) or None,
            annotation="Registro Crossref; confirmar edição, revisão por pares e pertinência metodológica.",
            identifier=item.get("DOI"),
        ))
    return hits


def search_datacite(query: str, limit: int) -> list[ResearchHit]:
    params = urllib.parse.urlencode({"query": query, "page[size]": limit})
    data = _request_json(f"https://api.datacite.org/dois?{params}")
    hits: list[ResearchHit] = []
    for item in data.get("data", []):
        attrs = item.get("attributes", {})
        title = (attrs.get("titles") or [{}])[0].get("title")
        if not title:
            continue
        hits.append(ResearchHit(
            title=title,
            authors=[a.get("name") for a in attrs.get("creators", []) if a.get("name")][:12],
            year=_year(attrs.get("published")),
            url=attrs.get("url"),
            source="DataCite",
            kind=attrs.get("types", {}).get("resourceTypeGeneral", "dataset/recurso"),
            abstract=attrs.get("descriptions", [{}])[0].get("description") if attrs.get("descriptions") else None,
            annotation="Registro DataCite; verificar licença, versão e relação entre dataset, software e publicação.",
            identifier=item.get("id"),
        ))
    return hits


def collect_references(query: str, limit: int = 10) -> dict[str, Any]:
    hits: list[ResearchHit] = []
    errors: list[dict[str, str]] = []
    for name, searcher in (("OpenAlex", search_openalex), ("Crossref", search_crossref), ("DataCite", search_datacite)):
        try:
            hits.extend(searcher(query, limit))
        except Exception as exc:
            errors.append({"fonte": name, "erro": f"{type(exc).__name__}: {exc}"})
    unique: dict[str, ResearchHit] = {}
    for hit in hits:
        key = (hit.identifier or hit.title).casefold().strip()
        unique.setdefault(key, hit)
    ordered = sorted(unique.values(), key=lambda item: (item.year or 0, item.title.casefold()), reverse=True)
    return {
        "schema": "ia_milk.research.bibliography.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "query": query,
        "references": [hit.to_dict() for hit in ordered],
        "summary": {
            "total": len(ordered),
            "artigos_pesquisas": sum(hit.kind == "artigo/pesquisa" for hit in ordered),
            "teses_dissertacoes": sum("thesis" in hit.kind.casefold() or "dissert" in hit.kind.casefold() for hit in ordered),
            "fontes_consultadas": sorted({hit.source for hit in ordered}),
        },
        "errors": errors,
        "validation": "Referências candidatas; exigem leitura humana e validação de evidência antes de uso institucional.",
    }
