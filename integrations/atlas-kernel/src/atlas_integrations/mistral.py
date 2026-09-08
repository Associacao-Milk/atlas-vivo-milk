from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from .http import SafeHttpClient


class AgentEnvelope(BaseModel):
    task_id: str
    origin_agent: str = "orquestrador"
    target_agent: str
    action: str
    data_classification: str
    source_refs: list[str] = Field(default_factory=list)
    review_required: bool = True
    status: str = "PENDENTE"
    log_ref: str
    payload: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class AgentSpec:
    role: str
    model_kind: str
    mission: str


AGENTS: dict[str, AgentSpec] = {
    "arquiteto_ecossistema": AgentSpec("arquiteto_ecossistema", "default", "Arquitetura, dependências e contratos."),
    "ontologia_protocolos_dados": AgentSpec("ontologia_protocolos_dados", "default", "Ontologia mínima, schemas, PIDs e semântica."),
    "codificador_modulos": AgentSpec("codificador_modulos", "code", "Código reversível conforme especificação."),
    "revisao_repositorio": AgentSpec("revisao_repositorio", "code", "Revisão de segurança, regressão e qualidade."),
    "testes_validacao": AgentSpec("testes_validacao", "code", "Testes, evidências e critérios de aceitação."),
    "documentacao_memoria": AgentSpec("documentacao_memoria", "default", "Documentação institucional e proveniência."),
    "conformidade_rgpd_soberania": AgentSpec("conformidade_rgpd_soberania", "default", "RGPD, AI Act, minimização e soberania."),
    "publicacao_interoperavel": AgentSpec("publicacao_interoperavel", "default", "ROR, DataCite, ORCID, Zenodo, SWH, Forgejo e FIWARE."),
    "migracao_preservativa": AgentSpec("migracao_preservativa", "code", "Checkpoint, hashes, contagens e transferência sem alterar a fonte."),
    "monitorizacao_financiabilidade": AgentSpec("monitorizacao_financiabilidade", "default", "Indicadores verificáveis, programas e oportunidades."),
}


class CloudPolicyError(RuntimeError):
    pass


class MistralOrchestrator:
    """Orquestra papéis Mistral sem enviar dados pessoais/confidenciais por omissão."""

    def __init__(self, api_key: str | None = None, *, default_model: str = "mistral-medium-latest",
                 code_model: str = "devstral-medium-latest", allow_restricted: bool = False):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.default_model = default_model
        self.code_model = code_model
        self.allow_restricted = allow_restricted
        self.client = SafeHttpClient({"api.mistral.ai"}, timeout=60, retries=3)

    @staticmethod
    def _redact(value: Any) -> Any:
        secret_keys = {"api_key", "apikey", "token", "secret", "password", "client_secret"}
        if isinstance(value, dict):
            return {key: "[DADO_REMOVIDO]" if key.lower().replace("-", "_") in secret_keys
                    else MistralOrchestrator._redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [MistralOrchestrator._redact(item) for item in value]
        if isinstance(value, str):
            value = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
                           "[DADO_REMOVIDO]", value, flags=re.IGNORECASE)
            return re.sub(r"\b\d{9}\b", "[DADO_REMOVIDO]", value)
        return value

    def prepare(self, envelope: AgentEnvelope) -> dict[str, Any]:
        if envelope.target_agent not in AGENTS:
            raise CloudPolicyError("agente não registado")
        if envelope.data_classification in {"confidencial", "dados_pessoais"}:
            raise CloudPolicyError("classe bloqueada para processamento cloud")
        if envelope.data_classification == "restrito" and not self.allow_restricted:
            raise CloudPolicyError("contexto restrito exige política explícita")
        spec = AGENTS[envelope.target_agent]
        safe_payload = self._redact(envelope.payload)
        system = (
            f"Atua como {spec.role} do Atlas Vivo MILK. Missão: {spec.mission} "
            "Português europeu. Preserva originais. Não publiques, apagues, movas ou inventes factos. "
            "Distingue proposta de execução. Devolve JSON com status, findings, actions, tests, "
            "source_refs, review_required e log_ref."
        )
        model = self.code_model if spec.model_kind == "code" else self.default_model
        return {"model": model, "temperature": 0.1, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": json.dumps({
                                 "task_id": envelope.task_id, "action": envelope.action,
                                 "source_refs": envelope.source_refs, "payload": safe_payload,
                                 "review_required": envelope.review_required,
                                 "log_ref": envelope.log_ref}, ensure_ascii=False)}]}

    def run(self, envelope: AgentEnvelope, *, execute: bool = False) -> dict[str, Any]:
        request = self.prepare(envelope)
        request_hash = sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        if not execute:
            return {"executed": False, "status": "VALIDADO_SEM_EXECUTAR", "request_hash": request_hash,
                    "agent": envelope.target_agent, "model": request["model"]}
        if not self.api_key:
            raise CloudPolicyError("MISTRAL_API_KEY em falta")
        response = self.client.request("POST", "https://api.mistral.ai/v1/chat/completions",
                                       json_body=request, headers={"Authorization": f"Bearer {self.api_key}"})
        return {"executed": True, "status": "CONCLUIDO", "request_hash": request_hash,
                "agent": envelope.target_agent, "result": response.body}


class EngineeringWorkflow:
    STAGES = (
        "arquiteto_ecossistema", "ontologia_protocolos_dados", "conformidade_rgpd_soberania",
        "codificador_modulos", "revisao_repositorio", "testes_validacao",
        "migracao_preservativa", "publicacao_interoperavel", "documentacao_memoria",
        "monitorizacao_financiabilidade",
    )

    def plan(self, task_id: str, action: str, source_refs: list[str], payload: dict[str, Any],
             classification: str = "interno") -> list[AgentEnvelope]:
        return [AgentEnvelope(task_id=f"{task_id}-{i:02d}", target_agent=agent, action=action,
                              data_classification=classification, source_refs=source_refs,
                              log_ref=f"audit/{task_id}/{i:02d}-{agent}.json", payload=payload)
                for i, agent in enumerate(self.STAGES, start=1)]
