from __future__ import annotations

from pathlib import Path
from typing import Any

from .ingest import CorpusStore
from .mistral import MistralClient
from .models import Answer, Visibility
from .policies import truth_claim_warnings
from .retrieval import HybridRetriever


class MilkAI:
    def __init__(
        self,
        state_dir: Path,
        *,
        mistral: MistralClient | None = None,
        semantic: bool = False,
        remote_allowed_layers: set[str] | None = None,
    ):
        self.store = CorpusStore(state_dir / "corpus")
        self.mistral = mistral
        self.remote_allowed_layers = remote_allowed_layers or {"publica", "licenciavel"}
        embed = mistral.embeddings if mistral and semantic else None
        self.retriever = HybridRetriever(self.store.chunks(), embed=embed)

    def refresh(self, semantic: bool = False) -> None:
        embed = self.mistral.embeddings if self.mistral and semantic else None
        self.retriever = HybridRetriever(self.store.chunks(), embed=embed)

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

    def query(self, question: str, limit: int = 5, visibility: set[str] | None = None) -> Answer:
        hits = self.retriever.search(question, limit=limit, visibility=visibility)
        if not hits:
            return Answer(
                text="Não encontrei evidência suficiente no corpus autorizado.",
                state="analisado",
                confidence="baixa",
                citations=[], facts=[], inferences=[], unknowns=[question], warnings=[],
            )
        if not self.mistral:
            return Answer(
                text="Foram recuperadas evidências locais; a síntese Mistral não foi executada.",
                state="analisado",
                confidence="não_calculada",
                citations=[hit.chunk_id for hit in hits],
                facts=[], inferences=[], unknowns=[],
                warnings=["MISTRAL_API_KEY ausente ou modo local seleccionado"],
            )

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
        payload = self.mistral.grounded_answer(question, [hit.to_dict() for hit in remotely_allowed])
        answer = Answer(
            text=str(payload.get("text", "")),
            state="inferido",
            confidence=str(payload.get("confidence", "não_calculada")),
            citations=list(payload.get("citations", [])),
            facts=list(payload.get("facts", [])),
            inferences=list(payload.get("inferences", [])),
            unknowns=list(payload.get("unknowns", [])),
            warnings=list(payload.get("warnings", [])),
            model=self.mistral.chat_model,
        )
        answer.warnings.extend(truth_claim_warnings(answer.text))
        return answer
