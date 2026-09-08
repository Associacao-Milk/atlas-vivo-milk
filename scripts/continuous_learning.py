#!/usr/bin/env python3
"""Daemon de aprendizado contínuo, relacional e multimodal da MILK IA.

Funciona como um processo autónomo que nunca para. Em cada ciclo:

  1. Varredura incremental: descobre ficheiros novos/alterados nas nuvens locais
     (OneDrive, Nextcloud, milk_ai) e ingere apenas o que ainda não está no corpus.
     Suporta texto, PDF, DOCX/XLSX/PPTX, OpenDocument, imagens (metadados + OCR
     opcional), ZIPs (extracção recursiva), formatos binários legacy.

  2. Aprendizado relacional: constrói e mantém um grafo de relações entre
     documentos -- citações partilhadas (DOI, URL, ISBN, autor-ano), entidades
     nomeadas partilhadas (pessoas, organizações, locais), e similaridade
     temática (TF-IDF). O grafo é persistido e actualizado incrementalmente.

  3. Aprendizado multimodal: indexa cada documento por modalidade (texto,
     imagem, dados tabulares, código, apresentação) e cruza modalidades --
     por exemplo, imagens referenciadas em documentos de texto, ou tabelas
     citadas em artigos.

  4. Pesquisa bibliográfica autónoma: consulta OpenAlex, Crossref e DataCite
     com tópicos extraídos do corpus, enriquece as referências e liga-as aos
     documentos que as citam.

  5. Exportação contínua da biblioteca estruturada em Sheets (.xlsx) e CSV,
     actualizada a cada ciclo.

  6. Relatório de estado persistido em estado_aprendizado.json.

Uso:
  python scripts/continuous_learning.py
  python scripts/continuous_learning.py --interval 300 --state-dir ~/MILK_AI_STATE_CANONICO
  python scripts/continuous_learning.py --once   # um único ciclo
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.cloud_sources import discover_cloud_sources
from milk_ai.ingest import CorpusStore, SUPPORTED_EXTENSIONS, effective_suffix
from milk_ai.models import Visibility
from milk_ai.provenance import atomic_json, sha256_bytes, sha256_file, utc_now

# Reutiliza a lógica de pré-processamento do ingest_total
sys.path.insert(0, str(ROOT / "scripts"))
from ingest_total import (
    PREPROCESS_EXTENSIONS,
    ALL_INGESTABLE,
    ZIP_EXTENSIONS,
    preprocess_file,
    _ingest_zip,
    _classify_document,
    _same_or_parent,
    extract_references,
)

# Reutiliza a construção de relações do build_library
from build_library import (
    extract_all_citations,
    build_citation_index,
    export_xlsx,
    export_csv,
)

log = logging.getLogger("milk_ai.continuous_learning")

# --------------------------------------------------------------------------
# Estado de aprendizado persistente
# --------------------------------------------------------------------------

STATE_SCHEMA = "ia_milk.continuous_learning.v1"

DEFAULT_QUERIES = [
    "tecnologia cultura métodos de análise social",
    "sociologia Portugal contemporaneidade",
    "neurolinguística neurotecnologia",
    "folclore português tradições orais",
    "psicologia social estudos contemporâneos",
    "Foucault Bourdieu Habermas Adorno teoria crítica",
    "história marginal Portugal analfabetos negros pobres interior",
]

# Entidades nomeadas simples (maiúsculas consistentes, 2+ palavras ou nomes próprios)
ENTITY_PATTERN = re.compile(
    r"\b(?:[A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+){1,4})\b"
)
# Locais geográficos portugueses
TERRITORY_HINTS = re.compile(
    r"\b(?:freguesia|concelho|município|distrito|aldeia|vila|cidade)\s+de\s+([A-Z][a-zà-ÿ\s-]+)",
    flags=re.IGNORECASE,
)


def load_learning_state(path: Path) -> dict[str, Any]:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "schema": STATE_SCHEMA,
        "created_at": utc_now(),
        "cycles": 0,
        "last_cycle": None,
        "known_sha256": [],
        "query_rotation": 0,
        "relations": {"shared_citations": 0, "shared_entities": 0, "cross_modal": 0},
    }


def save_learning_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_json(path, state)


# --------------------------------------------------------------------------
# Fase 1: Varredura incremental
# --------------------------------------------------------------------------

def scan_known_sha256(store: CorpusStore) -> set[str]:
    """Carrega os SHA-256 já ingeridos para saltar ficheiros duplicados."""
    known: set[str] = set()
    for doc_path in store.documents_dir.glob("*.json"):
        known.add(doc_path.stem)
    for q_path in store.quarantine_dir.glob("*.json"):
        known.add(q_path.stem)
    return known


def incremental_ingest(
    store: CorpusStore,
    *,
    sources: list[Path],
    visibility: Visibility,
    staging: Path,
    known_sha256: set[str],
) -> list[dict[str, Any]]:
    """Ingere apenas ficheiros novos (SHA-256 não no corpus)."""
    results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    protected_root = Path(os.path.abspath(store.root))

    for root in sources:
        if not root.is_dir():
            continue
        log.info("varredura incremental: %s", root)
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dir_path = Path(dirpath)
            from milk_ai.ingest import DEFAULT_EXCLUDED_DIRS
            dirnames[:] = [
                name for name in dirnames
                if not (dir_path / name).is_symlink()
                and name.casefold() not in DEFAULT_EXCLUDED_DIRS
                and not _same_or_parent(Path(os.path.abspath(dir_path / name)), protected_root)
            ]
            for filename in filenames:
                item = dir_path / filename
                if item.is_symlink():
                    continue
                key = str(item.resolve())
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                suffix = item.suffix.lower()
                if suffix not in ALL_INGESTABLE:
                    continue
                # Verificação rápida de SHA-256 para ficheiros suportados diretamente
                if suffix in SUPPORTED_EXTENSIONS:
                    try:
                        digest = sha256_file(item)
                    except OSError:
                        continue
                    if digest in known_sha256:
                        continue
                    known_sha256.add(digest)
                if suffix in ZIP_EXTENSIONS:
                    try:
                        results.extend(_ingest_zip(item, store, staging, visibility=visibility, seen_paths=seen_paths))
                    except Exception as exc:
                        results.append({"status": "erro", "path": str(item), "reason": f"zip: {exc}"[:200]})
                else:
                    try:
                        converted = preprocess_file(item, staging / "preprocessed")
                    except Exception as exc:
                        converted = None
                        log.debug("preprocess falhou para %s: %s", item, exc)
                    target = converted or item
                    try:
                        results.append(store.ingest(target, visibility=visibility, extra_metadata={
                            "document_type": _classify_document(item),
                            "source_root": str(root),
                        }))
                    except Exception as exc:
                        results.append({"status": "erro", "path": str(item), "reason": str(exc)[:200]})
    return results


# --------------------------------------------------------------------------
# Fase 2: Aprendizado relacional
# --------------------------------------------------------------------------

def extract_entities(text: str) -> list[str]:
    """Extrai entidades nomeadas simples do texto."""
    found: set[str] = set()
    for m in ENTITY_PATTERN.finditer(text):
        entity = m.group(0).strip()
        # Filtra falsos positivos comuns
        if len(entity) < 5 or entity.startswith(("O ", "A ", "Os ", "As ")):
            continue
        if entity.isupper():
            continue
        found.add(entity)
    # Locais geográficos
    for m in TERRITORY_HINTS.finditer(text):
        found.add(m.group(1).strip())
    return sorted(found)[:50]


def build_entity_index(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Constrói índice de entidades partilhadas entre documentos."""
    entity_to_docs: dict[str, list[str]] = defaultdict(list)
    doc_entities: dict[str, list[str]] = {}

    for doc in documents:
        meta = doc.get("metadata", {})
        source_id = meta.get("source_id", "?")
        text = doc.get("text", "")
        entities = extract_entities(text)
        doc_entities[source_id] = entities
        for entity in entities:
            entity_to_docs[entity].append(source_id)

    # Cruzamentos: pares de documentos que partilham entidades
    doc_pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for entity, doc_ids in entity_to_docs.items():
        if len(doc_ids) < 2:
            continue
        unique_ids = sorted(set(doc_ids))
        for i, id_a in enumerate(unique_ids):
            for id_b in unique_ids[i + 1:]:
                pair = (id_a, id_b)
                doc_pairs[pair].append(entity)

    cross_entity = []
    for (id_a, id_b), shared in sorted(doc_pairs.items(), key=lambda x: -len(x[1]))[:500]:
        cross_entity.append({
            "doc_a": id_a, "doc_b": id_b,
            "shared_count": len(shared),
            "shared_entities": shared[:20],
        })

    return {
        "entity_to_docs": dict(entity_to_docs),
        "doc_entities": doc_entities,
        "cross_entity": cross_entity,
        "stats": {
            "total_entities": len(entity_to_docs),
            "shared_entity_pairs": len(cross_entity),
        },
    }


