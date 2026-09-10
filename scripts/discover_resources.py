#!/usr/bin/env python3
"""MILK Resource Discovery — bulk deterministic scan.
Produces state/MILK_RESOURCE_REGISTRY.json with compact results.
No secret values are ever recorded — only credential NAMES and presence flags.
"""
from __future__ import annotations
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\Utilizador\MILK_AI_STATE_CANONICO")
OUT = ROOT / "state" / "MILK_RESOURCE_REGISTRY.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return f"ERROR: {e}", -1

# ---- WINDOWS: drives ----
def discover_drives():
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        p = Path(f"{letter}:\\")
        try:
            if p.is_dir():
                total = shutil.disk_usage(p).total
                drives.append({"drive": f"{letter}:", "path": str(p), "total_gb": round(total / 1e9, 1)})
        except: pass
    return drives

# ---- WINDOWS: ports ----
def discover_ports():
    out, _ = run(["netstat", "-an"])
    ports = []
    for line in out.split("\n"):
        m = re.match(r"\s+TCP\s+[\d\.]+:(\d+)\s+.*LISTENING", line)
        if m:
            p = int(m.group(1))
            if p > 1024:
                ports.append(p)
    # Dedupe and sort
    ports = sorted(set(ports))
    # Only return interesting ones
    interesting = [p for p in ports if p in (3000, 5432, 6333, 8009, 8765, 8766, 11434, 19530, 19531, 7474, 9200)]
    return {"listening_ports_count": len(ports), "interesting_ports": interesting, "all_listening": ports[:50]}

# ---- WINDOWS: processes ----
def discover_processes():
    out, _ = run(["tasklist"], timeout=20)
    interesting = []
    keywords = ["python", "llama", "ollama", "node", "docker", "postgres", "redis",
                "chroma", "meili", "nginx", "git", "code", "wsl"]
    for line in out.split("\n"):
        ll = line.lower()
        for kw in keywords:
            if kw in ll and "tasklist" not in ll:
                parts = line.split()
                if len(parts) >= 2:
                    interesting.append({"name": parts[0], "pid": parts[1], "match": kw})
                break
    # Dedupe by pid
    seen = set()
    result = []
    for p in interesting:
        if p["pid"] not in seen:
            seen.add(p["pid"])
            result.append(p)
    return result

# ---- WINDOWS: environment credential NAMES only ----
def discover_env_creds():
    cred_names = []
    sensitive_patterns = ["TOKEN", "API_KEY", "SECRET", "PASSWORD", "PASS", "CREDENTIAL",
                          "PRIVATE_KEY", "ACCESS_KEY", "AUTH", "ZENODO", "ORCID", "CODEBERG",
                          "GITHUB", "NEXTCLOUD", "BOX", "BASE44", "HF_TOKEN", "OPENAI",
                          "COGNITIVE", "AZURE", "AWS", "GCP", "GOOGLE"]
    for key in sorted(os.environ):
        ku = key.upper()
        for pat in sensitive_patterns:
            if pat in ku:
                val = os.environ[key]
                cred_names.append({
                    "name": key,
                    "present": bool(val.strip()),
                    "length": len(val) if val else 0,
                    "value_redacted": True
                })
                break
    return cred_names

# ---- CLOUD SYNC ----
def discover_cloud_sync():
    sources = {}
    home = Path.home()

    # Nextcloud
    nc = home / "Nextcloud"
    if nc.is_dir():
        items = [d.name for d in nc.iterdir() if d.is_dir() and not d.name.startswith(".")]
        sources["nextcloud"] = {"path": str(nc), "online": True, "items": len(items),
                                "top_folders": items[:15]}

    # Google Drive
    for gd_path in [home / "Google Drive", home / "GoogleDrive", Path("C:/Users/Utilizador/Google Drive"),
                    home / "My Drive"]:
        if gd_path.is_dir():
            sources["google_drive"] = {"path": str(gd_path), "online": True}
            break

    # OneDrive
    for od_env in ["OneDrive", "OneDriveCommercial", "OneDriveConsumer"]:
        od = os.environ.get(od_env)
        if od and Path(od).is_dir():
            sources["onedrive"] = {"path": od, "online": True, "env_var": od_env}
            break
    if "onedrive" not in sources:
        for od_path in [home / "OneDrive", home / "OneDrive - Associacao MILK"]:
            if od_path.is_dir():
                sources["onedrive"] = {"path": str(od_path), "online": True}
                break

    # Box
    for box_path in [home / "Box", home / "Box Sync", home / "Box Drive"]:
        if box_path.is_dir():
            sources["box"] = {"path": str(box_path), "online": True}
            break

    return sources

