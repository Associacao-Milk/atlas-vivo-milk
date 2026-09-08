from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import Any, ClassVar
from urllib.parse import urlparse

from .models import ActionLevel


SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
TASK_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
CREDENTIAL_ENV_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")


class ValidationError(ValueError):
    """Erro de contrato estrito sem dependência binária externa."""


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return value


class StrictModel:
    secret_fields: ClassVar[set[str]] = set()

    @classmethod
    def model_validate_json(cls, raw: str) -> Any:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"JSON inválido: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValidationError("o contrato deve ser um objecto JSON")
        allowed = {item.name for item in fields(cls)}
        unknown = set(value) - allowed
        if unknown:
            raise ValidationError(f"campos não permitidos: {sorted(unknown)}")
        try:
            return cls(**value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        if mode not in {"python", "json"}:
            raise ValueError("mode deve ser python ou json")
        result = {
            item.name: getattr(self, item.name)
            for item in fields(self)
            if item.name not in self.secret_fields
        }
        return _json_value(result) if mode == "json" else result


class StandardStatus(StrEnum):
    TO_ASSESS = "a_avaliar"
    NOT_APPLICABLE = "nao_aplicavel"
    PARTIAL = "parcial"
    VERIFIED = "verificado"


class AgentRole(StrEnum):
    ORCHESTRATOR = "orquestrador"
    HERMENEUT = "hermeneuta_c1"
    PROFILE = "gestor_perfis"
    INTEROPERABILITY = "gestor_interoperabilidade"
    FUNDING = "gestor_financiabilidade"


class ApprovalDecision(StrEnum):
    APPROVE = "aprovar"
    REJECT = "rejeitar"
    REQUEST_CHANGES = "pedir_alteracoes"


@dataclass(slots=True)
class PersonReference(StrictModel):
    display_name: str
    orcid: str | None = None
    roles: list[str] = field(default_factory=list)
    affiliation: str | None = None

    def __post_init__(self) -> None:
        self.display_name = self.display_name.strip()
        if not 1 <= len(self.display_name) <= 240:
            raise ValidationError("display_name inválido")
        if self.orcid is None:
            return
        if not ORCID_PATTERN.fullmatch(self.orcid):
            raise ValidationError("formato ORCID inválido")
        digits = self.orcid.replace("-", "")
        total = 0
        for char in digits[:15]:
            total = (total + int(char)) * 2
        check = (12 - total % 11) % 11
        expected = "X" if check == 10 else str(check)
        if digits[-1] != expected:
            raise ValidationError("checksum ORCID inválido")


@dataclass(slots=True)
class StandardClaim(StrictModel):
    standard: str
    version: str | None = None
    status: StandardStatus = StandardStatus.TO_ASSESS
    evidence_sha256: list[str] = field(default_factory=list)
    verified_by: str | None = None
    verified_at: datetime | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        self.standard = self.standard.strip()
        if len(self.standard) < 2:
            raise ValidationError("standard inválido")
        self.status = StandardStatus(self.status)
        if any(not SHA256_PATTERN.fullmatch(value) for value in self.evidence_sha256):
            raise ValidationError("evidência deve usar SHA-256")
        if self.status == StandardStatus.VERIFIED:
            if not self.evidence_sha256 or not self.verified_by or not self.verified_at:
                raise ValidationError("estado verificado exige evidência, responsável e data")


@dataclass(slots=True)
class ExternalService(StrictModel):
    secret_fields: ClassVar[set[str]] = {"credential"}
    name: str
    base_url: str
    credential_environment: str
    credential: str | None = field(default=None, repr=False)
    allows_write: bool = False

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("base_url inválido")
        if not CREDENTIAL_ENV_PATTERN.fullmatch(self.credential_environment):
            raise ValidationError("nome da variável de credencial inválido")


@dataclass(slots=True)
class ApprovalRecord(StrictModel):
    artifact_sha256: str
    validator_id: str
    validator_role: str
    decision: ApprovalDecision
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""

    def __post_init__(self) -> None:
        if not SHA256_PATTERN.fullmatch(self.artifact_sha256):
            raise ValidationError("artifact_sha256 inválido")
        self.validator_id = self.validator_id.strip()
        self.validator_role = self.validator_role.strip()
        self.reason = self.reason.strip()
        if not 3 <= len(self.validator_id) <= 160:
            raise ValidationError("validator_id inválido")
        if not 2 <= len(self.validator_role) <= 120:
            raise ValidationError("validator_role inválido")
        if not 3 <= len(self.reason) <= 2000:
            raise ValidationError("reason inválido")
        self.decision = ApprovalDecision(self.decision)


@dataclass(slots=True)
class ApprovalPolicy(StrictModel):
    minimum_distinct_approvals: int = 2
    required_roles: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not 1 <= self.minimum_distinct_approvals <= 10:
            raise ValidationError("minimum_distinct_approvals deve estar entre 1 e 10")

    def is_satisfied(self, artifact_sha256: str, records: list[ApprovalRecord]) -> bool:
        approvals = [
            record for record in records
            if record.artifact_sha256 == artifact_sha256 and record.decision == ApprovalDecision.APPROVE
        ]
        validators = {record.validator_id for record in approvals}
        roles = {record.validator_role for record in approvals}
        return len(validators) >= self.minimum_distinct_approvals and self.required_roles.issubset(roles)


@dataclass(slots=True)
class TaskEnvelope(StrictModel):
    task_id: str
    role: AgentRole
    action: ActionLevel
    source_ids: list[str] = field(default_factory=list)
    target: str | None = None
    requires_external_write: bool = False
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not TASK_PATTERN.fullmatch(self.task_id):
            raise ValidationError("task_id inválido")
        self.role = AgentRole(self.role)
        self.action = ActionLevel(self.action)
        if not isinstance(self.source_ids, list) or any(not isinstance(value, str) for value in self.source_ids):
            raise ValidationError("source_ids deve ser uma lista de texto")
        if not isinstance(self.payload, dict):
            raise ValidationError("payload deve ser um objecto")
        if self.requires_external_write and self.action == ActionLevel.READ:
            raise ValidationError("uma escrita externa não pode ser declarada como leitura")


@dataclass(slots=True)
class ExecutionReceipt(StrictModel):
    task_id: str
    agent_role: AgentRole
    state: str
    executed: bool
    evidence_sha256: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.agent_role = AgentRole(self.agent_role)
        if any(not SHA256_PATTERN.fullmatch(value) for value in self.evidence_sha256):
            raise ValidationError("evidence_sha256 inválido")
