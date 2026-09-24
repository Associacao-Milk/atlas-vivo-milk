"""Model routing by action layer - MILK IA.

Politica canonica (2026-09-19, Eduardo):
- Camada publica do Atlas Vivo (interacao com visitantes) -> llama3.2:3b
- Dominio proprio da IA MILK, perfis publicos (Associacao, Eduardo, Nuno)
  e atuacao documental (formularios, respostas de email) -> mistral:latest
Nenhum agente subordinado escolhe modelo por conta propria.
"""
from __future__ import annotations

FAST_MODEL = "llama3.2:3b"
RIGOR_MODEL = "mistral:latest"

CHANNEL_MODELS = {
    "atlas_publico": FAST_MODEL,
    "dominio_milk": RIGOR_MODEL,
    "perfil_publico": RIGOR_MODEL,
    "documental": RIGOR_MODEL,
}
DEFAULT_MODEL = RIGOR_MODEL


def model_for_channel(channel):
    """Devolve o modelo Ollama autorizado para o canal de atuacao pedido."""
    if not channel:
        return DEFAULT_MODEL
    return CHANNEL_MODELS.get(channel, DEFAULT_MODEL)
