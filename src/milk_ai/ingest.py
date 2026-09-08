from __future__ import annotations

import json
import os
import posixpath
import re
import unicodedata
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from .models import Chunk, EpistemicState, SourceMetadata, Visibility
from .provenance import atomic_json, sha256_bytes, sha256_file, utc_now
from .secret_scan import redact_secrets, scan_secrets


TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".py", ".html", ".htm", ".xml",
    ".gs", ".js", ".css", ".yaml", ".yml", ".toml", ".cff",
}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | {".docx", ".pdf", ".xlsx", ".pptx"}
DEFAULT_EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".tox", ".venv", "venv", "env",
    "__pycache__", "node_modules", "site-packages",
}
SENSITIVE_FILENAME = re.compile(
    r"(?:credencia|password|passwd|palavra[-_ ]?passe|senha|api[-_ ]?key|"
    r"client[-_ ]?secret|private[-_ ]?key|access[-_ ]?token|auth[-_ ]?token)",
    flags=re.IGNORECASE,
)


def _same_or_parent(candidate: Path, protected_root: Path) -> bool:
    """Impede que a ingestão leia o corpus ou o directório de estado que o contém."""
    return candidate == protected_root or candidate == protected_root.parent


def effective_suffix(path: Path) -> str:
    name = path.name.casefold()
    if name.endswith((".md colado", ".txt colado")):
        return ".md" if name.endswith(".md colado") else ".txt"
    return path.suffix.lower()


def _quality(text: str) -> int:
    return sum(text.count(token) for token in ("Ã", "Â", "â€", "�"))


def repair_mojibake(text: str) -> tuple[str, bool]:
    original_quality = _quality(text)
    if not original_quality:
        return unicodedata.normalize("NFC", text), False
    try:
        candidate = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return unicodedata.normalize("NFC", text), False
    if _quality(candidate) < original_quality:
        return unicodedata.normalize("NFC", candidate), True
    return unicodedata.normalize("NFC", text), False


def _read_text(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    notes: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            if encoding not in {"utf-8-sig", "utf-8"}:
                notes.append(f"descodificação de recuperação: {encoding}")
            repaired, changed = repair_mojibake(text)
            if changed:
                notes.append("mojibake reparado apenas na cópia indexada")
            return repaired, notes
        except UnicodeDecodeError:
            continue
    raise ValueError(f"não foi possível descodificar {path.name}")


def _read_docx(path: Path) -> tuple[str, list[str]]:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
        if text.strip():
            paragraphs.append(text.strip())
    return "\n\n".join(paragraphs), []


def _read_pdf(path: Path) -> tuple[str, list[str]]:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            return "", ["PDF ignorado: cabeçalho inválido ou placeholder sincronizado"]
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF exige a dependência pypdf fixada no projecto") from exc
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(text for text in pages if text), [f"PDF: {len(reader.pages)} páginas"]


def _read_xlsx(path: Path) -> tuple[str, list[str]]:
    spreadsheet_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    relationship_ns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    document_rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    with zipfile.ZipFile(path) as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.iter(f"{relationship_ns}Relationship")
        }
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.iter(f"{spreadsheet_ns}si"):
                shared.append("".join(node.text or "" for node in item.iter(f"{spreadsheet_ns}t")))

        sections: list[str] = []
        sheets = list(workbook.iter(f"{spreadsheet_ns}sheet"))
        for sheet in sheets:
            relation = sheet.attrib.get(f"{document_rel_ns}id", "")
            target = targets.get(relation, "")
            member = posixpath.normpath(posixpath.join("xl", target.lstrip("/")))
            if not target or member not in archive.namelist():
                continue
            root = ElementTree.fromstring(archive.read(member))
            rows: list[str] = []
            for row in root.iter(f"{spreadsheet_ns}row"):
                values: list[str] = []
                for cell in row.iter(f"{spreadsheet_ns}c"):
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find(f"{spreadsheet_ns}v")
                    if cell_type == "inlineStr":
                        value = "".join(node.text or "" for node in cell.iter(f"{spreadsheet_ns}t"))
                    elif value_node is None:
                        value = ""
                    elif cell_type == "s" and value_node.text:
                        index = int(value_node.text)
                        value = shared[index] if 0 <= index < len(shared) else ""
                    else:
                        value = value_node.text or ""
                    if value.strip():
                        values.append(value.strip())
                if values:
                    rows.append(" | ".join(values))
            if rows:
                sections.append(f"# FOLHA: {sheet.attrib.get('name', 'Sem nome')}\n\n" + "\n".join(rows))
    return "\n\n".join(sections), [f"XLSX: {len(sheets)} folhas"]


def _read_pptx(path: Path) -> tuple[str, list[str]]:
    drawing_ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        members = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda name: int(re.search(r"slide(\d+)\.xml$", name).group(1)),  # type: ignore[union-attr]
        )
        slides: list[str] = []
        for ordinal, member in enumerate(members, start=1):
            root = ElementTree.fromstring(archive.read(member))
            parts = [node.text.strip() for node in root.iter(f"{drawing_ns}t") if node.text and node.text.strip()]
            if parts:
                slides.append(f"# DIAPOSITIVO {ordinal}\n\n" + "\n".join(parts))
    return "\n\n".join(slides), [f"PPTX: {len(members)} diapositivos"]


