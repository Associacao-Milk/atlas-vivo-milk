"""MILK IA - Sovereign provider abstraction.

The core never imports a proprietary SDK or vendor type. Every external
capability (embeddings, grounded synthesis) flows through a
``ProviderAdapter``. ``LocalAdapter`` is the always-available offline
fallback: it never touches the network except an optional local Ollama
instance at http://localhost:11434 (same machine, sovereign).

Model routing (2026-09-19): the active Ollama model is chosen by the
action channel via ``model_routing.model_for_channel``. No subordinate
agent picks a model on its own.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .model_routing import model_for_channel

OLLAMA_URL = "http://localhost:11434"


def _ollama_chat(prompt: str, model: str, timeout: int = 300) -> str | None:
    """Call the local Ollama HTTP API (localhost only). None if unavailable."""
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": False,
         "options": {"temperature": 0.2}}
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL + "/api/generate", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            return str(body.get("response", "")).strip() or None
    except Exception:
        return None


def _ollama_list() -> list[str]:
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
            return [item.get("name", "") for item in body.get("models", [])]
    except Exception:
        return []


@runtime_checkable
class ProviderAdapter(Protocol):
    name: str
    is_local: bool

    def available(self) -> bool: ...

    def embeddings(self, texts: list[str]) -> list[list[float]]: ...

    def grounded_answer(
        self, question: str, contexts: list[dict[str, Any]]
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class LocalAdapter:
    """Offline fallback with optional local-LLM synthesis via Ollama.

    If an Ollama server answers on localhost, answers are written in natural
    language by the local model (grounded on the retrieved evidence).
    Otherwise it stays fully deterministic with zero network access.

    The Ollama model follows the canonical channel routing
    (atlas_publico -> fast model; everything else -> rigor model).
    """

    name: str = "local-offline"
    is_local: bool = True
    ollama_model: str = "mistral:latest"

    def set_channel(self, channel: str) -> str:
        """Route to the canonical model for this action channel.

        Returns the model now in effect (also keeps ollama_model in sync
        so status/manifests reflect the active model).
        """
        self.ollama_model = model_for_channel(channel)
        return self.ollama_model

    def available(self) -> bool:
        return True

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[] for _ in texts]

    def grounded_answer(
        self, question: str, contexts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        citations = [item.get("chunk_id", item.get("citation", "")) for item in contexts]
        facts: list[str] = []
        for item in contexts:
            text = (item.get("text") or "").strip().replace("\n", " ")
            if text:
                facts.append(text[:1200])
        warnings: list[str] = []

        if facts:
            evidence = "\n\n".join(
                f"[Fonte {index + 1}] {fact}" for index, fact in enumerate(facts)
            )
            prompt = (
                "E uma IA local da Associacao MILK que responde em portugues "
                "de Portugal, com honestidade e sem inventar.\n"
                "Responde a pergunta do utilizador usando APENAS a evidencia "
                "abaixo. Cita as fontes como [Fonte N]. Se a evidencia nao "
                "chegar para responder, diz claramente o que falta.\n\n"
                f"Pergunta: {question}\n\nEvidencia:\n{evidence}"
            )
            answer_text = _ollama_chat(prompt, self.ollama_model)
            if answer_text:
                return {
                    "text": answer_text,
                    "confidence": "local-llm",
                    "citations": citations,
                    "facts": facts,
                    "inferences": [],
                    "unknowns": [],
                    "warnings": ["sintese por LLM local (Ollama): validar antes de publicar"],
                    "model": f"ollama/{self.ollama_model}",
                }
            warnings.append("Ollama indisponivel: sintese deterministica sem LLM")

        synthesis = (
            f"[soberano/offline] Evidencia local recuperada para: {question}. "
            f"{len(facts)} fragmentos citados. Sintese deterministica sem LLM externo."
        )
        return {
            "text": synthesis,
            "confidence": "nao_calculada",
            "citations": citations,
            "facts": facts,
            "inferences": [],
            "unknowns": [question] if not facts else [],
            "warnings": warnings or ["modo soberano/offline: sem LLM externo, sintese deterministica"],
            "model": self.name,
        }


def select_provider(
    primary: ProviderAdapter | None, fallback: ProviderAdapter | None = None
) -> ProviderAdapter:
    if primary is not None and primary.available():
        return primary
    if fallback is not None and fallback.available():
        return fallback
    return LocalAdapter()


def assert_core_sovereign(loaded_modules: set[str]) -> list[str]:
    forbidden_prefixes = (
        "mistralai", "openai", "anthropic", "google.generativeai",
        "google.cloud.aiplatform", "mcp", "langchain",
    )
    allowed_prefixes = ("milk_ai", "numpy", "sklearn", "scipy")
    violations: list[str] = []
    for mod in sorted(loaded_modules):
        if mod.startswith(allowed_prefixes):
            continue
        if mod.startswith(forbidden_prefixes):
            violations.append(mod)
    return violations
