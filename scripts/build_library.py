#!/usr/bin/env python3
"""Constrói a biblioteca estruturada da MILK a partir do corpus ingerido.

Pipeline:
  1. Lê todos os documentos do CorpusStore (já ingeridos por ingest_total.py).
  2. Extrai citações/referências de cada documento (DOI, URL, ISBN, autor-ano).
  3. Entrecruza: para cada referência, lista que documentos a citam.
  4. Enriquece com dados da internet lidos de um ficheiro JSON opcional
     (--enrichment) — gerado pelo agente via web_search/web_fetch.
  5. Exporta em formato Sheets (.xlsx com openpyxl) e CSV.

Uso:
  python scripts/build_library.py --state-dir ~/MILK_AI_STATE_CANONICO
  python scripts/build_library.py --state-dir ~/MILK_AI_STATE_CANONICO --enrichment enrichment.json --output MILK_BIBLIOTECA.xlsx
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.ingest import CorpusStore  # noqa: E402
from milk_ai.provenance import atomic_json, sha256_bytes, utc_now  # noqa: E402

log = logging.getLogger("milk_ai.build_library")

# --------------------------------------------------------------------------
# Padrões de citação/referência (importados de ingest_total para consistência)
# --------------------------------------------------------------------------

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+\b")
URL_PATTERN = re.compile(r"https?://[^\s)\"<>]+")
ISBN13_PATTERN = re.compile(r"\b97[89]\d{10}\b")
ISBN10_PATTERN = re.compile(r"\b\d{9}[\dX]\b")
AUTHOR_YEAR_PATTERN = re.compile(
    r"^[A-Z][A-Za-zÀ-ÿ'’.-]+,\s+[A-Z](?:\.[A-Z])*\.?\s*\(\d{4}\)\.?"
)
REFERENCE_HEADINGS = re.compile(
    r"^\s*#{0,6}\s*(?:refer[êe]ncias|bibliografia|references|bibliography|obras citadas)\b",
    flags=re.IGNORECASE,
)
# Citações no estilo APA/ABNT dentro do texto: (Silva, 2020) ou (Silva et al., 2019)
INTEXT_CITATION_PATTERN = re.compile(
    r"\(([A-Z][A-Za-zÀ-ÿ'’.-]+(?:\s+et\s+al\.?)?,?\s+\d{4}[a-z]?)\)"
)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_all_citations(text: str) -> list[dict[str, str]]:
    """Extrai todas as citações de um texto: DOI, URL, ISBN, autor-ano, citações no texto."""
    found: dict[str, dict[str, str]] = {}

    for m in DOI_PATTERN.finditer(text):
        v = m.group(0).rstrip(".,);")
        found.setdefault(v, {"type": "doi", "value": v})

    for m in ISBN13_PATTERN.finditer(text):
        v = m.group(0)
        found.setdefault(v, {"type": "isbn13", "value": v})

    for m in ISBN10_PATTERN.finditer(text):
        v = m.group(0)
        # Evita falsos positivos: ISBN-10 só se parecer ISBN (começa por dígitos e não é ano).
        if len(v) == 10 and not v.startswith("20") and not v.startswith("19"):
            found.setdefault(f"isbn10:{v}", {"type": "isbn10", "value": v})

    for m in URL_PATTERN.finditer(text):
        v = m.group(0).rstrip(".,);]")
        if not v.startswith(("http://doi.org", "https://doi.org", "http://dx.doi.org")):
            found.setdefault(v, {"type": "url", "value": v})

    for m in EMAIL_PATTERN.finditer(text):
        v = m.group(0)
        found.setdefault(f"email:{v}", {"type": "email", "value": v})

    # Citações no texto (Autor, Ano) — apenas fora de secções de referências.
    for m in INTEXT_CITATION_PATTERN.finditer(text):
        v = m.group(1).strip()
        found.setdefault(f"intext:{v}", {"type": "intext_citation", "value": v})

    # Referências completas só dentro de secções de referências.
    lines = text.splitlines()
    in_section = False
    for line in lines:
        if REFERENCE_HEADINGS.match(line):
            in_section = True
            continue
        if in_section and line.strip().startswith("#"):
            in_section = False
        if not in_section:
            continue
        stripped = line.strip()
        if AUTHOR_YEAR_PATTERN.match(stripped) and 10 <= len(stripped) <= 400:
            digest = sha256_bytes(stripped.encode("utf-8"))[:12]
            found.setdefault(f"ref:{digest}", {"type": "reference", "value": stripped})

    return list(found.values())


# --------------------------------------------------------------------------
# Entrecruzamento de citações
# --------------------------------------------------------------------------

def build_citation_index(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Constrói índice: referência -> [documentos que a citam] e cruzamentos."""
    ref_to_docs: dict[str, list[dict[str, str]]] = defaultdict(list)
    doc_to_refs: dict[str, list[dict[str, str]]] = defaultdict(list)
    all_refs: dict[str, dict[str, str]] = {}

    for doc in documents:
        meta = doc.get("metadata", {})
        source_id = meta.get("source_id", "?")
        title = meta.get("original_name", "?")
        text = doc.get("text", "")
        citations = extract_all_citations(text)
        doc_to_refs[source_id] = citations
        for cit in citations:
            key = f"{cit['type']}:{cit['value']}"
            all_refs.setdefault(key, cit)
            ref_to_docs[key].append({
                "source_id": source_id,
                "title": title,
                "path": meta.get("original_path", ""),
            })

    # Cruzamentos: pares de documentos que partilham referências.
    cross_refs: list[dict[str, Any]] = []
    doc_pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for ref_key, docs in ref_to_docs.items():
        if len(docs) < 2:
            continue
        for i, doc_a in enumerate(docs):
            for doc_b in docs[i + 1:]:
                pair = tuple(sorted([doc_a["source_id"], doc_b["source_id"]]))
                doc_pairs[pair].append(all_refs[ref_key]["value"])

    doc_by_id = {
        d.get("metadata", {}).get("source_id", ""): d for d in documents
    }
    for (id_a, id_b), shared in sorted(doc_pairs.items(), key=lambda x: -len(x[1])):
        doc_a = doc_by_id.get(id_a, {})
        doc_b = doc_by_id.get(id_b, {})
        cross_refs.append({
            "doc_a": id_a,
            "doc_a_title": doc_a.get("metadata", {}).get("original_name", "?"),
            "doc_b": id_b,
            "doc_b_title": doc_b.get("metadata", {}).get("original_name", "?"),
            "shared_count": len(shared),
            "shared_refs": shared[:20],
        })

    return {
        "references": sorted(all_refs.values(), key=lambda r: (r["type"], r["value"])),
        "ref_to_docs": {k: v for k, v in sorted(ref_to_docs.items())},
        "cross_refs": cross_refs[:500],
        "stats": {
            "total_documents": len(documents),
            "total_unique_references": len(all_refs),
            "total_citation_links": sum(len(v) for v in ref_to_docs.values()),
            "cross_referenced_pairs": len(cross_refs),
        },
    }


