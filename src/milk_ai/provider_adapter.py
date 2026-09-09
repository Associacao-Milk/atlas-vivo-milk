"""MILK IA — Sovereign provider abstraction.

The core never imports a proprietary SDK or vendor type. Every external
capability (embeddings, grounded synthesis) flows through a
``ProviderAdapter``. ``LocalAdapter`` is the always-available offline
fallback with zero network access and zero third-party SDKs.

Design contract:
- ``ProviderAdapter`` is a structural ``Protocol`` — no base class needed,
  so vendor wrappers stay outside the core and only need to *match* the shape.
- The core imports ONLY this module for external capabilities, never
  ``mistral``, ``openai`` etc. directly.
- ``LocalAdapter`` is pure-Python and deterministic: it must never touch the
  network, the filesystem outside its constructor inputs, or any binary dep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProviderAdapter(Protocol):
    """Structural contract every provider must satisfy.

    ``is_local`` distinguishes the sovereign fallback from remote providers.
    ``available()`` is queried at call time — a remote provider may report
    ``False`` (no key / no network) and the core falls back to ``LocalAdapter``.
    """

    name: str
    is_local: bool

    def available(self) -> bool: ...

    def embeddings(self, texts: list[str]) -> list[list[float]]: ...

    def grounded_answer(
        self, question: str, contexts: list[dict[str, Any]]
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class LocalAdapter:
    """Offline, deterministic, dependency-free fallback.

    Produces NO dense embeddings (returns empty vectors so the retriever
    falls back to lexical-only search) and synthesises answers by
    deterministic evidence selection — no LLM, no network, no SDK.
    """

    name: str = "local-offline"
    is_local: bool = True

    def available(self) -> bool:
        return True

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        # No dense model offline — signal "no semantic path" to the retriever.
        return [[] for _ in texts]

    def grounded_answer(
        self, question: str, contexts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        citations = [item.get("chunk_id", item.get("citation", "")) for item in contexts]
        facts: list[str] = []
        for item in contexts:
            text = (item.get("text") or "").strip().replace("\n", " ")
            if text:
                facts.append(text[:280])
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
            "warnings": ["modo soberano/offline: sem LLM externo, sintese deterministica"],
            "model": self.name,
        }


def select_provider(
    primary: ProviderAdapter | None, fallback: ProviderAdapter | None = None
) -> ProviderAdapter:
    """Return the first available provider, else the sovereign ``LocalAdapter``.

    This is the single choke-point the core uses — it guarantees MILK always
    has a working provider even with no credentials and no network.
    """
    if primary is not None and primary.available():
        return primary
    if fallback is not None and fallback.available():
        return fallback
    return LocalAdapter()


def assert_core_sovereign(loaded_modules: set[str]) -> list[str]:
    """Return a list of sovereignty violations found in ``loaded_modules``.

    A violation is any loaded module whose top-level package is a known
    proprietary/cloud SDK. The stdlib, numpy, sklearn and this package are
    always allowed.
    """
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
