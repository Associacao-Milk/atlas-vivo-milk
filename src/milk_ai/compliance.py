"""MILK IA — Machine-readable ComplianceProfile.

Each profile is a deterministic, auditable data structure (no external SDK)
declaring the standard, its jurisdiction, mandatory controls, evidence
requirements and an evaluation function over a MILK artifact's governance
metadata. Profiles are versioned; the registry is the single source of
truth used by the sovereign core to emit compliance claims.

Standards covered:
- EIF / Mosaico-RNID / iAP   (interoperability, digital identity, Portugal)
- ENTI / ARPGU / CNMD / FIWARE (entities, registers, smart cities, IoT)
- AI Act                      (EU regulation 2024/1689)
- ISO/IEC 42001               (AI management system)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable


class ComplianceVerdict(StrEnum):
    CONFORMANT = "conforme"
    PARTIAL = "parcial"
    NON_CONFORMANT = "nao_conforme"
    NOT_APPLICABLE = "nao_aplicavel"
    NOT_ASSESSED = "nao_avaliado"


# A control evaluator receives a governance metadata dict and returns
# (verdict, evidence_keys, note).
ControlEvaluator = Callable[[dict[str, Any]], tuple[ComplianceVerdict, list[str], str]]


@dataclass(slots=True)
class ComplianceControl:
    control_id: str
    title: str
    mandatory: bool
    evaluate: ControlEvaluator


@dataclass(slots=True)
class ComplianceProfile:
    profile_id: str
    standard: str
    version: str
    jurisdiction: str
    scope: str
    controls: list[ComplianceControl]
    description: str = ""

    def assess(self, governance: dict[str, Any]) -> "ComplianceAssessment":
        results: list[dict[str, Any]] = []
        for ctrl in self.controls:
            verdict, evidence, note = ctrl.evaluate(governance)
            results.append({
                "control_id": ctrl.control_id,
                "title": ctrl.title,
                "mandatory": ctrl.mandatory,
                "verdict": verdict.value,
                "evidence_keys": evidence,
                "note": note,
            })
        mandatory_fails = [
            r for r in results
            if r["mandatory"] and r["verdict"] == ComplianceVerdict.NON_CONFORMANT.value
        ]
        if mandatory_fails:
            overall = ComplianceVerdict.NON_CONFORMANT
        elif any(r["verdict"] == ComplianceVerdict.PARTIAL.value for r in results):
            overall = ComplianceVerdict.PARTIAL
        elif all(
            r["verdict"] == ComplianceVerdict.CONFORMANT.value
            for r in results if r["mandatory"]
        ):
            overall = ComplianceVerdict.CONFORMANT
        else:
            overall = ComplianceVerdict.NOT_ASSESSED
        return ComplianceAssessment(
            profile_id=self.profile_id,
            standard=self.standard,
            version=self.version,
            overall=overall.value,
            controls=results,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )


@dataclass(slots=True)
class ComplianceAssessment:
    profile_id: str
    standard: str
    version: str
    overall: str
    controls: list[dict[str, Any]]
    assessed_at: str


# ---------------------------------------------------------------------------
# Control evaluators (pure functions over governance metadata)
# ---------------------------------------------------------------------------

def _bool_field(key: str) -> ControlEvaluator:
    def evaluate(g: dict[str, Any]) -> tuple[ComplianceVerdict, list[str], str]:
        val = g.get(key)
        if val is True or val == "validado" or val == "verificado":
            return ComplianceVerdict.CONFORMANT, [key], f"{key} presente e positivo"
        if val is None:
            return ComplianceVerdict.NOT_ASSESSED, [], f"{key} ausente"
        return ComplianceVerdict.NON_CONFORMANT, [key], f"{key}={val}"
    return evaluate


def _present_field(key: str) -> ControlEvaluator:
    def evaluate(g: dict[str, Any]) -> tuple[ComplianceVerdict, list[str], str]:
        val = g.get(key)
        if val:
            return ComplianceVerdict.CONFORMANT, [key], f"{key} definido"
        return ComplianceVerdict.NON_CONFORMANT, [key], f"{key} em falta"
    return evaluate


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

_EIF = ComplianceProfile(
    profile_id="eif-mosaico-rnid-iap",
    standard="EIF / Mosaico-RNID / iAP",
    version="2024.1",
    jurisdiction="PT-EU",
    scope="Interoperabilidade digital, identidade e autenticacao de servicos",
    description="European Interoperability Framework + Mosaico RNID + iAP Portugal",
    controls=[
        ComplianceControl("EIF-1", "Interoperabilidade semantica (ontologia versionada)", True,
                          _present_field("ontology_version")),
        ComplianceControl("EIF-2", "Proveniencia do documento (SHA-256)", True,
                          _present_field("sha256")),
        ComplianceControl("RNID-1", "Identidade digital do responsavel (ORCID/NIFF)", True,
                          _present_field("responsible_entity")),
        ComplianceControl("IAP-1", "Consentimento RGPD explicito", True,
                          _bool_field("consent_status")),
        ComplianceControl("IAP-2", "Estado RGPD validado", True,
                          _bool_field("rgpd_status")),
    ],
)

_ENTI = ComplianceProfile(
    profile_id="enti-arpgu-cnmd-fiware",
    standard="ENTI / ARPGU / CNMD / FIWARE",
    version="2023.2",
    jurisdiction="PT-EU",
    scope="Entidades, registos, modelacao de dados territoriais e IoT",
    description="ENg de TI / ARquivo PGU / Cadastro Nac. Modelos Dados / FIWARE NGSI-LD",
    controls=[
        ComplianceControl("ENTI-1", "Entidade responsavel identificada", True,
                          _present_field("responsible_entity")),
        ComplianceControl("ARPGU-1", "Territorio (municipio/freguesia) classificado", True,
                          _present_field("municipality")),
        ComplianceControl("CNMD-1", "Tipo de documento modelado", True,
                          _present_field("document_type")),
        ComplianceControl("FIWARE-1", "Exportavel em NGSI-LD (entity id estavel)", True,
                          _present_field("source_id")),
    ],
)

_AI_ACT = ComplianceProfile(
    profile_id="ai-act",
    standard="EU AI Act",
    version="2024/1689",
    jurisdiction="EU",
    scope="Regulamento de IA — risco, transparencia, supervisao humana",
    description="Regulamento UE 2024/1689 sobre regras harmonizadas em IA",
    controls=[
        ComplianceControl("AIA-1", "Nivel de risco classificado", True,
                          _present_field("ai_risk_level")),
        ComplianceControl("AIA-2", "Transparencia: humano pode interpretar saida", True,
                          _bool_field("human_validated")),
        ComplianceControl("AIA-3", "Sem decisao automatizada sem supervisao", True,
                          _bool_field("human_validated")),
        ComplianceControl("AIA-4", "Dados de treino rastreaveis (proveniencia)", True,
                          _present_field("sha256")),
    ],
)

_ISO42001 = ComplianceProfile(
    profile_id="iso-42001",
    standard="ISO/IEC 42001",
    version="2023",
    jurisdiction="international",
    scope="Sistema de gestao de IA",
    description="AI management system standard",
    controls=[
        ComplianceControl("ISO42-1", "Politica de IA documentada", True,
                          _present_field("ai_policy_ref")),
        ComplianceControl("ISO42-2", "Avaliacao de impacto de IA", True,
                          _present_field("ai_impact_assessment")),
        ComplianceControl("ISO42-3", "Validacao humana registada", True,
                          _bool_field("human_validated")),
        ComplianceControl("ISO42-4", "Rastreabilidade de alteracoes", True,
                          _present_field("change_log_ref")),
    ],
)

PROFILE_REGISTRY: dict[str, ComplianceProfile] = {
    p.profile_id: p for p in (_EIF, _ENTI, _AI_ACT, _ISO42001)
}


def assess_all(governance: dict[str, Any]) -> list[ComplianceAssessment]:
    return [profile.assess(governance) for profile in PROFILE_REGISTRY.values()]
