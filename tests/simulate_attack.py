#!/usr/bin/env python3
"""Simulação de Ataque Cibernético — MILK IA Sovereignty Gate.

Testa as defesas do sistema contra Sovereignty Spoofing: uma entidade
maliciosa tenta injetar um payload adulterando os metadados do autor
original ou alterando o ORCID para contornar o sistema de auditoria.

Demonstra em tempo real o acionamento do gatilho de pânico operacional.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from milk_ai.provenance import CANONICAL_AUTHOR
from milk_ai.exceptions import SecurityException, SovereigntyPanicController


def verify_payload_integrity(provenance_manifest: dict) -> bool:
    """Gate de Produção — verifica se a genealogia autoral respeita o design original."""
    required_orcid = CANONICAL_AUTHOR.get("orcid", "0009-0007-6892-6570")

    if provenance_manifest.get("prov:wasAttributedTo") != f"orcid:{required_orcid}":
        SovereigntyPanicController.handle_auth_breach(
            provenance_manifest.get("prov:wasAttributedTo", "MISSING"),
            required_orcid,
        )
        return False

    return True


def run_cyber_attack_simulation():
    print("=" * 70)
    print(" SIMULAÇÃO DE ATAQUE CIBERNÉTICO — MILK IA SECURITY GATE ")
    print("=" * 70)

    SovereigntyPanicController.reset()

    payload_legitimo = {
        "id": "urn:milk:annotation:001",
        "prov:wasAttributedTo": "orcid:0009-0007-6892-6570"
    }

    payload_hacker = {
        "id": "urn:milk:annotation:666",
        "prov:wasAttributedTo": "orcid:0009-0007-9999-9999"
    }

    print("\n[Cenário 1] Injetando pacote de dados legítimo...")
    try:
        if verify_payload_integrity(payload_legitimo):
            print(">> [PASS] GATE reconheceu o autor originário. Tráfego liberado.")
        else:
            print(">> [FAIL] Erro inesperado no fluxo legítimo.")
    except SecurityException:
        print(">> [FAIL] Exceção inesperada no fluxo legítimo.")

    print("\n[Cenário 2] ALERTA: Hacker tentando injetar metadados falsos...")
    try:
        verify_payload_integrity(payload_hacker)
        print(">> [ALERTA CRÍTICO] O sistema falhou! O tráfego hacker passou!")
    except SecurityException as ex:
        print("\n" + "#" * 50)
        print(" COUNTER-ATTACK TRIGGERED: PARAGUARDA ACIONADA! ")
        print(f" Detalhe: {ex}")
        print(f" Estado: {'LOCKED_READ_ONLY' if SovereigntyPanicController.is_frozen() else 'NORMAL'}")
        print("#" * 50)
        print("\n>> [SUCESSO] Invasão contida. Sistema preferiu auto-bloqueio à corrupção.")


if __name__ == "__main__":
    run_cyber_attack_simulation()
