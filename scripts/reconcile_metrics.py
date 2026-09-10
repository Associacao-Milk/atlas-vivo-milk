#!/usr/bin/env python3
"""MILK Metric Reconciliation — filesystem_bytes vs extracted_text_bytes.

Explains the 268 MB (extracted text) vs 779.3 MB (filesystem) discrepancy.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
OUT = ROOT / "state" / "metric_reconciliation.json"

def dir_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except: pass
    return total

def count_json_docs(path: Path) -> tuple[int, int, int]:
    """Count docs, total JSON file bytes, total extracted text bytes."""
    docs = 0
    json_bytes = 0
    text_bytes = 0
    for f in sorted(path.glob("*.json")):
        docs += 1
        json_bytes += f.stat().st_size
        try:
            d = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            text = d.get("text", "") or ""
            text_bytes += len(text.encode("utf-8"))
            for chunk in d.get("chunks", []):
                ct = chunk.get("text", "") or ""
                text_bytes += len(ct.encode("utf-8"))
        except: pass
    return docs, json_bytes, text_bytes

def main():
    print("MILK METRIC RECONCILIATION", flush=True)
    corpus_dir = ROOT / "corpus" / "documents"

    # Filesystem size of corpus
    fs_bytes = dir_size(corpus_dir)
    fs_mb = round(fs_bytes / 1e6, 1)

    # JSON docs and extracted text
    docs, json_bytes, text_bytes = count_json_docs(corpus_dir)
    json_mb = round(json_bytes / 1e6, 1)
    text_mb = round(text_bytes / 1e6, 1)

    # Total repo filesystem size (excluding lib, models, corpus)
    repo_fs = 0
    for item in ROOT.iterdir():
        if item.name in ("lib", "models", "corpus", ".git", "__pycache__"):
            continue
        if item.is_dir():
            repo_fs += dir_size(item)
        elif item.is_file():
            repo_fs += item.stat().st_size
    repo_mb = round(repo_fs / 1e6, 1)

    report = {
        "schema": "ia_milk.metric_reconciliation.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "doc_count": docs,
            "filesystem_bytes": fs_bytes,
            "filesystem_mb": fs_mb,
            "json_file_bytes": json_bytes,
            "json_file_mb": json_mb,
            "extracted_text_bytes": text_bytes,
            "extracted_text_mb": text_mb,
        },
        "repo_non_corpus": {
            "filesystem_bytes": repo_fs,
            "filesystem_mb": repo_mb,
        },
        "explanation": {
            "filesystem_mb": f"{fs_mb} MB = total size of all JSON files on disk (including JSON structure, metadata, chunk objects, base64, etc.)",
            "extracted_text_mb": f"{text_mb} MB = total bytes of extracted text content (document.text + chunk.text fields, UTF-8 encoded)",
            "ratio": round(fs_mb / text_mb, 2) if text_mb > 0 else None,
            "note": "268 MB (historical 'extracted text') vs 779.3 MB (filesystem JSON) discrepancy explained: filesystem includes JSON structure, metadata fields, chunk metadata, provenance info, and encoding overhead. Extracted text is the pure content bytes.",
            "canonical_definition": "filesystem_bytes = du -sh corpus/documents; extracted_text_bytes = sum(len(text.encode('utf-8')) for all documents and chunks)",
        },
        "quarantine": {
            "count": len(list((ROOT / "corpus" / "quarantine").iterdir())) if (ROOT / "corpus" / "quarantine").is_dir() else 0,
        }
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Docs: {docs}")
    print(f"  Filesystem: {fs_mb} MB")
    print(f"  JSON files: {json_mb} MB")
    print(f"  Extracted text: {text_mb} MB")
    print(f"  Ratio: {report['explanation']['ratio']}x")
    print(f"  Saved: {OUT}")

if __name__ == "__main__":
    main()
