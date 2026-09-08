from __future__ import annotations

from dataclasses import dataclass

from .governance_models import AgentRole, ExecutionReceipt, TaskEnvelope


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    role: AgentRole
    capabilities: tuple[str, ...]
    external_write_allowed: bool


CATALOG: dict[AgentRole, AgentDefinition] = {
    AgentRole.ORCHESTRATOR: AgentDefinition(
        AgentRole.ORCHESTRATOR,
        ("rotear_tarefa", "verificar_estado", "emitir_receipt"),
        False,
    ),
    AgentRole.HERMENEUT: AgentDefinition(
        AgentRole.HERMENEUT,
        ("auditar_texto", "mapear_conceitos", "separar_facto_inferencia", "consolidar"),
        False,
    ),
    AgentRole.PROFILE: AgentDefinition(
        AgentRole.PROFILE,
        ("validar_orcid", "preparar_metadados_perfil", "comparar_registos"),
        False,
    ),
    AgentRole.INTEROPERABILITY: AgentDefinition(
        AgentRole.INTEROPERABILITY,
        ("validar_metadados", "mapear_standards", "preparar_exportacao"),
        False,
    ),
    AgentRole.FUNDING: AgentDefinition(
        AgentRole.FUNDING,
        ("ler_aviso", "mapear_elegibilidade", "preparar_proposta"),
        False,
    ),
}


def route_task(task: TaskEnvelope) -> tuple[AgentDefinition, ExecutionReceipt]:
    agent = CATALOG[task.role]
    warnings: list[str] = []
    executed = False
    state = "preparado"
    if task.requires_external_write:
        warnings.append("escrita externa bloqueada: requer conector, autorização e receipt específico")
    else:
        state = "analisado"
    return agent, ExecutionReceipt(
        task_id=task.task_id,
        agent_role=task.role,
        state=state,
        executed=executed,
        warnings=warnings,
    )

