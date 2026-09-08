from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, model_validator


class Classification(StrEnum):
    PUBLIC = "publico"
    LICENSABLE = "licenciavel"
    CONFIDENTIAL = "confidencial"
    PERSONAL = "dados_pessoais"


class ApprovalState(StrEnum):
    PENDING = "PENDENTE"
    APPROVED = "APROVADO"
    REJECTED = "REJEITADO"


class Identifier(BaseModel):
    scheme: str
    value: str


class Provenance(BaseModel):
    source_id: str
    source_system: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    original_preserved: bool = True


class AtlasRecord(BaseModel):
    record_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    record_type: str
    language: str = "pt-PT"
    classification: Classification
    approval: ApprovalState = ApprovalState.PENDING
    consent_public: bool = False
    licence: str | None = None
    creators: list[str] = Field(default_factory=list)
    identifiers: list[Identifier] = Field(default_factory=list)
    provenance: Provenance
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def public_gate(self) -> "AtlasRecord":
        if self.classification == Classification.PUBLIC:
            if self.approval != ApprovalState.APPROVED or not self.consent_public:
                raise ValueError("registo público exige aprovação humana e consent_public=true")
            if not self.licence:
                raise ValueError("registo público exige licença explícita")
        return self

    def canonical_hash(self) -> str:
        data = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        # A hora da captura pertence ao log de proveniência, não à identidade
        # semântica do registo. Excluí-la torna a assinatura determinística.
        data.get("provenance", {}).pop("captured_at", None)
        material = __import__("json").dumps(data, sort_keys=True, ensure_ascii=False,
                                           separators=(",", ":"))
        return sha256(material.encode("utf-8")).hexdigest()


class ExecutionReceipt(BaseModel):
    connector: str
    operation: str
    executed: bool
    dry_run: bool
    status: str
    request_hash: str
    external_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class MigrationStatus(BaseModel):
    discovered_files: int
    discovered_folders: int
    transferred: int = 0
    verified: int = 0
    existing: int = 0
    failed: int = 0
    discovered_bytes: int
    transferred_bytes: int = 0