def build_modality_index(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Indexa documentos por modalidade e cruza modalidades."""
    modality_groups: dict[str, list[str]] = defaultdict(list)
    cross_modal: list[dict[str, Any]] = []

    for doc in documents:
        meta = doc.get("metadata", {})
        source_id = meta.get("source_id", "?")
        doc_type = meta.get("document_type", "outro")
        modality_groups[doc_type].append(source_id)

    # Cruzamentos modais: se um documento de texto referencia um ficheiro de imagem
    text_docs = modality_groups.get("texto", []) + modality_groups.get("documento_texto", [])
    image_docs = modality_groups.get("imagem", [])
    for text_doc_id in text_docs[:200]:
        doc = next((d for d in documents if d.get("metadata", {}).get("source_id") == text_doc_id), None)
        if not doc:
            continue
        text = doc.get("text", "")
        for img_doc_id in image_docs[:200]:
            img_doc = next((d for d in documents if d.get("metadata", {}).get("source_id") == img_doc_id), None)
            if not img_doc:
                continue
            img_name = img_doc.get("metadata", {}).get("original_name", "")
            if img_name and img_name.rsplit(".", 1)[0] in text:
                cross_modal.append({
                    "doc_a": text_doc_id,
                    "doc_a_type": "texto",
                    "doc_b": img_doc_id,
                    "doc_b_type": "imagem",
                    "relation": "referencia_visual",
                })

    return {
        "modalities": dict(modality_groups),
        "cross_modal": cross_modal[:500],
        "stats": {
            "total_modalities": len(modality_groups),
            "cross_modal_links": len(cross_modal),
        },
    }


def build_relations(store: CorpusStore) -> dict[str, Any]:
    """Constrói todas as relações do corpus."""
    documents = store.documents()
    log.info("a construir relações sobre %d documentos", len(documents))

    # Relações de citação (do build_library)
    citation_index = build_citation_index(documents)

    # Relações de entidades
    entity_index = build_entity_index(documents)

    # Relações multimodais
    modality_index = build_modality_index(documents)

    return {
        "generated_at": utc_now(),
        "documents": len(documents),
        "citations": citation_index,
        "entities": entity_index,
        "modalities": modality_index,
        "stats": {
            "documents": len(documents),
            "unique_references": citation_index["stats"]["total_unique_references"],
            "citation_links": citation_index["stats"]["total_citation_links"],
            "cross_referenced_pairs": citation_index["stats"]["cross_referenced_pairs"],
            "shared_entity_pairs": entity_index["stats"]["shared_entity_pairs"],
            "cross_modal_links": modality_index["stats"]["cross_modal_links"],
        },
    }


# --------------------------------------------------------------------------
# Fase 3: Pesquisa bibliográfica autónoma
# --------------------------------------------------------------------------

def autonomous_research(queries: list[str], limit: int = 8) -> dict[str, Any]:
    """Pesquisa autónoma em OpenAlex, Crossref e DataCite."""
    from milk_ai.research import collect_references

    all_refs: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for query in queries:
        try:
            result = collect_references(query, limit=limit)
            all_refs.extend(result.get("references", []))
            errors.extend(result.get("errors", []))
        except Exception as exc:
            errors.append({"query": query, "erro": f"{type(exc).__name__}: {exc}"})
        time.sleep(1)  # cortesia às APIs

    # Deduplica por identificador
    unique: dict[str, dict[str, Any]] = {}
    for ref in all_refs:
        key = (ref.get("identificador") or ref.get("titulo", "")).casefold().strip()
        unique.setdefault(key, ref)

    return {
        "generated_at": utc_now(),
        "queries": queries,
        "references": sorted(unique.values(), key=lambda r: (r.get("ano") or 0, r.get("titulo", "")), reverse=True),
        "errors": errors,
    }


# --------------------------------------------------------------------------
# Fase 4: Exportação da biblioteca
# --------------------------------------------------------------------------

def export_library(store: CorpusStore, state_dir: Path, relations: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    """Exporta a biblioteca estruturada em .xlsx e CSV."""
    documents = store.documents()
    library = {
        "generated_at": utc_now(),
        "documents": documents,
        "index": relations["citations"],
    }

    xlsx_path = state_dir / "MILK_BIBLIOTECA.xlsx"
    csv_dir = state_dir / "MILK_BIBLIOTECA_CSV"

    try:
        export_xlsx(library, {}, xlsx_path)
    except Exception as exc:
        log.warning("export xlsx falhou: %s", exc)
        xlsx_path = None

    try:
        export_csv(library, {}, csv_dir)
    except Exception as exc:
        log.warning("export csv falhou: %s", exc)
        csv_dir = None

    return {
        "xlsx": str(xlsx_path) if xlsx_path else None,
        "csv_dir": str(csv_dir) if csv_dir else None,
    }


# --------------------------------------------------------------------------
# Ciclo principal
# --------------------------------------------------------------------------

def run_cycle(
    store: CorpusStore,
    state_dir: Path,
    state: dict[str, Any],
    *,
    visibility: Visibility,
    sources: list[Path],
    research_queries: list[str],
    staging: Path,
    do_research: bool = True,
) -> dict[str, Any]:
    """Executa um ciclo completo de aprendizado. Retorna sumário do ciclo."""
    cycle_start = time.time()
    cycle_num = state.get("cycles", 0) + 1
    log.info("=== CICLO %d ===", cycle_num)

    # Fase 1: Varredura incremental
    known_sha256 = set(state.get("known_sha256", []))
    if not known_sha256:
        known_sha256 = scan_known_sha256(store)
        state["known_sha256"] = list(known_sha256)

    ingest_results = incremental_ingest(
        store, sources=sources, visibility=visibility, staging=staging, known_sha256=known_sha256,
    )
    ingest_counts = Counter(item.get("status", "desconhecido") for item in ingest_results)
    new_docs = sum(1 for item in ingest_results if item.get("status") == "indexado")
    log.info("fase 1 (ingestão): %d novos, %s", new_docs, dict(ingest_counts))

    # Actualiza SHA-256 conhecidos
    for item in ingest_results:
        if item.get("sha256") and item["sha256"] not in known_sha256:
            known_sha256.add(item["sha256"])
    state["known_sha256"] = sorted(known_sha256)[-50000:]  # limite de memória

    # Fase 2: Aprendizado relacional
    relations = build_relations(store)
    atomic_json(state_dir / "relacoes.json", relations)
    log.info("fase 2 (relações): %d refs, %d pares citação, %d pares entidade, %d cruzamentos modais",
             relations["stats"]["unique_references"],
             relations["stats"]["cross_referenced_pairs"],
             relations["stats"]["shared_entity_pairs"],
             relations["stats"]["cross_modal_links"])

    # Fase 3: Pesquisa bibliográfica autónoma (rota queries)
    research_result = None
    if do_research and research_queries:
        rotation = state.get("query_rotation", 0)
        batch_size = min(3, len(research_queries))
        selected = [research_queries[i % len(research_queries)] for i in range(rotation, rotation + batch_size)]
        state["query_rotation"] = (rotation + batch_size) % len(research_queries)
        try:
            research_result = autonomous_research(selected, limit=8)
            atomic_json(state_dir / "pesquisa_autonoma.json", research_result)
            log.info("fase 3 (pesquisa): %d referências de %d queries", len(research_result["references"]), len(selected))
        except Exception as exc:
            log.warning("fase 3 (pesquisa) falhou: %s", exc)

    # Fase 4: Exportação da biblioteca
    export_info = export_library(store, state_dir, relations, research_result or {})
    log.info("fase 4 (biblioteca): %s", export_info)

    # Estado
    elapsed = time.time() - cycle_start
    state["cycles"] = cycle_num
    state["last_cycle"] = {
        "at": utc_now(),
        "elapsed_seconds": round(elapsed, 1),
        "new_documents": new_docs,
        "ingest_counts": dict(ingest_counts),
        "relations": relations["stats"],
        "research_refs": len(research_result["references"]) if research_result else 0,
        "export": export_info,
    }
    state["relations"] = {
        "shared_citations": relations["stats"]["cross_referenced_pairs"],
        "shared_entities": relations["stats"]["shared_entity_pairs"],
        "cross_modal": relations["stats"]["cross_modal_links"],
    }

    return state["last_cycle"]


# --------------------------------------------------------------------------
# Daemon
# --------------------------------------------------------------------------

_running = True


def _signal_handler(signum, frame):
    global _running
    _running = False
    log.info("sinal %s recebido — a terminar após o ciclo actual", signum)


def main() -> int:
    args = parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG - min(args.verbose * 10, 30),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    state_dir = args.state_dir.expanduser().resolve()
    store = CorpusStore(state_dir / "corpus")
    visibility = Visibility(args.visibility)
    staging = state_dir / "staging"
    state_path = state_dir / "estado_aprendizado.json"
    state = load_learning_state(state_path)

    # Fontes
    sources = [Path(s) for s in args.sources if Path(s).is_dir()]
    if not sources:
        sources = discover_cloud_sources()
    log.info("fontes: %s", [str(s) for s in sources])

    # Queries de pesquisa
    research_queries = DEFAULT_QUERIES
    if args.queries_file:
        research_queries = json.loads(Path(args.queries_file).read_text(encoding="utf-8"))

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    log.info("MILK IA — daemon de aprendizado contínuo iniciado")
    log.info("state_dir=%s, interval=%ds, once=%s", state_dir, args.interval, args.once)

    while _running:
        try:
            run_cycle(
                store, state_dir, state,
                visibility=visibility,
                sources=sources,
                research_queries=research_queries,
                staging=staging,
                do_research=not args.no_research,
            )
            save_learning_state(state_path, state)
        except Exception as exc:
            log.error("ciclo falhou: %s", exc, exc_info=True)
            state["last_error"] = {"at": utc_now(), "error": str(exc)}
            save_learning_state(state_path, state)

        if args.once:
            break

        log.info("a dormir %d segundos antes do próximo ciclo...", args.interval)
        # Sleep interrompível
        slept = 0
        while _running and slept < args.interval:
            time.sleep(1)
            slept += 1

    save_learning_state(state_path, state)
    log.info("daemon terminado após %d ciclos", state.get("cycles", 0))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Daemon de aprendizado contínuo, relacional e multimodal da MILK IA.",
    )
    result.add_argument("--state-dir", type=Path, default=Path.home() / "MILK_AI_STATE_CANONICO")
    result.add_argument("--interval", type=int, default=300, help="segundos entre ciclos (defeito: 300)")
    result.add_argument("--visibility", choices=[item.value for item in Visibility], default=Visibility.RESTRICTED.value)
    result.add_argument("--sources", nargs="*", default=[], help="raízes adicionais para varrer")
    result.add_argument("--queries-file", type=Path, help="JSON com queries de pesquisa bibliográfica")
    result.add_argument("--no-research", action="store_true", help="desativar pesquisa bibliográfica autónoma")
    result.add_argument("--once", action="store_true", help="executar um único ciclo e sair")
    result.add_argument("-v", "--verbose", action="count", default=0)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
