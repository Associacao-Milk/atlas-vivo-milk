from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .connectors import RORConnector
from .models import AtlasRecord, MigrationStatus


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def migration_status(manifest_path: str) -> MigrationStatus:
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    summary = data.get("summary", data)
    return MigrationStatus(
        discovered_files=summary.get("files", summary.get("total_files", 0)),
        discovered_folders=summary.get("folders", summary.get("total_folders", 0)),
        discovered_bytes=summary.get("bytes", summary.get("total_bytes", 0)),
        transferred=summary.get("transferred", 0), verified=summary.get("verified", 0),
        existing=summary.get("existing", 0), failed=summary.get("failed", 0),
        transferred_bytes=summary.get("transferred_bytes", 0))


def main() -> None:
    parser = argparse.ArgumentParser(prog="atlas-integrations")
    sub = parser.add_subparsers(dest="command", required=True)
    ror = sub.add_parser("ror-search")
    ror.add_argument("query")
    mig = sub.add_parser("migration-status")
    mig.add_argument("manifest")
    val = sub.add_parser("validate-record")
    val.add_argument("record")
    args = parser.parse_args()
    if args.command == "ror-search":
        _json(RORConnector(os.getenv("ROR_CLIENT_ID")).search(args.query))
    elif args.command == "migration-status":
        _json(migration_status(args.manifest).model_dump())
    elif args.command == "validate-record":
        record = AtlasRecord.model_validate_json(Path(args.record).read_text(encoding="utf-8"))
        _json({"valid": True, "canonical_hash": record.canonical_hash()})


if __name__ == "__main__":
    main()