# --------------------------------------------------------------------------
# Enriquecimento com dados da internet
# --------------------------------------------------------------------------

def load_enrichment(path: Path | None) -> dict[str, dict[str, str]]:
    """Carrega dados de enriquecimento web (JSON: {ref_value: {title, authors, ...}})."""
    if not path or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def merge_enrichment(
    references: list[dict[str, str]],
    enrichment: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Funde metadados web nas referências encontradas."""
    result = []
    for ref in references:
        enriched = dict(ref)
        for key, meta in enrichment.items():
            if key.lower() in ref["value"].lower() or ref["value"].lower() in key.lower():
                enriched["web_title"] = meta.get("title", "")
                enriched["web_authors"] = meta.get("authors", "")
                enriched["web_date"] = meta.get("date", "")
                enriched["web_summary"] = meta.get("summary", "")[:300]
                break
        result.append(enriched)
    return result


# --------------------------------------------------------------------------
# Exportação para Sheets (Excel .xlsx) e CSV
# --------------------------------------------------------------------------

def export_xlsx(library: dict[str, Any], enrichment: dict[str, dict[str, str]], output: Path) -> None:
    """Exporta a biblioteca para um livro Excel multi-folhas."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    wrap = Alignment(wrap_text=True, vertical="top")

    def _write_sheet(ws, headers, rows):
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
        for row_idx, row in enumerate(rows, 2):
            for col, h in enumerate(headers, 1):
                val = row.get(h, "")
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                ws.cell(row=row_idx, column=col, value=str(val)[:32000])
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = min(60, max(15, max(
                (len(str(row.get(h, ""))) for row in rows), default=15
            )))
        ws.freeze_panes = "A2"

    # Folha 1: Documentos
    ws1 = wb.active
    ws1.title = "Documentos"
    doc_headers = ["source_id", "original_name", "document_type", "size_bytes",
                   "visibility", "ingested_at", "original_path", "chunks", "citation_count"]
    doc_rows = []
    for doc in library["documents"]:
        meta = doc.get("metadata", {})
        sid = meta.get("source_id", "?")
        doc_rows.append({
            "source_id": sid,
            "original_name": meta.get("original_name", "?"),
            "document_type": meta.get("document_type", ""),
            "size_bytes": meta.get("size_bytes", 0),
            "visibility": meta.get("visibility", ""),
            "ingested_at": meta.get("ingested_at", ""),
            "original_path": meta.get("original_path", ""),
            "chunks": len(doc.get("chunks", [])),
            "citation_count": len(library["index"]["ref_to_docs"].get(sid, [])) if sid in library.get("doc_ref_counts", {}) else 0,
        })
    _write_sheet(ws1, doc_headers, doc_rows)

    # Folha 2: Referências
    ws2 = wb.create_sheet("Referencias")
    enriched_refs = merge_enrichment(library["index"]["references"], enrichment)
    ref_headers = ["type", "value", "cited_by_count", "cited_by_docs",
                   "web_title", "web_authors", "web_date", "web_summary"]
    ref_rows = []
    for ref in enriched_refs:
        key = f"{ref['type']}:{ref['value']}"
        docs = library["index"]["ref_to_docs"].get(key, [])
        ref_rows.append({
            "type": ref["type"],
            "value": ref["value"],
            "cited_by_count": len(docs),
            "cited_by_docs": "; ".join(d["title"] for d in docs[:10]),
            "web_title": ref.get("web_title", ""),
            "web_authors": ref.get("web_authors", ""),
            "web_date": ref.get("web_date", ""),
            "web_summary": ref.get("web_summary", ""),
        })
    _write_sheet(ws2, ref_headers, ref_rows)

    # Folha 3: Entrecruzamentos
    ws3 = wb.create_sheet("Entrecruzamentos")
    cross_headers = ["doc_a", "doc_a_title", "doc_b", "doc_b_title", "shared_count", "shared_refs"]
    _write_sheet(ws3, cross_headers, library["index"]["cross_refs"])

    # Folha 4: Estatísticas
    ws4 = wb.create_sheet("Estatisticas")
    stats = library["index"]["stats"]
    _write_sheet(ws4, ["metric", "value"], [{"metric": k, "value": v} for k, v in stats.items()])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def export_csv(library: dict[str, Any], enrichment: dict[str, dict[str, str]], output_dir: Path) -> None:
    """Exporta também em CSV (um ficheiro por folha) para importação directa em Google Sheets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    enriched_refs = merge_enrichment(library["index"]["references"], enrichment)

    # documentos.csv
    with open(output_dir / "documentos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source_id", "original_name", "document_type",
                                          "size_bytes", "visibility", "ingested_at",
                                          "original_path", "chunks"])
        w.writeheader()
        for doc in library["documents"]:
            meta = doc.get("metadata", {})
            w.writerow({
                "source_id": meta.get("source_id", ""),
                "original_name": meta.get("original_name", ""),
                "document_type": meta.get("document_type", ""),
                "size_bytes": meta.get("size_bytes", ""),
                "visibility": meta.get("visibility", ""),
                "ingested_at": meta.get("ingested_at", ""),
                "original_path": meta.get("original_path", ""),
                "chunks": len(doc.get("chunks", [])),
            })

    # referencias.csv
    with open(output_dir / "referencias.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["type", "value", "cited_by_count", "cited_by_docs",
                                          "web_title", "web_authors", "web_date", "web_summary"])
        w.writeheader()
        for ref in enriched_refs:
            key = f"{ref['type']}:{ref['value']}"
            docs = library["index"]["ref_to_docs"].get(key, [])
            w.writerow({
                "type": ref["type"],
                "value": ref["value"],
                "cited_by_count": len(docs),
                "cited_by_docs": "; ".join(d["title"] for d in docs[:10]),
                "web_title": ref.get("web_title", ""),
                "web_authors": ref.get("web_authors", ""),
                "web_date": ref.get("web_date", ""),
                "web_summary": ref.get("web_summary", ""),
            })

    # entrecruzamentos.csv
    with open(output_dir / "entrecruzamentos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doc_a", "doc_a_title", "doc_b", "doc_b_title",
                                          "shared_count", "shared_refs"])
        w.writeheader()
        for cr in library["index"]["cross_refs"]:
            w.writerow({
                "doc_a": cr["doc_a"],
                "doc_a_title": cr["doc_a_title"],
                "doc_b": cr["doc_b"],
                "doc_b_title": cr["doc_b_title"],
                "shared_count": cr["shared_count"],
                "shared_refs": "; ".join(cr["shared_refs"]),
            })


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Constrói a biblioteca estruturada MILK: citações, entrecruzamento, Sheets.",
    )
    result.add_argument("--state-dir", type=Path, default=Path.home() / "MILK_AI_STATE_CANONICO")
    result.add_argument("--enrichment", type=Path, help="JSON com metadados web para enriquecer referências")
    result.add_argument("--output", type=Path, default=Path("MILK_BIBLIOTECA.xlsx"))
    result.add_argument("--csv-dir", type=Path, default=Path("MILK_BIBLIOTECA_CSV"))
    result.add_argument("--report", type=Path)
    result.add_argument("-v", "--verbose", action="count", default=0)
    return result


def main() -> int:
    args = parser().parse_args()
    logging.basicConfig(
        level=logging.WARNING - min(args.verbose * 10, 30),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    state_dir = args.state_dir.expanduser().resolve()
    store = CorpusStore(state_dir / "corpus")
    documents = store.documents()
    if not documents:
        print(json.dumps({"status": "sem_documentos", "reason": "corpus vazio — execute ingest_total.py primeiro"}, ensure_ascii=False))
        return 2

    log.info("a processar %d documentos do corpus", len(documents))
    index = build_citation_index(documents)

    enrichment = load_enrichment(args.enrichment)
    if enrichment:
        log.info("enriquecimento carregado: %d entradas", len(enrichment))

    library = {
        "generated_at": utc_now(),
        "documents": documents,
        "index": index,
    }

    # Exportação
    output_xlsx = args.output.expanduser().resolve()
    export_xlsx(library, enrichment, output_xlsx)
    log.info("Excel exportado: %s", output_xlsx)

    csv_dir = args.csv_dir.expanduser().resolve()
    export_csv(library, enrichment, csv_dir)
    log.info("CSV exportado: %s", csv_dir)

    # Relatório JSON
    report_path = (args.report or (state_dir / "BIBLIOTECA_RELATORIO.json")).expanduser().resolve()
    report = {
        "generated_at": utc_now(),
        "stats": index["stats"],
        "output_xlsx": str(output_xlsx),
        "csv_dir": str(csv_dir),
        "enrichment_entries": len(enrichment),
    }
    atomic_json(report_path, report)

    summary = {
        "status": "concluido",
        "stats": index["stats"],
        "output_xlsx": str(output_xlsx),
        "csv_dir": str(csv_dir),
        "report": str(report_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
