from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .models import ActionLevel, SourceMetadata, Visibility


ABSOLUTE_CLAIMS = (
    r"\b100\s*%\s+(?:blindad[oa]|segur[oa]|garantid[oa])\b",
    r"\bjuridicamente blindad[oa]\b",
    r"\bfinanciável com certeza\b",
    r"\bpronto para submissão\b",
    r"\bsem risco(?: nenhum)?\b",
)

HIGH_RISK_PURPOSES = {
    "biometria",
    "perfil_psicologico",
    "scoring_humano",
    "vigilancia_comportamental",
    "geolocalizacao_individual",
    "previsao_comportamental",
    "medicao_emocional_individual",
}


@dataclass(slots=True)
class GateDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)


def truth_claim_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for pattern in ABSOLUTE_CLAIMS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            warnings.append(f"promessa absoluta detectada: {pattern}")
    return warnings


def action_gate(
    action: ActionLevel,
    records: Iterable[SourceMetadata],
    *,
    human_approval: bool = False,
    purpose: str | None = None,
) -> GateDecision:
    reasons: list[str] = []
    requirements: list[str] = []
    records = list(records)

    if purpose in HIGH_RISK_PURPOSES:
        reasons.append("finalidade proibida ou de alto risco pela governação MILK")

    if action in {ActionLevel.MODIFY, ActionLevel.PUBLISH} and not human_approval:
        reasons.append("alteração ou publicação exige aprovação humana explícita")

    if action == ActionLevel.PUBLISH:
        for record in records:
            if record.visibility != Visibility.PUBLIC:
                reasons.append(f"{record.source_id}: camada não pública")
            if record.rights_status != "validado":
                requirements.append(f"{record.source_id}: validar direitos")
            if record.rgpd_status != "validado":
                requirements.append(f"{record.source_id}: validar RGPD")
            if not record.human_validated:
                requirements.append(f"{record.source_id}: validação humana pendente")

    return GateDecision(not reasons and not requirements, reasons, requirements)


def remote_processing_allowed(record: SourceMetadata, allowed_layers: set[str]) -> bool:
    return record.visibility.value in allowed_layers and record.rgpd_status == "validado"

