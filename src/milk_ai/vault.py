from __future__ import annotations

import base64
import ctypes
import json
import os
import re
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, TypeVar

from .provenance import atomic_json, canonical_json, sha256_bytes, utc_now


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{1,80}$")
T = TypeVar("T")


class VaultError(RuntimeError):
    pass


class Protector(Protocol):
    def protect(self, value: bytes) -> bytes: ...
    def unprotect(self, value: bytes) -> bytes: ...


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(value: bytes) -> tuple[_DataBlob, object]:
    buffer = (ctypes.c_ubyte * len(value)).from_buffer_copy(value)
    return _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


class DPAPIProtector:
    """Cifra para o utilizador Windows actual sem guardar uma chave mestra."""

    entropy = b"MILK_AI_VAULT_V1"

    def __init__(self) -> None:
        if os.name != "nt":
            raise VaultError("o cofre operacional DPAPI só pode ser aberto no Windows")
        self.crypt32 = ctypes.windll.crypt32
        self.kernel32 = ctypes.windll.kernel32

    def protect(self, value: bytes) -> bytes:
        return self._call("CryptProtectData", value)

    def unprotect(self, value: bytes) -> bytes:
        return self._call("CryptUnprotectData", value)

    def _call(self, operation: str, value: bytes) -> bytes:
        source, source_buffer = _blob(value)
        entropy, entropy_buffer = _blob(self.entropy)
        output = _DataBlob()
        function = getattr(self.crypt32, operation)
        args = (
            ctypes.byref(source),
            "MILK AI credential" if operation == "CryptProtectData" else None,
            ctypes.byref(entropy),
            None,
            None,
            0x1,
            ctypes.byref(output),
        )
        if not function(*args):
            raise VaultError(f"DPAPI falhou: erro Windows {ctypes.get_last_error()}")
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            self.kernel32.LocalFree(output.pbData)
            del source_buffer, entropy_buffer


def default_vault_dir() -> Path:
    configured = os.environ.get("MILK_AI_VAULT_DIR")
    if configured:
        return Path(configured).expanduser()
    local = os.environ.get("LOCALAPPDATA")
    return (Path(local) if local else Path.home() / "AppData" / "Local") / "MILK_AI" / "vault"


@dataclass(slots=True)
class CredentialBroker:
    vault: "SecretVault"

    def execute(
        self,
        credential_id: str,
        *,
        action: str,
        adapter: Callable[[str], T],
        human_approval: bool = False,
    ) -> T:
        if action not in {"read", "write"}:
            raise VaultError("acção deve ser read ou write")
        if action == "write" and not human_approval:
            raise VaultError("escrita externa exige aprovação humana")
        secret = self.vault.get(credential_id)
        self.vault.audit("credential_use_started", credential_id, {"action": action})
        try:
            result = adapter(secret)
            self.vault.audit("credential_use_completed", credential_id, {"action": action})
            return result
        except Exception as exc:
            self.vault.audit("credential_use_failed", credential_id, {"action": action, "error_type": type(exc).__name__})
            raise
        finally:
            secret = ""


class SecretVault:
    def __init__(self, root: Path | None = None, protector: Protector | None = None):
        self.root = (root or default_vault_dir()).expanduser().resolve()
        self.credentials_dir = self.root / "credentials"
        self.unresolved_dir = self.root / "unresolved"
        self.audit_path = self.root / "audit.jsonl"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.unresolved_dir.mkdir(parents=True, exist_ok=True)
        self.protector = protector or DPAPIProtector()

    def put(
        self,
        *,
        service: str,
        account: str,
        secret: str,
        scopes: list[str] | None = None,
        status: str = "candidate",
        kind: str = "credential",
    ) -> dict:
        service = service.strip().casefold()
        if not IDENTIFIER.fullmatch(service):
            raise VaultError("identificador de serviço inválido")
        if not account.strip() or not secret:
            raise VaultError("conta e segredo são obrigatórios")
        if status not in {"candidate", "active", "expired", "revoked"}:
            raise VaultError("estado de credencial inválido")
        credential_id = f"cred_{uuid.uuid4().hex}"
        now = utc_now()
        secret_bytes = secret.encode("utf-8")
        protected_envelope = canonical_json({
            "value": secret,
            "sha256": sha256_bytes(secret_bytes),
        })
        record = {
            "credential_id": credential_id,
            "service": service,
            "account": account.strip()[:240],
            "kind": kind,
            "scopes": sorted(set(scopes or [])),
            "status": status,
            "created_at": now,
            "updated_at": now,
            "ciphertext_dpapi": base64.b64encode(self.protector.protect(protected_envelope)).decode("ascii"),
        }
        atomic_json(self.credentials_dir / f"{credential_id}.json", record)
        self.audit("credential_stored", credential_id, {"service": service, "status": status, "kind": kind})
        return self._public(record)

    def list(self, *, service: str | None = None, status: str | None = None) -> list[dict]:
        records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.credentials_dir.glob("cred_*.json"))]
        if service:
            records = [item for item in records if item["service"] == service.casefold()]
        if status:
            records = [item for item in records if item["status"] == status]
        return [self._public(item) for item in records]

    def get(self, credential_id: str, *, require_active: bool = True) -> str:
        record = self._load(credential_id)
        if require_active and record["status"] != "active":
            raise VaultError("credencial não está activa")
        encrypted = base64.b64decode(record["ciphertext_dpapi"], validate=True)
        try:
            envelope = json.loads(self.protector.unprotect(encrypted).decode("utf-8"))
            value = envelope["value"]
            if not isinstance(value, str) or envelope["sha256"] != sha256_bytes(value.encode("utf-8")):
                raise VaultError("integridade da credencial inválida")
            return value
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise VaultError("envelope cifrado inválido") from exc

    def activate(self, credential_id: str, *, actor: str, reason: str, human_approval: bool) -> dict:
        if not human_approval or not actor.strip() or not reason.strip():
            raise VaultError("activação exige aprovação humana, responsável e fundamento")
        record = self._load(credential_id)
        record["status"] = "active"
        record["updated_at"] = utc_now()
        atomic_json(self.credentials_dir / f"{credential_id}.json", record)
        self.audit("credential_activated", credential_id, {"actor": actor.strip(), "reason": reason.strip()})
        return self._public(record)

    def find_single_active(self, service: str) -> tuple[str, str]:
        records = self.list(service=service, status="active")
        if len(records) != 1:
            raise VaultError(f"serviço {service} exige exactamente uma credencial activa; encontradas: {len(records)}")
        credential_id = records[0]["credential_id"]
        return credential_id, self.get(credential_id)

    def audit(self, event: str, credential_id: str | None, details: dict | None = None) -> None:
        previous = "0" * 64
        if self.audit_path.exists():
            lines = self.audit_path.read_text(encoding="utf-8").splitlines()
            if lines:
                previous = json.loads(lines[-1])["record_sha256"]
        unsigned = {
            "timestamp": utc_now(),
            "event": event,
            "credential_id": credential_id,
            "details": details or {},
            "previous_sha256": previous,
        }
        record = {**unsigned, "record_sha256": sha256_bytes(canonical_json(unsigned))}
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _load(self, credential_id: str) -> dict:
        if not re.fullmatch(r"cred_[a-f0-9]{32}", credential_id):
            raise VaultError("credential_id inválido")
        path = self.credentials_dir / f"{credential_id}.json"
        if not path.is_file():
            raise VaultError("credencial não encontrada")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _public(record: dict) -> dict:
        return {key: value for key, value in record.items() if key != "ciphertext_dpapi"}
