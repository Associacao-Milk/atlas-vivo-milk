from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .atlas_graph import build_graph
from .engine import MilkAI
from .ingest import CorpusStore
from .agent_catalog import route_task
from .governance_models import TaskEnvelope
from .mistral import MistralClient, MistralError
from .models import Visibility
from .provenance import build_manifest, canonical_json
from .research import collect_references
from .vault import SecretVault, VaultError, default_vault_dir
from .webapp import serve as atlas_webapp_serve


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="milk-ai", description="MILK AI — núcleo soberano")
    result.add_argument("--state-dir", type=Path, default=Path("state"))
    sub = result.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="estado factual do corpus")
    status.set_defaults(action="status")

    atlas = sub.add_parser("atlas", help="artefactos estruturais do Atlas")
    atlas_sub = atlas.add_subparsers(dest="atlas_command", required=True)
    graph = atlas_sub.add_parser("graph", help="construir grafo factual local")
    graph.add_argument("--output", type=Path, default=Path("state") / "atlas_graph.json")
    graph.set_defaults(action="atlas_graph")

    research = sub.add_parser("research", help="pesquisa bibliográfica anotada em fontes públicas")
    research.add_argument("query")
    research.add_argument("--limit", type=int, default=10)
    research.add_argument("--output", type=Path, default=Path("state") / "research_report.json")
    research.set_defaults(action="research")

    atlas_serve = atlas_sub.add_parser("serve", help="webapp só de leitura do Atlas")
    atlas_serve.add_argument("--host", default="127.0.0.1")
    atlas_serve.add_argument("--port", type=int, default=8765)
    atlas_serve.set_defaults(action="atlas_serve")

    ingest = sub.add_parser("ingest", help="indexação preservativa")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--visibility", choices=[item.value for item in Visibility], default=Visibility.RESTRICTED.value)
    ingest.add_argument("--secret-mode", choices=["quarantine", "redact"], default="quarantine")
    ingest.set_defaults(action="ingest")

    query = sub.add_parser("query", help="consulta fundamentada")
    query.add_argument("question")
    query.add_argument("--limit", type=int, default=5)
    query.add_argument("--mistral", action="store_true")
    query.add_argument("--ollama", action="store_true", help="síntese local com Ollama")
    query.add_argument("--ollama-model", default="mistral:latest")
    query.add_argument("--semantic", action="store_true")
    query.add_argument("--include-restricted-remote", action="store_true")
    query.set_defaults(action="query")

    governance = sub.add_parser("governance", help="validação humana auditada de uma fonte")
    governance.add_argument("source_id")
    governance.add_argument("--actor", required=True)
    governance.add_argument("--reason", required=True)
    governance.add_argument("--visibility", choices=[item.value for item in Visibility])
    governance.add_argument("--rights-status")
    governance.add_argument("--consent-status")
    governance.add_argument("--rgpd-status")
    governance.add_argument("--human-validated", action="store_true")
    governance.add_argument("--confirm-human-approval", action="store_true")
    governance.set_defaults(action="governance")

    manifest = sub.add_parser("manifest", help="manifesto SHA-256 do pacote")
    manifest.add_argument("path", type=Path, nargs="?", default=Path("."))
    manifest.set_defaults(action="manifest")

    route = sub.add_parser("route", help="validar e rotear um contrato de tarefa JSON")
    route.add_argument("task", type=Path)
    route.set_defaults(action="route")

    vault = sub.add_parser("vault", help="cofre DPAPI de credenciais")
    vault.add_argument("--vault-dir", type=Path, default=default_vault_dir())
    vault_commands = vault.add_subparsers(dest="vault_command", required=True)
    vault_list = vault_commands.add_parser("list", help="listar apenas metadados seguros")
    vault_list.add_argument("--service")
    vault_list.add_argument("--status", choices=["candidate", "active", "expired", "revoked"])
    vault_list.set_defaults(action="vault_list")
    vault_put = vault_commands.add_parser("put", help="guardar valor recebido por variável de ambiente")
    vault_put.add_argument("--service", required=True)
    vault_put.add_argument("--account", required=True)
    vault_put.add_argument("--from-env", required=True)
    vault_put.add_argument("--scope", action="append", default=[])
    vault_put.set_defaults(action="vault_put")
    vault_activate = vault_commands.add_parser("activate", help="activar credencial validada")
    vault_activate.add_argument("credential_id")
    vault_activate.add_argument("--actor", required=True)
    vault_activate.add_argument("--reason", required=True)
    vault_activate.add_argument("--confirm-human-approval", action="store_true")
    vault_activate.set_defaults(action="vault_activate")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    state_dir = args.state_dir.resolve()
    if args.action == "manifest":
        root = args.path.resolve()
        _json(build_manifest((p for p in root.rglob("*") if p.is_file()), root))
        return 0
    if args.action == "route":
        task = TaskEnvelope.model_validate_json(args.task.read_text(encoding="utf-8"))
        agent, receipt = route_task(task)
        _json({
            "agent": {
                "role": agent.role.value,
                "capabilities": list(agent.capabilities),
                "external_write_allowed": agent.external_write_allowed,
            },
            "receipt": receipt.model_dump(mode="json"),
        })
        return 0
    if args.action.startswith("vault_"):
        try:
            vault = SecretVault(args.vault_dir)
            if args.action == "vault_list":
                _json(vault.list(service=args.service, status=args.status))
                return 0
            if args.action == "vault_put":
                secret = os.environ.get(args.from_env, "")
                if not secret:
                    raise VaultError(f"variável {args.from_env} ausente ou vazia")
                result = vault.put(
                    service=args.service,
                    account=args.account,
                    secret=secret,
                    scopes=args.scope,
                )
                os.environ.pop(args.from_env, None)
                _json(result)
                return 0
            if args.action == "vault_activate":
                _json(vault.activate(
                    args.credential_id,
                    actor=args.actor,
                    reason=args.reason,
                    human_approval=args.confirm_human_approval,
                ))
                return 0
        except VaultError as exc:
            _json({"status": "bloqueado", "reason": str(exc)})
            return 2

    if args.action == "atlas_graph":
        graph = build_graph(CorpusStore(state_dir / "corpus").documents())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _json(graph["summary"] | {"output": str(args.output.resolve())})
        return 0

    if args.action == "research":
        if args.limit < 1 or args.limit > 100:
            _json({"status": "bloqueado", "reason": "limit deve estar entre 1 e 100"})
            return 2
        report = collect_references(args.query, args.limit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _json(report["summary"] | {"output": str(args.output.resolve()), "errors": len(report["errors"])})
        return 0 if not report["errors"] else 2
    if args.action == "atlas_serve":
        return atlas_webapp_serve(state_dir, host=args.host, port=args.port)

    client = None
    if getattr(args, "ollama", False):
        client = MistralClient(
            api_key="ollama",
            base_url="http://127.0.0.1:11434/v1",
            chat_model=args.ollama_model,
        )
    elif getattr(args, "mistral", False):
        try:
            if os.environ.get("MISTRAL_API_KEY", "").strip():
                client = MistralClient.from_environment()
            else:
                _credential_id, key = SecretVault(default_vault_dir()).find_single_active("mistral")
                client = MistralClient(api_key=key)
        except (MistralError, VaultError) as exc:
            _json({"status": "bloqueado", "reason": str(exc)})
            return 2
    allowed = {"publica", "licenciavel"}
    if getattr(args, "include_restricted_remote", False):
        allowed.add("restrita")
    engine = MilkAI(
        state_dir,
        mistral=client,
        semantic=getattr(args, "semantic", False),
        remote_allowed_layers=allowed,
    )
    if args.action == "status":
        documents = engine.store.documents()
        ollama_available = shutil.which("ollama") is not None
        _json({
            "documents": len(documents),
            "chunks": sum(len(item.get("chunks", [])) for item in documents),
            "active_backend": "local_ollama",
            "ollama_available": ollama_available,
            "ollama_default_model": "mistral:latest",
            "mistral_configured": bool(os.environ.get("MISTRAL_API_KEY")) or _vault_has_active_mistral(),
            "state_dir": str(state_dir),
        })
        return 0
    if args.action == "ingest":
        _json(engine.ingest(args.path, Visibility(args.visibility), secret_mode=args.secret_mode))
        return 0
    if args.action == "governance":
        changes = {
            key: value for key, value in {
                "visibility": args.visibility,
                "rights_status": args.rights_status,
                "consent_status": args.consent_status,
                "rgpd_status": args.rgpd_status,
                "human_validated": True if args.human_validated else None,
                "validated_by": args.actor if args.human_validated else None,
            }.items() if value is not None
        }
        try:
            _json(engine.update_governance(
                args.source_id,
                changes,
                actor=args.actor,
                reason=args.reason,
                human_approval=args.confirm_human_approval,
            ))
            return 0
        except (PermissionError, ValueError, KeyError) as exc:
            _json({"status": "bloqueado", "reason": str(exc)})
            return 2
    if args.action == "query":
        try:
            _json(engine.query(args.question, limit=args.limit).to_dict())
            return 0
        except MistralError as exc:
            _json({"status": "bloqueado", "reason": str(exc)})
            return 2
    return 1


def _vault_has_active_mistral() -> bool:
    try:
        return len(SecretVault(default_vault_dir()).list(service="mistral", status="active")) == 1
    except VaultError:
        return False