# ---- DOCKER ----
def discover_docker():
    result = {"available": False, "containers": [], "volumes": [], "networks": [], "compose": []}
    out, code = run(["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"], timeout=15)
    if code == 0 and out:
        result["available"] = True
        for line in out.split("\n"):
            if line.strip():
                parts = line.split("|")
                result["containers"].append({
                    "name": parts[0] if len(parts) > 0 else "",
                    "image": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                    "ports": parts[3] if len(parts) > 3 else ""
                })

    out, _ = run(["docker", "volume", "ls", "--format", "{{.Name}}|{{.Driver}}"], timeout=15)
    if out:
        for line in out.split("\n"):
            if line.strip():
                parts = line.split("|")
                result["volumes"].append({"name": parts[0], "driver": parts[1] if len(parts) > 1 else ""})

    out, _ = run(["docker", "network", "ls", "--format", "{{.Name}}|{{.Driver}}"], timeout=15)
    if out:
        for line in out.split("\n"):
            if line.strip():
                parts = line.split("|")
                result["networks"].append({"name": parts[0], "driver": parts[1] if len(parts) > 1 else ""})

    out, _ = run(["docker", "compose", "ls", "--format", "{{.Name}}|{{.Status}}"], timeout=15)
    if out:
        for line in out.split("\n"):
            if line.strip():
                parts = line.split("|")
                result["compose"].append({"name": parts[0], "status": parts[1] if len(parts) > 1 else ""})

    return result

# ---- WSL ----
def discover_wsl():
    result = {"available": False, "distributions": []}
    out, code = run(["wsl", "-l", "-v"], timeout=15)
    if code == 0 and out:
        result["available"] = True
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        for line in lines[1:]:  # skip header
            parts = line.split()
            if len(parts) >= 3:
                result["distributions"].append({
                    "name": parts[0].strip("*"),
                    "state": parts[1],
                    "version": parts[2]
                })
    return result

# ---- LOCAL AI ----
def discover_local_ai():
    ai = {}
    # GPT-OSS
    ai["gpt_oss"] = {"endpoint": "127.0.0.1:8009", "online": True,
                    "model": "gpt-oss-20b-MXFP4", "role": "reasoning_worker"}

    # Fabric
    ai["milk_fabric"] = {"endpoint": "127.0.0.1:8766", "online": True,
                         "role": "orchestrator", "pid": 5744}

    # Ollama
    out, code = run(["ollama", "list"], timeout=10)
    if code == 0 and out.strip():
        ai["ollama"] = {"endpoint": "127.0.0.1:11434", "online": True,
                        "models": [l.split()[0] for l in out.strip().split("\n")[1:] if l.strip()]}
    else:
        # Check if ollama is running
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect(("127.0.0.1", 11434))
            ai["ollama"] = {"endpoint": "127.0.0.1:11434", "online": True, "models": []}
        except:
            ai["ollama"] = {"online": False}
        s.close()

    # BGE-M3 / BGE-reranker (check HF cache)
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    bge_models = []
    if hf_cache.is_dir():
        for d in hf_cache.iterdir():
            if "bge" in d.name.lower():
                bge_models.append(d.name)
    ai["bge_models"] = {"cached": bge_models, "cache_path": str(hf_cache)}

    # GPU
    out, _ = run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader"], timeout=10)
    if out:
        parts = out.split(",")
        ai["gpu"] = {"name": parts[0].strip(), "vram_total_mb": parts[1].strip(),
                      "vram_used_mb": parts[2].strip()}

    return ai

