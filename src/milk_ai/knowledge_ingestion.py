"""MILK Knowledge Ingestion Pipeline — incremental, staged, sovereign.

Pipeline: SCAN_DELTA → STAGE → VALIDATE → CLASSIFY → DEDUP → ENRICH → PROMOTE
→ INDEX → VERIFY.

Does NOT modify existing corpus documents. Adds only new items through staging.
Uses existing provenance, compliance, and semantic infrastructure.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_CORPUS = _ROOT / "corpus" / "documents"
_STAGING = _ROOT / "corpus" / "staging"
_CHECKPOINT = _ROOT / "state" / "knowledge_ingestion_checkpoint.json"
_LIBRARY_LOG = _ROOT / "state" / "knowledge_ingestion_log.jsonl"


def _now():
    return datetime.now(timezone.utc).isoformat()

def _sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def _uuid():
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Staged item with full provenance
# ---------------------------------------------------------------------------

class StagedItem:
    """A staged item awaiting validation and promotion."""

    def __init__(self, *, source: str, source_id: str, source_uri: str,
                 content: bytes, content_hash: str, original_name: str = "",
                 size: int = 0, mtime: str = ""):
        self.document_id = _sha256(content_hash + source)[:64]  # stable ID
        self.source = source
        self.source_id = source_id
        self.source_uri = source_uri
        self.content = content
        self.content_hash = content_hash
        self.original_name = original_name or source_id
        self.size = size or len(content)
        self.mtime = mtime
        self.ingested_at = _now()

        # Classification (filled during pipeline)
        self.mime_type = ""
        self.language = "pt"
        self.licence = "UNKNOWN"
        self.rights_status = "unknown"
        self.privacy_class = "UNKNOWN"
        self.dedup_status = "NEW"
        self.content_quality = 0.0
        self.semantic_tags: list[str] = []
        self.territory = ""
        self.municipality = ""
        self.claims: list[str] = []
        self.pipeline_decision = "PENDING"  # ACCEPT, REVIEW, QUARANTINE, REJECT
        self.provenance: list[dict] = []
        # Trust / publication boundary
        self.trust_state = "untrusted"
        self.human_validated = False
        self.public_eligible = False
        self.epistemic_state = "uncorroborated"
        # Encoding
        self.encoding_ok = True
        self.encoding_issues: list[str] = []
        self.normalized_text = ""
        # Disposition
        self.disposition_reason = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "content"}

    def to_canonical(self) -> dict:
        """Convert to canonical corpus document format (compatible with existing)."""
        text = self.content.decode("utf-8", errors="replace")[:10000]
        return {
            "hash": self.document_id,
            "text": text,
            "chunks": [],  # will be filled by chunker
            "source": self.source,
            "source_id": self.source_id,
            "source_uri": self.source_uri,
            "original_name": self.original_name,
            "ingested_at": self.ingested_at,
            "content_hash": self.content_hash,
            "mime_type": self.mime_type,
            "language": self.language,
            "licence": self.licence,
            "rights_status": self.rights_status,
            "privacy_class": self.privacy_class,
            "territory": self.territory,
            "municipality": self.municipality,
            "semantic_tags": self.semantic_tags,
            "pipeline_decision": self.pipeline_decision,
            "pipeline_version": "ingest-v1",
            "provenance": self.provenance,
            "trust_state": self.trust_state,
            "human_validated": self.human_validated,
            "public_eligible": self.public_eligible,
            "epistemic_state": self.epistemic_state,
            "rights_status": self.rights_status,
            "encoding_ok": self.encoding_ok,
            "encoding_issues": self.encoding_issues,
        }


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

class KnowledgeIngestionPipeline:
    """Full ingestion pipeline: SCAN → STAGE → VALIDATE → CLASSIFY → DEDUP
    → ENRICH → PROMOTE → INDEX → VERIFY."""

    PIPELINE_VERSION = "ingest-v1"

    def __init__(self, corpus_dir: Path | None = None,
                 staging_dir: Path | None = None,
                 checkpoint_path: Path | None = None,
                 log_path: Path | None = None):
        self.corpus = corpus_dir or _CORPUS
        self.staging = staging_dir or _STAGING
        self.checkpoint_path = checkpoint_path or _CHECKPOINT
        self.log_path = log_path or _LIBRARY_LOG
        self.staging.mkdir(parents=True, exist_ok=True)
        self._existing_hashes: set[str] | None = None
        self._checkpoint: dict = self._load_checkpoint()

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        return {"processed_hashes": [], "sources": {}, "last_run": ""}

    def _save_checkpoint(self):
        self._checkpoint["last_run"] = _now()
        self.checkpoint_path.write_text(json.dumps(self._checkpoint, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    def _get_existing_hashes(self) -> set[str]:
        """Get content hashes of existing corpus documents (lazy, cached)."""
        if self._existing_hashes is not None:
            return self._existing_hashes
        hashes = set()
        # Load from checkpoint first
        for h in self._checkpoint.get("processed_hashes", []):
            hashes.add(h)
        # Also check a sample of existing files
        for f in sorted(self.corpus.glob("*.json"))[:500]:
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
                ch = doc.get("content_hash", "")
                if ch:
                    hashes.add(ch)
            except Exception:
                pass
        self._existing_hashes = hashes
        return hashes

    # ---- STAGE: create staged items from delta ----

    def stage_items(self, delta_items: list[dict]) -> list[StagedItem]:
        """Stage items from delta discovery."""
        staged = []
        existing = self._get_existing_hashes()
        processed = set(self._checkpoint.get("processed_hashes", []))

        for item in delta_items:
            ch = item.get("content_hash", "")
            if ch in existing or ch in processed:
                continue  # already in corpus or processed

            # Read content from source
            source_uri = Path(item["source_uri"])
            try:
                if not source_uri.exists():
                    continue
                content = source_uri.read_bytes()[:50000]  # limit size
            except Exception:
                continue

            # Skip empty or tiny files
            if len(content) < 20:
                continue

            # Verify hash matches
            actual_hash = _sha256(content[:5000])
            if actual_hash != ch:
                # Hash was computed on first 5000 bytes — use actual
                ch = actual_hash

            staged_item = StagedItem(
                source=item["source"],
                source_id=item["source_id"],
                source_uri=item["source_uri"],
                content=content,
                content_hash=ch,
                original_name=item.get("source_id", ""),
                size=len(content),
                mtime=item.get("mtime", ""),
            )
            staged.append(staged_item)

        return staged

    # ---- VALIDATE: MIME type, size, safety, encoding ----

    def check_encoding(self, item: StagedItem):
        """Detect UTF-8/mojibake issues in content."""
        try:
            text = item.content.decode("utf-8", errors="replace")
        except Exception:
            text = ""

        mojibake_patterns = ["Ã", "â€", "ï¿½", "Ã©", "Ã³", "Ã¡", "Ã§"]
        issues = []
        for pat in mojibake_patterns:
            if pat in text:
                issues.append(f"mojibake_pattern:{pat}")

        if issues:
            item.encoding_ok = False
            item.encoding_issues = issues
            item.disposition_reason = "encoding_issues"
            # Don't reject — produce normalized_text if safe
            try:
                # Try latin-1 to utf-8 fix
                fixed = item.content.decode("latin-1").encode("utf-8").decode("utf-8", errors="replace")
                if fixed and not any(p in fixed for p in mojibake_patterns):
                    item.normalized_text = fixed[:10000]
            except Exception:
                pass
        else:
            item.encoding_ok = True
            item.normalized_text = text[:10000]

    def validate(self, item: StagedItem) -> bool:
        """Validate MIME type and content safety."""
        ext = Path(item.original_name).suffix.lower()
        mime_map = {".txt": "text/plain", ".md": "text/markdown",
                   ".json": "application/json", ".pdf": "application/pdf",
                   ".docx": "application/vnd.openxmlformats-officedocument",
                   ".xlsx": "application/vnd.openxmlformats-officedocument"}
        item.mime_type = mime_map.get(ext, "application/octet-stream")

        # Safety: check for prompt injection patterns in content
        try:
            text = item.content.decode("utf-8", errors="replace").lower()
            injection_patterns = ["ignore previous instructions", "system prompt:",
                                "you are now", "disregard all", "forget your rules"]
            for pattern in injection_patterns:
                if pattern in text:
                    item.pipeline_decision = "QUARANTINE"
                    item.provenance.append({"stage": "validate", "result": "prompt_injection_detected"})
                    return False
        except Exception:
            pass

        # Size limit: 100KB
        if item.size > 100000:
            item.pipeline_decision = "REVIEW"
            item.provenance.append({"stage": "validate", "result": "large_file_review"})
            return True  # still process, but flag for review

        item.provenance.append({"stage": "validate", "result": "passed"})
        return True

    # ---- CLASSIFY: privacy, licence, legal ----

    def classify(self, item: StagedItem):
        """Classify privacy, licence, and legal status."""
        try:
            text = item.content.decode("utf-8", errors="replace").lower()
        except Exception:
            text = ""

        # Privacy classification
        personal_patterns = ["nome:", "bi:", "cartão", "nif:", "morada:",
                            "telefone:", "email:", "password", "senha"]
        special_patterns = ["saúde", "médico", "doença", "diagnóstico",
                           "religião", "crença", "orientação sexual",
                           "convicção política"]

        has_personal = any(p in text for p in personal_patterns)
        has_special = any(p in text for p in special_patterns)

        if has_special:
            item.privacy_class = "SPECIAL_CATEGORY"
            item.pipeline_decision = "QUARANTINE"
        elif has_personal:
            item.privacy_class = "PERSONAL_DATA"
            item.pipeline_decision = "REVIEW_REQUIRED"
        else:
            item.privacy_class = "INTERNAL"
            item.licence = "UNKNOWN"
            item.rights_status = "internal_preservation"

        # Licence detection
        licence_patterns = {
            "EUPL-1.2": ["eupl-1.2", "eupl 1.2", "união europeia"],
            "CC-BY": ["cc-by", "creative commons"],
            "CC0": ["cc0", "public domain"],
            " proprietary": ["all rights reserved", "confidential"],
        }
        for licence, patterns in licence_patterns.items():
            if any(p in text for p in patterns):
                item.licence = licence
                break

        item.provenance.append({"stage": "classify", "result": "classified",
                               "privacy": item.privacy_class, "licence": item.licence})

    # ---- DEDUP: exact and near-duplicate ----

    def dedup(self, item: StagedItem, all_staged: list[StagedItem]):
        """Check for exact and near duplicates."""
        existing = self._get_existing_hashes()

        # Exact duplicate
        if item.content_hash in existing:
            item.dedup_status = "EXACT_DUPLICATE"
            item.pipeline_decision = "REJECT"
            return

        # Check against other staged items
        for other in all_staged:
            if other is item or other.dedup_status == "EXACT_DUPLICATE":
                continue
            if other.content_hash == item.content_hash:
                item.dedup_status = "EXACT_DUPLICATE"
                item.pipeline_decision = "REJECT"
                return

        # Near-duplicate: check first 100 chars overlap
        try:
            text = item.content.decode("utf-8", errors="replace")[:200]
        except Exception:
            text = ""
        for other in all_staged:
            if other is item:
                continue
            try:
                other_text = other.content.decode("utf-8", errors="replace")[:200]
            except Exception:
                continue
            if text[:100] == other_text[:100] and item.content_hash != other.content_hash:
                item.dedup_status = "NEAR_DUPLICATE"
                item.pipeline_decision = "REVIEW"
                return

        item.dedup_status = "NEW"
        item.provenance.append({"stage": "dedup", "result": "NEW"})

    # ---- ENRICH: extract metadata, territory, tags ----

    def enrich(self, item: StagedItem):
        """Extract metadata, territory, semantic tags."""
        try:
            text = item.content.decode("utf-8", errors="replace")
        except Exception:
            text = ""

        # Territory extraction (Portuguese municipalities)
        pt_municipalities = ["lisboa", "porto", "braga", "coimbra", "faro", "evora",
                            "aveiro", "leiria", "viseu", "setubal", "guarda", "beja",
                            "portalegre", "castelo branco", "viana do castelo",
                            "vila real", "braganca", "santarem"]
        text_lower = text.lower()
        for muni in pt_municipalities:
            if muni in text_lower:
                item.municipality = muni
                item.territory = muni
                break

        # Semantic tags
        tag_patterns = {
            "folklore": ["folclore", "folklore", "tradição", "tradicao", "lenda", "romaria"],
            "music": ["música", "musica", "canto", "instrumento", "coro"],
            "dance": ["dança", "danca", "baile", "rancho"],
            "culture": ["cultura", "património", "patrimonio", "imaterial"],
            "territory": ["freguesia", "município", "municipio", "distrito", "território"],
            "festival": ["festival", "festa", "romaria", "feira"],
            "technology": ["digital", "tecnologia", "web", "api", "software"],
            "governance": ["governação", "governacao", "política", "politica", "lei"],
        }
        for tag, patterns in tag_patterns.items():
            if any(p in text_lower for p in patterns):
                item.semantic_tags.append(tag)

        # Content quality (simple: based on text length and diversity)
        words = set(text_lower.split())
        item.content_quality = min(1.0, len(words) / 200)

        # Claims extraction (first 3 sentences)
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        item.claims = sentences[:3]

        item.provenance.append({"stage": "enrich", "result": "enriched",
                               "tags": item.semantic_tags, "territory": item.territory})

    # ---- PROMOTE: add to canonical corpus ----

    def promote(self, item: StagedItem) -> bool:
        """Promote a staged item to the canonical corpus."""
        if item.pipeline_decision not in ("ACCEPT", "PENDING"):
            if item.pipeline_decision == "REVIEW_REQUIRED":
                item.pipeline_decision = "REVIEW"
                return False
            return False

        # Final decision: accept if privacy_class is INTERNAL or PUBLIC
        if item.privacy_class in ("SPECIAL_CATEGORY", "PERSONAL_DATA"):
            item.pipeline_decision = "REVIEW"
            return False

        item.pipeline_decision = "ACCEPT"

        # Trust / publication boundary
        item.trust_state = "trusted_internal"
        item.human_validated = False  # not yet human-validated
        item.public_eligible = False  # licence UNKNOWN = not public
        item.epistemic_state = "uncorroborated"
        item.rights_status = "internal_preservation_only"

        # Generate chunks (simple: text split into 500-char chunks)
        text = item.content.decode("utf-8", errors="replace")
        chunks = []
        for i in range(0, min(len(text), 10000), 500):
            chunk_text = text[i:i+500]
            if chunk_text.strip():
                chunks.append({
                    "chunk_id": f"{item.document_id[:16]}_{i//500}",
                    "text": chunk_text,
                    "sha256": _sha256(chunk_text.encode("utf-8")),
                })

        # Create canonical document
        doc = item.to_canonical()
        doc["chunks"] = chunks

        # Write to corpus (new file, never overwrite)
        output_path = self.corpus / f"{item.document_id}.json"
        if output_path.exists():
            # Already exists (shouldn't happen with dedup, but safety)
            item.pipeline_decision = "EXACT_DUPLICATE"
            return False

        output_path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

        # Update checkpoint
        self._checkpoint.setdefault("processed_hashes", []).append(item.content_hash)
        self._checkpoint.setdefault("promoted_documents", []).append(item.document_id)

        item.provenance.append({"stage": "promote", "result": "accepted",
                               "document_path": str(output_path), "chunks": len(chunks)})

        # Log to ingestion log
        log_entry = {
            "timestamp": _now(),
            "document_id": item.document_id,
            "source": item.source,
            "source_id": item.source_id,
            "content_hash": item.content_hash,
            "decision": "ACCEPT",
            "chunks": len(chunks),
            "privacy_class": item.privacy_class,
            "licence": item.licence,
            "tags": item.semantic_tags,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return True

    # ---- Full pipeline run ----

    def run(self, delta_items: list[dict]) -> dict:
        """Run the full pipeline on delta items."""
        results = {
            "pipeline_version": self.PIPELINE_VERSION,
            "timestamp": _now(),
            "discovered": len(delta_items),
            "documents_before": len(list(self.corpus.glob("*.json"))),
            "staged": 0,
            "skipped": 0,
            "skipped_items": [],
            "validated": 0,
            "classified": 0,
            "deduped_new": 0,
            "deduped_duplicates": 0,
            "enriched": 0,
            "accepted": 0,
            "review_required": 0,
            "quarantined": 0,
            "rejected": 0,
            "encoding_issues": 0,
            "chunks_added": 0,
            "documents_after": 0,
            "items": [],
        }

        # STAGE
        staged = self.stage_items(delta_items)
        results["staged"] = len(staged)
        results["skipped"] = len(delta_items) - len(staged)

        # Track skipped items for accounting
        staged_hashes = set()
        for s in staged:
            staged_hashes.add(s.content_hash)
        for d in delta_items:
            ch = d.get("content_hash", "")
            if ch not in staged_hashes:
                results["skipped_items"].append({
                    "source": d.get("source", ""),
                    "source_id": d.get("source_id", ""),
                    "reason": "not_staged",
                })

        for item in staged:
            # ENCODING CHECK
            self.check_encoding(item)
            if not item.encoding_ok:
                results["encoding_issues"] += 1

            # VALIDATE
            if not self.validate(item):
                results["quarantined"] += 1
                item.disposition_reason = "validation_failed"
                results["items"].append(item.to_dict())
                continue
            results["validated"] += 1

            # CLASSIFY
            self.classify(item)
            results["classified"] += 1

            # DEDUP
            self.dedup(item, staged)
            if item.dedup_status == "EXACT_DUPLICATE":
                results["deduped_duplicates"] += 1
                results["rejected"] += 1
                item.disposition_reason = "exact_duplicate"
                results["items"].append(item.to_dict())
                continue
            results["deduped_new"] += 1

            # ENRICH
            self.enrich(item)
            results["enriched"] += 1

            # PROMOTE
            if self.promote(item):
                results["accepted"] += 1
                # Count chunks from the canonical doc (already written)
                try:
                    doc = json.loads((self.corpus / f"{item.document_id}.json").read_text(encoding="utf-8"))
                    results["chunks_added"] += len(doc.get("chunks", []))
                except Exception:
                    pass
            elif item.pipeline_decision == "REVIEW":
                results["review_required"] += 1
                item.disposition_reason = "review_required"
            elif item.pipeline_decision == "QUARANTINE":
                results["quarantined"] += 1
                item.disposition_reason = "quarantined"

            results["items"].append(item.to_dict())

        results["documents_after"] = len(list(self.corpus.glob("*.json")))

        # Verify disposition invariant
        accounted = (results["accepted"] + results["review_required"] +
                     results["quarantined"] + results["rejected"] + results["skipped"])
        results["unaccounted_items"] = results["discovered"] - accounted

        self._save_checkpoint()

        return results
