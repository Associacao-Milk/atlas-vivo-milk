from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Visibility(StrEnum):
    PUBLIC = "publica"
    LICENSABLE = "licenciavel"
    RESTRICTED = "restrita"
    INVISIBLE = "invisivel"


class EpistemicState(StrEnum):
    PREPARED = "preparado"
    ANALYSED = "analisado"
    INFERRED = "inferido"
    INTERNAL_VALIDATED = "validado_internamente"
    EXTERNAL_VALIDATED = "validado_externamente"
    EXECUTED = "executado"
    PUBLISHED = "publicado"


class ActionLevel(StrEnum):
    READ = "leitura"
    PROPOSE = "proposta"
    MODIFY = "alteracao"
    PUBLISH = "publicacao"


@dataclass(slots=True)
class SourceMetadata:
    source_id: str
    original_name: str
    original_path: str
    sha256: str
    size_bytes: int
    ingested_at: str
    visibility: Visibility = Visibility.RESTRICTED
    epistemic_state: EpistemicState = EpistemicState.PREPARED
    author: str | None = None
    responsible_entity: str = "Associação MILK"
    territory: str | None = None
    district: str | None = None
    municipality: str | None = None
    parish: str | None = None
    document_type: str | None = None
    curatorial_device: str | None = None
    rights_status: str = "por_validar"
    consent_status: str = "por_validar"
    rgpd_status: str = "por_validar"
    human_validated: bool = False
    validated_by: str | None = None
    validation_date: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    source_id: str
    ordinal: int
    text: str
    heading: str | None
    sha256: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RetrievalHit:
    chunk_id: str
    source_id: str
    score: float
    lexical_score: float
    semantic_score: float | None
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Answer:
    text: str
    state: str
    confidence: str
    citations: list[str]
    facts: list[str]
    inferences: list[str]
    unknowns: list[str]
    warnings: list[str]
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