# ---- MCP / Vibe discovery ----
def discover_mcp():
    mcp = {}
    vibe_dir = home = Path.home() / ".vibe"
    if vibe_dir.is_dir():
        mcp["vibe_dir"] = str(vibe_dir)
        mcp["vibe_files"] = [f.name for f in vibe_dir.iterdir() if f.is_file()]
    else:
        mcp["vibe_dir"] = "not found"

    # Check .vibe in project
    project_vibe = ROOT / ".vibe"
    if project_vibe.is_dir():
        mcp["project_vibe"] = str(project_vibe)
        mcp["project_vibe_files"] = [f.name for f in project_vibe.iterdir() if f.is_file()]

    # Check for MCP config files
    mcp_configs = []
    for p in [Path.home() / ".claude" / "settings.json",
              Path.home() / ".claude" / "settings.local.json",
              ROOT / ".claude" / "settings.json",
              ROOT / ".claude" / "settings.local.json"]:
        if p.exists():
            mcp_configs.append(str(p))
    mcp["config_files_found"] = mcp_configs

    return mcp

# ---- Windows Credential Manager targets ----
def discover_credman():
    out, code = run(["cmdkey", "/list"], timeout=15)
    targets = []
    if code == 0 and out:
        for line in out.split("\n"):
            m = re.search(r"Target:\s*(.+)", line)
            if m:
                targets.append(m.group(1).strip())
    return {"available": code == 0, "targets": targets, "count": len(targets)}


def main():
    print("MILK RESOURCE DISCOVERY", flush=True)
    registry = {
        "schema": "ia_milk.resource_registry.v1",
        "generated_at": now(),
        "canonical_root": str(ROOT),
    }

    print("  drives...", end="", flush=True)
    registry["drives"] = discover_drives()
    print(f" {len(registry['drives'])}")

    print("  ports...", end="", flush=True)
    registry["ports"] = discover_ports()
    print(f" {len(registry['ports']['all_listening'])} listening")

    print("  processes...", end="", flush=True)
    registry["processes"] = discover_processes()
    print(f" {len(registry['processes'])} interesting")

    print("  env_creds...", end="", flush=True)
    registry["env_credentials"] = discover_env_creds()
    print(f" {len(registry['env_credentials'])} names")

    print("  credman...", end="", flush=True)
    registry["credman"] = discover_credman()
    print(f" {registry['credman']['count']} targets")

    print("  cloud_sync...", end="", flush=True)
    registry["cloud_sync"] = discover_cloud_sync()
    print(f" {list(registry['cloud_sync'].keys())}")

    print("  docker...", end="", flush=True)
    registry["docker"] = discover_docker()
    print(f" available={registry['docker']['available']}, containers={len(registry['docker']['containers'])}")

    print("  wsl...", end="", flush=True)
    registry["wsl"] = discover_wsl()
    print(f" available={registry['wsl']['available']}, distros={len(registry['wsl']['distributions'])}")

    print("  local_ai...", end="", flush=True)
    registry["local_ai"] = discover_local_ai()
    print(f" {list(registry['local_ai'].keys())}")

    print("  mcp...", end="", flush=True)
    registry["mcp"] = discover_mcp()
    print(f" {list(registry['mcp'].keys())}")

    # Summary
    registry["summary"] = {
        "total_drives": len(registry["drives"]),
        "cloud_sync_sources": list(registry["cloud_sync"].keys()),
        "docker_available": registry["docker"]["available"],
        "docker_containers": len(registry["docker"]["containers"]),
        "wsl_available": registry["wsl"]["available"],
        "local_ai_services": [k for k, v in registry["local_ai"].items() if isinstance(v, dict) and v.get("online")],
        "env_cred_names": len(registry["env_credentials"]),
        "credman_targets": registry["credman"]["count"],
        "interesting_ports": registry["ports"]["interesting_ports"],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSAVED: {OUT}")
    print(f"SUMMARY: {json.dumps(registry['summary'], ensure_ascii=False)}")

if __name__ == "__main__":
    main()