def extract_text(path: Path) -> tuple[str, list[str]]:
    suffix = effective_suffix(path)
    if suffix in TEXT_EXTENSIONS:
        return _read_text(path)
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".xlsx":
        return _read_xlsx(path)
    if suffix == ".pptx":
        return _read_pptx(path)
    raise ValueError(f"formato não suportado: {suffix}")


def semantic_chunks(text: str, max_chars: int = 1400, overlap: int = 180) -> list[tuple[str | None, str]]:
    if max_chars < 400 or overlap >= max_chars:
        raise ValueError("configuração de chunk inválida")
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    heading: str | None = None
    units: list[tuple[str | None, str]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            value = " ".join(part.strip() for part in paragraph if part.strip()).strip()
            if value:
                units.append((heading, value))
            paragraph.clear()

    for line in lines:
        stripped = line.strip()
        is_heading = bool(
            stripped.startswith("#")
            or re.match(r"^\d+(?:\.\d+)*[.)]?\s+\S", stripped)
            or (stripped.isupper() and " " in stripped and 8 <= len(stripped) <= 120)
        )
        if is_heading:
            flush()
            heading = stripped.lstrip("# ")
        elif not stripped:
            flush()
        else:
            paragraph.append(stripped)
    flush()

    chunks: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current = ""
    for unit_heading, unit in units:
        if len(unit) > max_chars:
            if current:
                chunks.append((current_heading, current))
                current = ""
            step = max_chars - overlap
            for start in range(0, len(unit), step):
                piece = unit[start:start + max_chars].strip()
                if piece:
                    chunks.append((unit_heading, piece))
            continue
        candidate = f"{current}\n\n{unit}".strip() if current else unit
        if current and (len(candidate) > max_chars or unit_heading != current_heading):
            chunks.append((current_heading, current))
            tail = current[-overlap:].lstrip() if overlap else ""
            current = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            current = candidate
        current_heading = unit_heading
    if current:
        chunks.append((current_heading, current))
    return chunks


class CorpusStore:
    def __init__(self, root: Path):
        self.root = root
        self.documents_dir = root / "documents"
        self.quarantine_dir = root / "quarantine"
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def ingest(
        self,
        path: Path,
        *,
        visibility: Visibility = Visibility.RESTRICTED,
        extra_metadata: dict[str, Any] | None = None,
        secret_mode: str = "quarantine",
    ) -> dict[str, Any]:
        path = Path(os.path.abspath(path))
        if not path.is_file():
            raise FileNotFoundError(path)
        if effective_suffix(path) not in SUPPORTED_EXTENSIONS:
            return {"status": "ignorado", "path": str(path), "reason": "formato não suportado"}
        digest = sha256_file(path)
        target = self.documents_dir / f"{digest}.json"
        quarantine_target = self.quarantine_dir / f"{digest}.json"
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            provenance = existing.setdefault("provenance_paths", [])
            if str(path) not in provenance:
                provenance.append(str(path))
                atomic_json(target, existing)
            return {"status": "existente", "sha256": digest, "source_id": existing["metadata"]["source_id"]}

        if quarantine_target.exists() and secret_mode == "quarantine":
            return {"status": "quarentena_existente", "sha256": digest, "source_id": f"sha256:{digest}", "text_stored": False}

        if secret_mode not in {"quarantine", "redact"}:
            raise ValueError("secret_mode deve ser quarantine ou redact")

        if SENSITIVE_FILENAME.search(path.name) and secret_mode == "quarantine":
            record = {
                "source_id": f"sha256:{digest}",
                "original_name": path.name,
                "original_path": str(path),
                "sha256": digest,
                "size_bytes": path.stat().st_size,
                "quarantined_at": utc_now(),
                "reason": "nome do ficheiro indica possível conteúdo credencial",
                "findings": [],
                "text_stored": False,
            }
            atomic_json(quarantine_target, record)
            return {
                "status": "quarentena",
                "sha256": digest,
                "source_id": f"sha256:{digest}",
                "reason": "nome sensível",
                "text_stored": False,
            }

        text, notes = extract_text(path)
        if not text.strip():
            return {"status": "ignorado", "path": str(path), "reason": "sem texto extraível"}
        source_id = f"sha256:{digest}"
        secret_findings = scan_secrets(text)
        if secret_findings and secret_mode == "quarantine":
            record = {
                "source_id": source_id,
                "original_name": path.name,
                "original_path": str(path),
                "sha256": digest,
                "size_bytes": path.stat().st_size,
                "quarantined_at": utc_now(),
                "reason": "potenciais credenciais detectadas",
                "findings": [finding.public_dict() for finding in secret_findings],
                "text_stored": False,
            }
            atomic_json(quarantine_target, record)
            return {
                "status": "quarentena",
                "sha256": digest,
                "source_id": source_id,
                "findings": len(secret_findings),
                "text_stored": False,
            }
        if secret_findings:
            text = redact_secrets(text, secret_findings)
            notes.append(f"{len(secret_findings)} potenciais segredos ocultados na cópia indexada")
        metadata = SourceMetadata(
            source_id=source_id,
            original_name=path.name,
            original_path=str(path),
            sha256=digest,
            size_bytes=path.stat().st_size,
            ingested_at=utc_now(),
            visibility=visibility,
            epistemic_state=EpistemicState.PREPARED,
            notes=notes,
        )
        if extra_metadata:
            allowed = set(asdict(metadata))
            protected = {"source_id", "sha256", "size_bytes", "original_name", "original_path", "ingested_at", "visibility", "epistemic_state"}
            for key, value in extra_metadata.items():
                if key in allowed and key not in protected:
                    setattr(metadata, key, value)

        chunk_values = semantic_chunks(text)
        chunks: list[dict[str, Any]] = []
        for ordinal, (heading, value) in enumerate(chunk_values):
            indexed_value = f"{heading}\n\n{value}" if heading else value
            chunk_digest = sha256_bytes(indexed_value.encode("utf-8"))
            chunks.append(
                Chunk(
                    chunk_id=f"{source_id}#chunk-{ordinal:05d}-{chunk_digest[:12]}",
                    source_id=source_id,
                    ordinal=ordinal,
                    text=indexed_value,
                    heading=heading,
                    sha256=chunk_digest,
                    metadata={
                        "visibility": metadata.visibility.value,
                        "epistemic_state": metadata.epistemic_state.value,
                        "original_name": metadata.original_name,
                        "rights_status": metadata.rights_status,
                        "consent_status": metadata.consent_status,
                        "rgpd_status": metadata.rgpd_status,
                        "human_validated": metadata.human_validated,
                        "territory": metadata.territory,
                        "municipality": metadata.municipality,
                        "parish": metadata.parish,
                    },
                ).to_dict()
            )
        atomic_json(
            target,
            {
                "metadata": metadata.to_dict(),
                "provenance_paths": [str(path)],
                "text": text,
                "chunks": chunks,
            },
        )
        if secret_mode == "redact":
            quarantine_target.unlink(missing_ok=True)
        return {"status": "indexado", "sha256": digest, "source_id": source_id, "chunks": len(chunks)}

    def ingest_tree(
        self,
        path: Path,
        *,
        include_dependencies: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        path = Path(os.path.abspath(path))
        candidates: Iterable[Path]
        if path.is_file():
            candidates = [path]
        else:
            discovered: list[Path] = []
            protected_root = Path(os.path.abspath(self.root))
            for root, directories, filenames in os.walk(path, followlinks=False):
                root_path = Path(root)
                directories[:] = [
                    name for name in directories
                    if not (root_path / name).is_symlink()
                    and (include_dependencies or name.casefold() not in DEFAULT_EXCLUDED_DIRS)
                    and not _same_or_parent(Path(os.path.abspath(root_path / name)), protected_root)
                ]
                for filename in filenames:
                    item = root_path / filename
                    if not item.is_symlink():
                        discovered.append(item)
            candidates = sorted(discovered)
        results: list[dict[str, Any]] = []
        for item in candidates:
            try:
                results.append(self.ingest(item, **kwargs))
            except Exception as exc:
                results.append({
                    "status": "erro",
                    "path": str(item),
                    "error_type": type(exc).__name__,
                    "reason": str(exc)[:500],
                })
        return results

    def update_governance(
        self,
        source_id: str,
        changes: dict[str, Any],
        *,
        actor: str,
        reason: str,
        human_approval: bool,
    ) -> dict[str, Any]:
        if not human_approval:
            raise PermissionError("alteração de governação exige aprovação humana explícita")
        if not actor.strip() or not reason.strip():
            raise ValueError("responsável e fundamento são obrigatórios")
        allowed = {
            "visibility",
            "rights_status",
            "consent_status",
            "rgpd_status",
            "human_validated",
            "validated_by",
            "validation_date",
            "epistemic_state",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"campos de governação não permitidos: {sorted(unknown)}")
        digest = source_id.removeprefix("sha256:")
        target = self.documents_dir / f"{digest}.json"
        if not target.exists():
            raise KeyError(source_id)
        document = json.loads(target.read_text(encoding="utf-8"))
        before = {key: document["metadata"].get(key) for key in changes}
        document["metadata"].update(changes)
        propagated = {
            key: value for key, value in changes.items()
            if key in {"visibility", "rights_status", "consent_status", "rgpd_status", "human_validated", "epistemic_state"}
        }
        for chunk in document.get("chunks", []):
            chunk.setdefault("metadata", {}).update(propagated)
        log_entry = {
            "at": utc_now(),
            "actor": actor.strip(),
            "reason": reason.strip(),
            "before": before,
            "after": changes,
        }
        document.setdefault("governance_log", []).append(log_entry)
        atomic_json(target, document)
        return {"source_id": source_id, "updated": sorted(changes), "audit": log_entry}

    def documents(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.documents_dir.glob("*.json"))]

    def chunks(self) -> list[dict[str, Any]]:
        return [chunk for document in self.documents() for chunk in document.get("chunks", [])]
