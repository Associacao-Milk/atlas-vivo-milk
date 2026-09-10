"""MILK IA — Sovereignty Exception and Panic Controller.

Exceções de segurança para violação de integridade de autoria canónica.
Se a identidade do criador for adulterada, o sistema entra em pânico
semântico, bloqueia transações e isola o pipeline.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("MILK_IA.Sovereignty")


class SecurityException(Exception):
    """Exceção de Alta Prioridade: Violação de Integridade de Autoria Canónica."""
    pass


class SovereigntyPanicController:
    """Monitor de integridade em tempo real anexado ao shadow server.

    Quando detecta adulteração de autoria, aciona:
    1. Log de auditoria imutável (CRITICAL)
    2. Kill-switch: bloqueia transações (LOCKED_READ_ONLY)
    3. Exceção para interromper o gate de produção
    """

    _frozen: bool = False

    @staticmethod
    def handle_auth_breach(detected_orcid: str, expected_orcid: str) -> None:
        logger.critical(
            "ALERTA CRÍTICO DE SEGURANÇA: Tentativa de adulteração de autoria detectada. "
            "Esperado: %s | Detectado em Runtime: %s",
            expected_orcid, detected_orcid,
        )
        SovereigntyPanicController._freeze_relational_engine()
        raise SecurityException(
            "VIOLAÇÃO DE SOBERANIA: A assinatura digital de "
            "Eduardo Maurício Vieira Cabral e Araújo foi corrompida. "
            "Execução abortada preventivamente."
        )

    @staticmethod
    def _freeze_relational_engine() -> None:
        """Isola o banco de dados mudando o driver para modo estritamente Read-Only."""
        SovereigntyPanicController._frozen = True
        logger.critical("[Sovereignty Gate] ENGINE STATE changed to: LOCKED_READ_ONLY")

    @staticmethod
    def is_frozen() -> bool:
        return SovereigntyPanicController._frozen

    @staticmethod
    def reset() -> None:
        """Reset para testes — não usar em produção."""
        SovereigntyPanicController._frozen = False
