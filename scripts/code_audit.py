#!/usr/bin/env python3
"""MILK First-Party Code Audit — risk classification of MILK source code.

Scans only FIRST-PARTY code:
  milk_*.py, src/milk_ai/, integrations/, scripts/, atlas_infra/

Excludes:
  lib/torch, venv/.venv, models, node_modules, caches, logs, snapshots/backups

Classifications:
  broad exceptions, process execution, network code, hardcoded paths,
  potential secret assignments, TODO/FIXME/HACK

Never prints secret values.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
OUT = ROOT / "state" / "code_audit_report.json"

# Patterns
BROAD_EXCEPTION = re.compile(r"except\s*:|except\s+Exception\s*:|except\s+BaseException\s*:|bare\s+except", re.I)
PROCESS_EXEC = re.compile(r"subprocess\.(run|call|Popen|check_output|check_call)|os\.system\(|os\.popen\(|eval\(|exec\(", re.I)
NETWORK_CODE = re.compile(r"urllib|requests\.(get|post|put|delete|patch)|http\.client|socket\.connect|urlopen", re.I)
HARDCODED_PATH = re.compile(r"[A-Z]:\\\\|/c/Users/|C:\\\\Users\\\\|/home/", re.I)
SECRET_ASSIGN = re.compile(r"(password|secret|token|api_key|apikey|access_key|private_key)\s*[=:]\s*['\"][^'\"]{8,}", re.I)
TODO_FIXME = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|WORKAROUND)", re.I)

EXCLUDE_DIRS = {"lib", "__pycache__", "node_modules", ".git", "venv", ".venv",
                "models", "caches", "logs", "snapshots", "backup_pre_retrain",
                "snapshot_retrain_5f727f5", "corpus"}

FIRST_PARTY_PATTERNS = [
    "milk_*.py",
    "src/milk_ai/*.py",
    "scripts/*.py",
    "integrations/**/*.py",
    "atlas_infra/backend/src/**/*.js",
    "atlas_infra/backend/src/**/*.ts",
    "*.py",
]

def should_scan(path: Path) -> bool:
    parts = str(path.relative_to(ROOT))
    for ex in EXCLUDE_DIRS:
        if ex in parts:
            return False
    return True

def scan_file(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"file": str(path), "error": "read failed"}

    findings = {
        "broad_exceptions": [],
        "process_execution": [],
        "network_code": [],
        "hardcoded_paths": [],
        "potential_secrets": [],
        "todo_fixme": [],
    }

    for i, line in enumerate(content.split("\n"), 1):
        if BROAD_EXCEPTION.search(line):
            findings["broad_exceptions"].append({"line": i, "code": line.strip()[:120]})
        if PROCESS_EXEC.search(line):
            findings["process_execution"].append({"line": i, "code": line.strip()[:120]})
        if NETWORK_CODE.search(line):
            findings["network_code"].append({"line": i, "code": line.strip()[:120]})
        if HARDCODED_PATH.search(line):
            findings["hardcoded_paths"].append({"line": i, "code": line.strip()[:120]})
        if SECRET_ASSIGN.search(line):
            # Redact the actual value
            redacted = re.sub(r"['\"][^'\"]{8,}['\"]", "'<REDACTED>'", line.strip()[:120])
            findings["potential_secrets"].append({"line": i, "code": redacted})
        if TODO_FIXME.search(line):
            findings["todo_fixme"].append({"line": i, "code": line.strip()[:120]})

    # Only include if there are findings
    total = sum(len(v) for v in findings.values())
    if total == 0:
        return None
    return {"file": str(path.relative_to(ROOT)), **findings, "total_findings": total}

def main():
    print("MILK FIRST-PARTY CODE AUDIT", flush=True)
    files_scanned = 0
    all_findings = []
    summary = {
        "broad_exceptions": 0, "process_execution": 0, "network_code": 0,
        "hardcoded_paths": 0, "potential_secrets": 0, "todo_fixme": 0,
    }

    # Scan Python files
    for pattern in ["milk_*.py", "src/milk_ai/*.py", "scripts/*.py",
                    "integrations/atlas-kernel/src/**/*.py", "*.py"]:
        for p in ROOT.glob(pattern):
            if not should_scan(p) or not p.is_file():
                continue
            files_scanned += 1
            result = scan_file(p)
            if result:
                all_findings.append(result)
                for k in summary:
                    summary[k] += len(result.get(k, []))

    # Scan JS files in atlas_infra
    for p in (ROOT / "atlas_infra").rglob("*.js"):
        if not should_scan(p):
            continue
        files_scanned += 1
        result = scan_file(p)
        if result:
            all_findings.append(result)
            for k in summary:
                summary[k] += len(result.get(k, []))

    # Sort by total findings (most issues first)
    all_findings.sort(key=lambda f: f["total_findings"], reverse=True)

    report = {
        "schema": "ia_milk.code_audit.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_scanned": files_scanned,
        "files_with_findings": len(all_findings),
        "summary": summary,
        "findings": all_findings[:50],  # Top 50 files
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Files scanned: {files_scanned}")
    print(f"  Files with findings: {len(all_findings)}")
    print(f"  Summary: {json.dumps(summary)}")
    print(f"  Saved: {OUT}")

if __name__ == "__main__":
    main()
