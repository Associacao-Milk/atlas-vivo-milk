#!/usr/bin/env python3
"""MILK IA — SOVEREIGN CORE GATE test: prova de independencia offline.

Executa uma query real ao core MILK com rede e providers externos OFF.
Valida: soberania de import, fallback local, query offline, compliance,
ontologia, export NGSI-LD/CNMD. Nao treina, nao activa daemon.
"""
from __future__ import annotations
import sys, os, json, socket
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO\src")
sys.path.insert(0, str(SRC))

# Block network BEFORE importing core, to prove no import-time network.
_orig_connect = socket.socket.connect
def _blocked(self, addr):
    raise RuntimeError(f"NETWORK BLOCKED: {addr}")
socket.socket.connect = _blocked  # type: ignore[method-assign]

# Clear any provider credentials
for var in ("MISTRAL_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
    os.environ.pop(var, None)

from milk_ai.engine import MilkAI
from milk_ai.sovereign_gate import run_gate, report_to_dict
from milk_ai.provider_adapter import LocalAdapter, select_provider

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")

# Build the sovereign core with NO provider (forces LocalAdapter fallback)
core = MilkAI(ROOT, provider=None)

# Real offline query against the 250k-chunk corpus
QUESTION = "folclore romaria tradicao popular freguesia Moura"
answer = core.query(QUESTION, limit=5)
answer_dict = answer.to_dict()

print(f"=== OFFLINE QUERY (network blocked, no provider) ===")
print(f"  question: {QUESTION}")
print(f"  provider: {core.provider.name} (is_local={core.provider.is_local})")
print(f"  answer_text: {answer_dict['text'][:120]}")
print(f"  citations: {len(answer_dict['citations'])}")
print(f"  confidence: {answer_dict['confidence']}")
print(f"  warnings: {answer_dict['warnings']}")

# Now run the full gate with the offline query as proof
def query_fn():
    return answer_dict

# Capture loaded modules for sovereignty scan
loaded = set(sys.modules.keys())
report = run_gate(core_query_fn=query_fn, loaded_modules=loaded)
rd = report_to_dict(report)
rd["offline_query_answer"] = {
    "text": answer_dict["text"],
    "citations_count": len(answer_dict["citations"]),
    "facts_count": len(answer_dict["facts"]),
    "model": answer_dict.get("model"),
}

print(f"\n=== SOVEREIGN CORE GATE ===")
print(f"  import_sovereignty_ok: {rd['import_sovereignty_ok']}")
print(f"  forbidden_modules: {rd['forbidden_modules']}")
print(f"  fallback_provider_ok: {rd['fallback_provider_ok']} ({rd['fallback_provider_name']})")
print(f"  offline_query_ok: {rd['offline_query_ok']} (citations={rd['offline_answer_citations']})")
print(f"  compliance_profiles_count: {rd['compliance_profiles_count']}")
print(f"  ontology_version: {rd['ontology_version']}")
print(f"  ngsi_ld_export_ok: {rd['ngsi_ld_export_ok']}")
print(f"  shacl_shapes_ok: {rd['shacl_shapes_ok']}")
print(f"  overall_ok: {rd['overall_ok']}")

# Restore network for file writing
socket.socket.connect = _orig_connect  # type: ignore[method-assign]

out = ROOT / "state" / "sovereign_core_gate_report.json"
out.write_text(json.dumps(rd, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nreport -> {out}")

# Save ontology artifacts
from milk_ai.ontology import jsonld_context, turtle, shacl_shapes
onto_dir = ROOT / "state" / "ontology"
onto_dir.mkdir(exist_ok=True)
(onto_dir / "milk_context.jsonld").write_text(json.dumps(jsonld_context(), ensure_ascii=False, indent=2), encoding="utf-8")
(onto_dir / "milk_ontology.ttl").write_text(turtle(), encoding="utf-8")
(onto_dir / "milk_shacl_shapes.json").write_text(json.dumps(shacl_shapes(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"ontology artifacts -> {onto_dir}")

sys.exit(0 if rd["overall_ok"] else 1)
