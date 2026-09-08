#!/usr/bin/env python3
"""Ingestão total: bibliotecas externas, nuvens locais, OCR e bibliografia.

Integra-se no núcleo MILK AI: reutiliza CorpusStore (indexação preservativa com
provenância, desduplicação por SHA-256 e quarentena de segredos), o cofre DPAPI
para credenciais, e a descoberta de nuvens locais do cloud_sources.

As fontes externas (``library_search`` / ``open_library_result``) são injectáveis
como callbacks: o script funciona em modo demonstração (dry-run) quando o adaptador
não está disponível, e em modo real quando se fornece ``--library-adapter`` apontando
a um módulo Python que exporte essas duas funções.

Credenciais nunca são lidas do código: vêm de variáveis de ambiente ou do cofre.
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from milk_ai.cloud_sources import discover_cloud_sources  # noqa: E402
from milk_ai.ingest import CorpusStore  # noqa: E402
from milk_ai.models import Visibility  # noqa: E402
from milk_ai.provenance import (  # noqa: E402
    atomic_json,
    build_manifest,
    sha256_bytes,
    utc_now,
)

log = logging.getLogger("milk_ai.ingest_total")

# --------------------------------------------------------------------------
# Bibliotecas externas: adaptador injectável
# --------------------------------------------------------------------------

LibrarySearchFn = Callable[..., list[dict[str, Any]]]
LibraryOpenFn = Callable[[str], dict[str, Any] | None]

# As 12 bibliotecas do Universo MILK (identificadores estáveis; podem ser
# sobrescritos via --libraries ou ficheiro JSON).
DEFAULT_LIBRARIES: list[str] = [
    "01a01132-7adb-750d-a875-46d1789f04f0",
    "01a0165a-46c2-7081-a7e9-fa0f3bc4af4d",
    "019fabc3-665a-75f2-bdc4-5a131aa3998e",
    "019f3335-9ac2-7061-a2ad-5ff9489903f7",
    "019f3324-0ff1-75e7-84dd-eb414c431d37",
    "019f3274-9057-7005-aa8f-e3a831a634b2",
    "019f3266-ed62-73d2-a561-cea416715d7c",
    "019f2e9e-4189-768f-915e-841d122efb00",
    "019f2c63-e40a-72fb-a1e5-fca162b30d9a",
    "019f2bdb-a71c-7536-8416-a4054a3fb44e",
    "01a01132-7d25-753d-855e-f6bfbccec9bc",
    "01a01132-7bfc-705b-94d4-8bc4bcf29c32",
]


def _noop_library_search(**kwargs: Any) -> list[dict[str, Any]]:
    return []


def _noop_library_open(document_id: str) -> dict[str, Any] | None:
    return None


def load_library_adapter(module_path: str | None) -> tuple[LibrarySearchFn, LibraryOpenFn]:
    """Carrega library_search/open_library_result de um módulo Python.

    O módulo deve expor ``library_search(*, query, library_id, limit)`` e
    ``open_library_result(document_id)``. Sem ``module_path`` devolve no-ops
    (modo demonstração): o script corre sem erro mas não ingere nada das
    bibliotecas externas.
    """
    if not module_path:
        return _noop_library_search, _noop_library_open
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise SystemExit(f"adaptador de bibliotecas não encontrado: {module_path} ({exc})") from exc
    search = getattr(module, "library_search", None)
    opener = getattr(module, "open_library_result", None)
    if search is None or opener is None:
        raise SystemExit(f"{module_path} tem de exportar library_search e open_library_result")
    return search, opener


def _safe_title_filename(title: str, fallback: str) -> str:
    """Sanitiza um título para uso como nome de ficheiro."""
    value = (title or "").strip() or fallback
    value = unicodedata.normalize("NFKD", value)
    value = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", value)
    value = re.sub(r"\s+", " ", value).strip().strip(".")
    return (value or fallback)[:140]


# --------------------------------------------------------------------------
# Ingestão das bibliotecas externas
# --------------------------------------------------------------------------

def fetch_library_documents(
    libraries: list[str],
    search: LibrarySearchFn,
    *,
    query: str = "",
    page_size: int = 50,
    rate_delay: float = 0.4,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    """Lista documentos de todas as bibliotecas, desduplicando por id/url."""
    seen: set[str] = set()
    documents: list[dict[str, Any]] = []
    for library_id in libraries:
        for attempt in range(1, max_retries + 1):
            try:
                hits = search(query=query, library_id=library_id, limit=page_size) or []
                break
            except Exception as exc:  # noqa: BLE001 - adaptador externo
                if attempt == max_retries:
                    log.warning("biblioteca %s falhou após %d tentativas: %s", library_id, max_retries, exc)
                    hits = []
                else:
                    time.sleep(rate_delay * attempt * 2)
        for item in hits:
            if not isinstance(item, dict):
                continue
            doc_id = str(item.get("url", item.get("id", ""))).rstrip("/")
            key = doc_id or item.get("title", "")
            if not key or key in seen:
                continue
            seen.add(key)
            documents.append({
                "id": doc_id.split("/")[-1] if doc_id else "",
                "title": item.get("title", "Sem título"),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "library_id": library_id,
                "source": "library",
            })
        time.sleep(rate_delay)
    return documents


def ingest_library_documents(
    documents: list[dict[str, Any]],
    opener: LibraryOpenFn,
    store: CorpusStore,
    *,
    staging: Path,
    visibility: Visibility,
    rate_delay: float = 0.3,
) -> list[dict[str, Any]]:
    """Abre cada documento remoto, grava cópia local temporária e ingere-a."""
    staging.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for ordinal, doc in enumerate(documents, start=1):
        title = doc["title"]
        log.info("bibliotecas [%d/%d] %s", ordinal, len(documents), title)
        opened = None
        try:
            opened = opener(doc["id"])
        except Exception as exc:  # noqa: BLE001 - adaptador externo
            results.append({"status": "erro", "title": title, "reason": f"open: {exc}"})
            continue
        if not opened or not str(opened.get("content", "")).strip():
            results.append({"status": "ignorado", "title": title, "reason": "sem conteúdo"})
            continue
        filename = _safe_title_filename(title, fallback=doc["id"] or f"doc-{ordinal}")
        path = staging / f"{filename}.md"
        header = (
            f"# {title}\n\n"
            f"**Descrição:** {doc.get('description', 'N/A')}\n\n"
            f"**Biblioteca:** {doc['library_id']}\n\n"
            f"**URL:** {doc.get('url', 'N/A')}\n\n"
            f"**Ingerido em:** {utc_now()}\n\n---\n\n"
        )
        path.write_text(header + str(opened["content"]), encoding="utf-8")
        results.append(store.ingest(path, visibility=visibility, extra_metadata={"document_type": "library_export"}))
        time.sleep(rate_delay)
    return results


# --------------------------------------------------------------------------
# Pré-processamento: ZIP, OpenDocument, imagens
# --------------------------------------------------------------------------

# Extensões que o CorpusStore aceita directamente.
from milk_ai.ingest import SUPPORTED_EXTENSIONS  # noqa: E402

# Extensões que exigem pré-processamento antes de chegar ao CorpusStore.
ZIP_EXTENSIONS = {".zip"}
OPENDOCUMENT_EXTENSIONS = {".odt", ".odp", ".ods", ".odg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".webp"}
LEGACY_OFFICE_EXTENSIONS = {".doc", ".xls", ".ppt", ".vsd", ".pages"}
PREPROCESS_EXTENSIONS = ZIP_EXTENSIONS | OPENDOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | LEGACY_OFFICE_EXTENSIONS
ALL_INGESTABLE = SUPPORTED_EXTENSIONS | PREPROCESS_EXTENSIONS

MAX_ZIP_DEPTH = 3
MAX_ZIP_MEMBERS = 2000
MAX_ZIP_SIZE = 1024 * 1024 * 1024  # 1 GB


def _extract_opendocument_text(path: Path) -> str:
    """Extrai texto de ficheiros OpenDocument (ODT/ODP/ODS/ODG — ZIP com content.xml)."""
    from xml.etree import ElementTree
    import zipfile
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        target = "content.xml" if "content.xml" in members else next(
            (m for m in members if m.endswith("content.xml")), None
        )
        if not target:
            return ""
        xml = archive.read(target)
    root = ElementTree.fromstring(xml)
    paragraphs = []
    for node in root.iter():
        if node.text and node.text.strip():
            paragraphs.append(node.text.strip())
    return "\n\n".join(paragraphs)


def _extract_image_metadata(path: Path) -> str:
    """Extrai metadados de imagens (dimensões, EXIF) via Pillow. OCR exige tesseract."""
    from PIL import Image
    lines = [f"# Imagem: {path.name}", f"**Caminho:** {path}", ""]
    try:
        img = Image.open(path)
        lines.append(f"**Formato:** {img.format}")
        lines.append(f"**Dimensões:** {img.width} x {img.height} px")
        lines.append(f"**Modo:** {img.mode}")
        exif = img.getexif()
        if exif:
            lines.append("")
            lines.append("## EXIF")
            for tag_id, value in exif.items():
                from PIL.ExifTags import TAGS
                tag = TAGS.get(tag_id, str(tag_id))
                lines.append(f"- {tag}: {value}")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"**Erro:** {exc}")
    return "\n".join(lines)


def preprocess_file(path: Path, staging: Path) -> Path | None:
    """Converte um ficheiro especial num formato que o CorpusStore aceita (.md/.txt).

    Devolve o caminho do ficheiro convertido, ou None se não precisa de conversão.
    """
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return None  # o CorpusStore lida directamente
    if suffix not in PREPROCESS_EXTENSIONS:
        return None  # formato não reconhecido

    staging.mkdir(parents=True, exist_ok=True)
    relative = path.stem
    out = staging / f"{relative}.md"

    if suffix in OPENDOCUMENT_EXTENSIONS:
        text = _extract_opendocument_text(path)
        if not text.strip():
            return None
        out.write_text(f"# {path.name}\n\n{text}", encoding="utf-8")
        return out

    if suffix in IMAGE_EXTENSIONS:
        text = _extract_image_metadata(path)
        out.write_text(text, encoding="utf-8")
        return out

    if suffix in LEGACY_OFFICE_EXTENSIONS:
        # Formatos binários legacy (.doc/.xls/.ppt) — regista metadados sem extrair texto.
        out.write_text(
            f"# {path.name}\n\n**Formato binário legacy:** {suffix}\n\n"
            f"**Caminho:** {path}\n\n"
            f"**Tamanho:** {path.stat().st_size} bytes\n\n"
            f"Texto não extraído automaticamente (formato binário proprietário).",
            encoding="utf-8",
        )
        return out

    return None


def _ingest_zip(
    zip_path: Path,
    store: CorpusStore,
    staging: Path,
    *,
    visibility: Visibility,
    depth: int = 0,
    seen_paths: set[str],
) -> list[dict[str, Any]]:
    """Extrai um ZIP e ingere todos os ficheiros relevantes do seu interior."""
    if depth > MAX_ZIP_DEPTH:
        log.warning("ZIP aninhado demasiado profundo (>%d): %s", MAX_ZIP_DEPTH, zip_path)
        return []
    import zipfile
    import tempfile
    results: list[dict[str, Any]] = []
    try:
        if zip_path.stat().st_size > MAX_ZIP_SIZE:
            log.warning("ZIP demasiado grande (>1GB): %s", zip_path)
            return [{"status": "ignorado", "path": str(zip_path), "reason": "ZIP > 1GB"}]
        with zipfile.ZipFile(zip_path) as archive:
            members = [m for m in archive.namelist() if not m.endswith("/")]
            if len(members) > MAX_ZIP_MEMBERS:
                log.warning("ZIP com demasiados membros (>%d): %s", MAX_ZIP_MEMBERS, zip_path)
                return [{"status": "ignorado", "path": str(zip_path), "reason": f"ZIP > {MAX_ZIP_MEMBERS} membros"}]
            extract_dir = staging / f"zip_{zip_path.stem}_{depth}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            archive.extractall(extract_dir)
    except (zipfile.BadZipFile, OSError) as exc:
        return [{"status": "erro", "path": str(zip_path), "reason": f"ZIP: {exc}"}]

    for member in sorted(extract_dir.rglob("*")):
        if not member.is_file():
            continue
        key = str(member.resolve())
        if key in seen_paths:
            continue
        seen_paths.add(key)
        suffix = member.suffix.lower()
        if suffix in ZIP_EXTENSIONS:
            results.extend(_ingest_zip(member, store, staging, visibility=visibility, depth=depth + 1, seen_paths=seen_paths))
        elif suffix in ALL_INGESTABLE:
            converted = preprocess_file(member, staging / "preprocessed")
            target = converted or member
            try:
                results.append(store.ingest(target, visibility=visibility, extra_metadata={
                    "document_type": "zip_member",
                    "zip_origin": str(zip_path),
                }))
            except Exception as exc:  # noqa: BLE001
                results.append({"status": "erro", "path": str(member), "reason": str(exc)[:200]})
    return results


def walk_and_ingest_all(
    store: CorpusStore,
    roots: list[Path],
    *,
    visibility: Visibility,
    staging: Path,
) -> list[dict[str, Any]]:
    """Percorre recursivamente todas as raízes e ingere todos os formatos suportados.

    Trata ZIPs (com extracção recursiva), OpenDocument, imagens, e tudo o que o
    CorpusStore aceita nativamente. Ignora dependências e directorias do sistema.
    """
    from milk_ai.ingest import DEFAULT_EXCLUDED_DIRS
    results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    protected_root = Path(os.path.abspath(store.root))

    for root in roots:
        if not root.is_dir():
            continue
        log.info("a percorrer: %s", root)
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dir_path = Path(dirpath)
            # Filtra directorias excluídas (dependências, sistema, corpus).
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
                if suffix in ZIP_EXTENSIONS:
                    results.extend(_ingest_zip(item, store, staging, visibility=visibility, seen_paths=seen_paths))
                elif suffix in ALL_INGESTABLE:
                    converted = preprocess_file(item, staging / "preprocessed")
                    target = converted or item
                    try:
                        results.append(store.ingest(target, visibility=visibility, extra_metadata={
                            "document_type": _classify_document(item),
                            "source_root": str(root),
                        }))
                    except Exception as exc:  # noqa: BLE001
                        results.append({"status": "erro", "path": str(item), "reason": str(exc)[:200]})
    return results


def _same_or_parent(candidate: Path, protected_root: Path) -> bool:
    return candidate == protected_root or candidate == protected_root.parent


def _classify_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".docx", ".doc", ".odt", ".pages"}:
        return "documento_texto"
    if suffix in {".xlsx", ".xls", ".ods", ".csv"}:
        return "dados_tabela"
    if suffix in {".pptx", ".ppt", ".odp"}:
        return "apresentacao"
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".py", ".js", ".gs", ".html", ".css", ".json", ".yaml", ".yml", ".toml"}:
        return "codigo"
    if suffix in {".md", ".txt"}:
        return "texto"
    if suffix in IMAGE_EXTENSIONS:
        return "imagem"
    if suffix == ".zip":
        return "arquivo_zip"
    return "outro"


# --------------------------------------------------------------------------
# Nuvens locais (OneDrive / Google Drive / Nextcloud sincronizado)
# --------------------------------------------------------------------------

def ingest_local_clouds(store: CorpusStore, *, sources: list[Path], visibility: Visibility, staging: Path) -> list[dict[str, Any]]:
    roots = sources or discover_cloud_sources()
    roots = [item for item in roots if item.is_dir()]
    if not roots:
        log.info("nenhuma nuvem local sincronizada encontrada")
        return []
    return walk_and_ingest_all(store, roots, visibility=visibility, staging=staging)


# --------------------------------------------------------------------------
# OCR de imagens (opcional — exige tesseract)
# --------------------------------------------------------------------------

def run_ocr(images_dir: Path, store: CorpusStore, *, visibility: Visibility, lang: str = "por") -> list[dict[str, Any]]:
    if not images_dir.is_dir():
        log.info("pasta de imagens ausente: %s", images_dir)
        return []
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        log.warning("OCR indisponível: instale pytesseract e Pillow (e o binário tesseract-ocr)")
        return []
    results: list[dict[str, Any]] = []
    for image_path in sorted(images_dir.rglob("*")):
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}:
            continue
        try:
            from PIL import Image
            import pytesseract
            text = pytesseract.image_to_string(Image.open(image_path), lang=lang)
        except Exception as exc:  # noqa: BLE001 - OCR instável por imagem
            results.append({"status": "erro", "path": str(image_path), "reason": str(exc)[:200]})
            continue
        if not text.strip():
            results.append({"status": "ignorado", "path": str(image_path), "reason": "sem texto OCR"})
            continue
        out = images_dir.parent / "Processed" / f"{image_path.stem}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"# Texto extraído de {image_path.name}\n\n{text}", encoding="utf-8")
        results.append(store.ingest(out, visibility=visibility, extra_metadata={"document_type": "ocr"}))
    return results


# --------------------------------------------------------------------------
# Extração de referências bibliográficas
# --------------------------------------------------------------------------

# Padrões intencionais e restritos — evitam falsos positivos do original.
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+\b")
URL_PATTERN = re.compile(r"https?://[^\s)\"<>]+")
ISBN13_PATTERN = re.compile(r"\b97[89]\d{10}\b")
# Autor-ano só em linhas curtas e pontuadas: "Surname, A. (2020). Título."
AUTHOR_YEAR_PATTERN = re.compile(r"^[A-Z][A-Za-zÀ-ÿ'’.-]+,\s+[A-Z](?:\.[A-Z])*\.?\s*\(\d{4}\)\.?")
REFERENCE_HEADINGS = re.compile(
    r"^\s*#{0,6}\s*(?:refer[êe]ncias|bibliografia|references|bibliography|obras citadas)\b",
    flags=re.IGNORECASE,
)


def extract_references(text: str) -> list[dict[str, str]]:
    """Extrai referências bibliográficas com tipo identificado, sem duplicados."""
    found: dict[str, dict[str, str]] = {}
    for match in DOI_PATTERN.finditer(text):
        value = match.group(0).rstrip(".,);")
        found.setdefault(value, {"type": "doi", "value": value})
    for match in ISBN13_PATTERN.finditer(text):
        value = match.group(0)
        found.setdefault(value, {"type": "isbn13", "value": value})
    for match in URL_PATTERN.finditer(text):
        value = match.group(0).rstrip(".,);]")
        if not value.startswith(("http://doi.org", "https://doi.org")):
            found.setdefault(value, {"type": "url", "value": value})
    # Entradas numeradas/autor-ano apenas dentro de secções de referências.
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
        if AUTHOR_YEAR_PATTERN.match(stripped) and 10 <= len(stripped) <= 320:
            digest = sha256_bytes(stripped.encode("utf-8"))[:12]
            found.setdefault(f"ref:{digest}", {"type": "reference", "value": stripped})
    return list(found.values())


def extract_bibliography(corpus_root: Path, output: Path) -> dict[str, Any]:
    """Percorre o corpus já ingerido e agrega todas as referências encontradas."""
    references: list[dict[str, str]] = []
    files = 0
    for doc_path in sorted((corpus_root / "documents").glob("*.json")):
        try:
            document = json.loads(doc_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        files += 1
        references.extend(extract_references(document.get("text", "")))
    # Deduplica por (tipo, valor).
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for ref in references:
        unique[(ref["type"], ref["value"])] = ref
    ordered = sorted(unique.values(), key=lambda r: (r["type"], r["value"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output, {"generated_at": utc_now(), "count": len(ordered), "references": ordered})
    return {"files_scanned": files, "references": len(ordered), "path": str(output)}


# --------------------------------------------------------------------------
# Credenciais: variável de ambiente ou cofre DPAPI
# --------------------------------------------------------------------------

def resolve_secret(name: str, env_var: str) -> str | None:
    """Lê um segredo da variável de ambiente; nunca do código-fonte."""
    value = os.environ.get(env_var)
    if value:
        return value
    log.info("%s não definido em %s (modo local funciona sem credenciais externas)", name, env_var)
    return None


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Ingestão total MILK: bibliotecas externas, nuvens locais, OCR e bibliografia.",
    )
    result.add_argument("--state-dir", type=Path, default=Path.home() / "MILK_AI_STATE_CANONICO")
    result.add_argument("--visibility", choices=[item.value for item in Visibility], default=Visibility.RESTRICTED.value)
    result.add_argument("--library-adapter", help="módulo Python com library_search e open_library_result")
    result.add_argument("--libraries", help="ficheiro JSON com lista de IDs de bibliotecas")
    result.add_argument("--images-dir", type=Path, help="pasta de imagens para OCR")
    result.add_argument("--cloud-source", type=Path, action="append", default=[], help="raiz de nuvem local adicional")
    result.add_argument("--no-cloud", action="store_true", help="ignorar nuvens locais")
    result.add_argument("--no-libraries", action="store_true", help="ignorar bibliotecas externas")
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
    visibility = Visibility(args.visibility)
    report_path = (args.report or (state_dir / "INGESTAO_TOTAL_RELATORIO.json")).expanduser().resolve()

    libraries = DEFAULT_LIBRARIES
    if args.libraries:
        libraries = json.loads(Path(args.libraries).read_text(encoding="utf-8"))

    sections: dict[str, Any] = {}
    all_results: list[dict[str, Any]] = []

    # 1. Bibliotecas externas.
    if not args.no_libraries:
        search, opener = load_library_adapter(args.library_adapter)
        if search is _noop_library_search:
            log.warning("sem adaptador de bibliotecas: secção externa em modo demonstração (nada ingerido)")
            sections["libraries"] = {"status": "demonstracao", "documents": 0, "indexed": 0}
        else:
            documents = fetch_library_documents(libraries, search)
            staging = state_dir / "library_staging"
            lib_results = ingest_library_documents(documents, opener, store, staging=staging, visibility=visibility)
            all_results.extend(lib_results)
            counts = Counter(item.get("status", "desconhecido") for item in lib_results)
            sections["libraries"] = {
                "status": "concluido",
                "documents": len(documents),
                "counts": dict(sorted(counts.items())),
            }
    else:
        sections["libraries"] = {"status": "ignorado"}

    # 2. Nuvens locais (OneDrive, Nextcloud, etc. — com ZIP, OpenDocument, imagens).
    if not args.no_cloud:
        staging = state_dir / "staging"
        cloud_results = ingest_local_clouds(
            store, sources=args.cloud_source, visibility=visibility, staging=staging,
        )
        all_results.extend(cloud_results)
        counts = Counter(item.get("status", "desconhecido") for item in cloud_results)
        sections["local_clouds"] = {"counts": dict(sorted(counts.items())), "files_seen": len(cloud_results)}
    else:
        sections["local_clouds"] = {"status": "ignorado"}

    # 3. OCR.
    if args.images_dir:
        ocr_results = run_ocr(args.images_dir.expanduser().resolve(), store, visibility=visibility)
        all_results.extend(ocr_results)
        counts = Counter(item.get("status", "desconhecido") for item in ocr_results)
        sections["ocr"] = {"counts": dict(sorted(counts.items())), "images": len(ocr_results)}
    else:
        sections["ocr"] = {"status": "ignorado"}

    # 4. Bibliografia agregada.
    bib_path = state_dir / "bibliografia.json"
    sections["bibliography"] = extract_bibliography(store.root, bib_path)

    # Relatório + manifesto, no mesmo formato dos outros scripts do projecto.
    totals = Counter(item.get("status", "desconhecido") for item in all_results)
    documents = store.documents()
    report = {
        "generated_at": utc_now(),
        "state_dir": str(state_dir),
        "sections": sections,
        "totals": dict(sorted(totals.items())),
        "documents": len(documents),
        "chunks": sum(len(item.get("chunks", [])) for item in documents),
        "errors": [item for item in all_results if item.get("status") == "erro"],
    }
    atomic_json(report_path, report)
    atomic_json(state_dir / "MANIFEST_INGESTAO_TOTAL.json", build_manifest(_state_files(state_dir), state_dir))

    summary = {
        "status": "concluido_com_alertas" if totals.get("erro") else "concluido",
        "totals": dict(sorted(totals.items())),
        "documents": report["documents"],
        "chunks": report["chunks"],
        "references": sections["bibliography"]["references"],
        "report": str(report_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if totals.get("erro") else 0


def _state_files(state_dir: Path) -> Iterable[Path]:
    for path in state_dir.rglob("*"):
        if path.is_file():
            yield path


if __name__ == "__main__":
    raise SystemExit(main())
