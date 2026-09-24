from __future__ import annotations

import os

from pathlib import Path
from typing import Any

from .ingest import CorpusStore
from .mistral import MistralClient, MistralAdapter
from .models import Answer, Visibility
from .policies import truth_claim_warnings
from .provider_adapter import LocalAdapter, ProviderAdapter, select_provider
from .retrieval import HybridRetriever


class MilkAI:
    """Sovereign core: works offline with LocalAdapter; uses a ProviderAdapter
    (MistralAdapter, future OpenAI/Anthropic adapters) only when available.

    The core never imports a vendor SDK directly - it depends on the
    ``ProviderAdapter`` abstraction. ``mistral`` is accepted for backward
    compatibility and wrapped in ``MistralAdapter``.

    Model routing (2026-09-19): ``query`` accepts a ``channel`` (atlas_publico,
    dominio_milk, perfil_publico, documental). The channel selects the local
    Ollama model per the canonical policy in ``model_routing.py``.
    """

    def __init__(
        self,
        state_dir: Path,
        *,
        provider: ProviderAdapter | None = None,
        mistral: MistralClient | None = None,
        semantic: bool = False,
        remote_allowed_layers: set[str] | None = None,
    ):
        self.state_dir = state_dir
        self.store = CorpusStore(state_dir / "corpus")
        if provider is None and mistral is not None:
            provider = MistralAdapter(mistral)
        self.provider = select_provider(provider)
        self.remote_allowed_layers = remote_allowed_layers or {"publica", "licenciavel"}
        embed = self.provider.embeddings if self.provider.available() and not self.provider.is_local and semantic else None
        self.retriever = HybridRetriever(self.store.chunks(), embed=embed, cache_dir=os.path.join(str(self.state_dir), "retriever_cache"))

    def refresh(self, semantic: bool = False) -> None:
        embed = self.provider.embeddings if self.provider.available() and not self.provider.is_local and semantic else None
        self.retriever = HybridRetriever(self.store.chunks(), embed=embed, cache_dir=os.path.join(str(self.state_dir), "retriever_cache"))

    def ingest(
        self,
        path: Path,
        visibility: Visibility = Visibility.RESTRICTED,
        *,
        secret_mode: str = "quarantine",
    ) -> list[dict[str, Any]]:
        results = self.store.ingest_tree(path, visibility=visibility, secret_mode=secret_mode)
        self.refresh(semantic=False)
        return results

    def update_governance(self, source_id: str, changes: dict[str, Any], **audit: Any) -> dict[str, Any]:
        result = self.store.update_governance(source_id, changes, **audit)
        self.refresh(semantic=False)
        return result

    def query(
        self,
        question: str,
        limit: int = 5,
        visibility: set[str] | None = None,
        channel: str = "dominio_milk",
    ) -> Answer:
        # Canonical channel routing: pick the local Ollama model before synthesis.
        if isinstance(self.provider, LocalAdapter):
            self.provider.set_channel(channel)

        hits = self.retriever.search(question, limit=limit, visibility=visibility)
        if not hits:
            return Answer(
                text="Não encontrei evidência suficiente no corpus autorizado.",
                state="analisado",
                confidence="baixa",
                citations=[], facts=[], inferences=[], unknowns=[question], warnings=[],
            )
        if self.provider.is_local:
            payload = self.provider.grounded_answer(
                question, [hit.to_dict() for hit in hits]
            )
            answer = Answer(
                text=str(payload.get("text", "")),
                state="analisado",
                confidence=str(payload.get("confidence", "não_calculada")),
                citations=list(payload.get("citations", [])),
                facts=list(payload.get("facts", [])),
                inferences=list(payload.get("inferences", [])),
                unknowns=list(payload.get("unknowns", [])),
                warnings=list(payload.get("warnings", [])),
                model=self.provider.name,
            )
            answer.warnings.extend(truth_claim_warnings(answer.text))
            return answer

        remotely_allowed = [
            hit for hit in hits
            if hit.metadata.get("visibility") in self.remote_allowed_layers
            and hit.metadata.get("rgpd_status") == "validado"
        ]
        if not remotely_allowed:
            return Answer(
                text="A evidência foi encontrada localmente, mas a política não permite enviá-la ao serviço remoto.",
                state="analisado",
                confidence="não_calculada",
                citations=[hit.chunk_id for hit in hits], facts=[], inferences=[], unknowns=[],
                warnings=["camada não autorizada ou RGPD por validar: síntese remota bloqueada"],
            )
        payload = self.provider.grounded_answer(question, [hit.to_dict() for hit in remotely_allowed])
        answer = Answer(
            text=str(payload.get("text", "")),
            state="inferido",
            confidence=str(payload.get("confidence", "não_calculada")),
            citations=list(payload.get("citations", [])),
            facts=list(payload.get("facts", [])),
            inferences=list(payload.get("inferences", [])),
            unknowns=list(payload.get("unknowns", [])),
            warnings=list(payload.get("warnings", [])),
            model=getattr(self.provider, "chat_model", self.provider.name),
        )
        answer.warnings.extend(truth_claim_warnings(answer.text))
        return answer
