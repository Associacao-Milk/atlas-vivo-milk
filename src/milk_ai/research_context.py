"""MILK IA — Research Context Gate (research-before-reasoning).

Mandatory gate for every substantial MILK research/curatorial task:

    TASK
    -> intent/domain detection
    -> semantic seed retrieval
    -> ACTIVE_REFERENCE selection
    -> hypergraph traversal
    -> original source recovery
    -> method/repertoire retrieval
    -> territorial/temporal/context retrieval
    -> reranking
    -> bounded ResearchContext
    -> EvidenceBundle
    -> reasoning
    -> response/action

MILK workers MUST NOT reason from model priors alone when relevant MILK
knowledge exists. A ResearchTrace records the full provenance of every
research act. When evidence is insufficient, a ResearchGap is a valid,
successful outcome — never hallucinate to avoid a gap.

This module reuses the existing SovereignHypergraph and provenance layer; it
adds no parallel content store.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .hypergraph import SovereignHypergraph, ReferenceCapsule, ResearchGap
from .runtime_nomenclature import RUNTIME_ROLES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid(seed: str = "") -> str:
    return hashlib.sha256(f"{_now()}{seed}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# ResearchTrace — full provenance of one research act
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ResearchTrace:
    """Immutable record of a single research-act's retrieval provenance."""
    task_id: str
    trace_id: str = field(default_factory=lambda: _uuid("trace"))
    detected_domains: list[str] = field(default_factory=list)
    reference_queries: list[str] = field(default_factory=list)
    references_considered: list[str] = field(default_factory=list)
    references_selected: list[str] = field(default_factory=list)
    references_rejected: list[str] = field(default_factory=list)
    rejection_reason: dict[str, str] = field(default_factory=dict)
    graph_paths: list[list[str]] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    method_nodes: list[str] = field(default_factory=list)
    multimodal_links: list[str] = field(default_factory=list)
    research_gaps: list[str] = field(default_factory=list)
    worker: str = ""
    runtime_role: str = "validation"
    created_at: str = field(default_factory=_now)

    def __post_init__(self):
        if self.runtime_role not in RUNTIME_ROLES:
            raise ValueError(f"invalid runtime_role: {self.runtime_role}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "trace_id": self.trace_id,
            "detected_domains": self.detected_domains,
            "reference_queries": self.reference_queries,
            "references_considered": list(self.references_considered),
            "references_selected": list(self.references_selected),
            "references_rejected": list(self.references_rejected),
            "rejection_reason": dict(self.rejection_reason),
            "graph_paths": self.graph_paths,
            "source_ids": self.source_ids, "evidence_ids": self.evidence_ids,
            "method_nodes": self.method_nodes,
            "multimodal_links": self.multimodal_links,
            "research_gaps": self.research_gaps,
            "worker": self.worker, "runtime_role": self.runtime_role,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# EvidenceBundle — bounded research output handed to the reasoning worker
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class EvidenceBundle:
    """Bounded, source-grounded evidence for one reasoning act."""
    bundle_id: str
    task_id: str
    trace_id: str
    references: list[ReferenceCapsule] = field(default_factory=list)
    graph_paths: list[list[str]] = field(default_factory=list)
    method_nodes: list[str] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    research_gap: ResearchGap | None = None
    source_count: int = 0
    has_research_context: bool = True
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id, "task_id": self.task_id,
            "trace_id": self.trace_id,
            "references": [r.to_dict() for r in self.references],
            "graph_paths": self.graph_paths,
            "method_nodes": self.method_nodes,
            "contradictions": self.contradictions,
            "research_gap": self.research_gap.to_dict() if self.research_gap else None,
            "source_count": self.source_count,
            "has_research_context": self.has_research_context,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# ResearchContext Gate
# ---------------------------------------------------------------------------

# Lightweight domain keyword detection for intent/domain routing.
_DOMAIN_SEEDS: dict[str, tuple[str, ...]] = {
    "territory/toponymy": ("topónimo", "freguesia", "território", "lugar", "paisagem", "mapa", "caop"),
    "sound/orality": ("som", "sons", "oral", "voz", "soundscape", "sussurro", "escuta", "paisagem sonora"),
    "theatre/performance": ("teatro", "performance", "palco", "corpo", "gesto", "cena", "oprimido"),
    "falarte": ("falarte", "fal arte", "núcleo falarte"),
    "cosmic_flow": ("cosmic flow", "cosmicoxes", "cósmico", "fluxo cósmico"),
    "memory/time": ("memória", "tempo", "passado", "recordação", "oral history"),
    "language": ("linguagem", "palavra", "texto", "poesia", "discurso", "concreta"),
    "curatorial_invention": ("curatorial", "device", "dispositivo", "exposição", "intervenção"),
    "authorship/provenance": ("autor", "autoria", "orcid", "proveniência", "mauer", "nuno a", "assinatura"),
    "contradiction": ("contradição", "conflito", "discrepância", "versão divergente"),
    "multimodal": ("imagem", "fotografia", "vídeo", "audio", "cross-modal", "multimodal"),
    "method": ("método", "device", "schafer", "schaeffer", "boal", "freire", "beckett"),
}


def detect_domains(query: str) -> list[str]:
    q = query.lower()
    hits = []
    for domain, seeds in _DOMAIN_SEEDS.items():
        if any(s in q for s in seeds):
            hits.append(domain)
    return hits or ["general"]


class ResearchContextGate:
    """Enforces research-before-reasoning over a SovereignHypergraph.

    The gate is pluggable: a ``retriever`` callable maps a query to candidate
    node ids (defaults to a label substring match over the hypergraph). The
    gate then selects ACTIVE_REFERENCEs, traverses graph paths, recovers
    methods, preserves contradictions, and either builds a bounded
    EvidenceBundle or records a ResearchGap.
    """

    def __init__(self, graph: SovereignHypergraph,
                 retriever: Callable[[str, SovereignHypergraph, int], list] | None = None,
                 relevance_threshold: float = 1.0):
        self.graph = graph
        self._retriever = retriever or _default_retriever
        self.relevance_threshold = relevance_threshold
        self._traces: list[ResearchTrace] = []
        self._bundles: list[EvidenceBundle] = []
        self._queries_with_context = 0
        self._queries_without_context = 0

    # -- retrieval --------------------------------------------------------

    def retrieve_candidates(self, query: str, limit: int = 10) -> list:
        return self._retriever(query, self.graph, limit)

    # -- main entry -------------------------------------------------------

    def research(self, *, task_id: str, query: str, worker: str = "",
                 runtime_role: str = "validation",
                 max_references: int = 10,
                 max_depth: int = 4,
                 require_human_validation: bool = False) -> EvidenceBundle:
        """Run the research gate and return a bounded EvidenceBundle.

        If no eligible references are found, a ResearchGap is recorded and the
        bundle is still returned (has_research_context reflects whether real
        evidence was gathered). ResearchGap is a valid successful outcome.
        """
        domains = detect_domains(query)
        trace = ResearchTrace(task_id=task_id, worker=worker,
                              runtime_role=runtime_role,
                              detected_domains=domains,
                              reference_queries=[query])

        considered = self.retrieve_candidates(query, max_references)
        # Normalise to (node_id, score) pairs (retriever may return ids or tuples)
        scored: list[tuple[str, float]] = []
        for item in considered:
            if isinstance(item, tuple) and len(item) == 2:
                scored.append((str(item[0]), float(item[1])))
            else:
                scored.append((str(item), 0.0))
        trace.references_considered = [nid for nid, _ in scored]

        # Rerank / select: relevance threshold + ACTIVE_REFERENCE criteria
        # (an ACTIVE_REFERENCE must be relevant + observed + retrievable + traceable)
        selected: list[str] = []
        rejected: list[str] = []
        rejection_reason: dict[str, str] = {}
        for nid, score in scored:
            node = self.graph.get_node(nid)
            if node is None:
                rejected.append(nid)
                rejection_reason[nid] = "node_not_found"
                continue
            if score < self.relevance_threshold:
                rejected.append(nid)
                rejection_reason[nid] = "low_relevance"
                continue
            is_active = bool(node.source_pointer or node.evidence_pointer) or node.validation_state == "validated"
            if is_active:
                selected.append(nid)
            else:
                rejected.append(nid)
                rejection_reason[nid] = "no_source_pointer_pending"
        trace.references_selected = selected
        trace.references_rejected = rejected
        trace.rejection_reason = rejection_reason

        # Graph traversal from selected nodes
        graph_paths: list[list[str]] = []
        if len(selected) >= 2:
            graph_paths = self.graph.path_between(selected[0], selected[1], max_depth=max_depth)
        elif selected:
            adj = self.graph.traverse(selected[0], max_depth=max_depth)
            graph_paths = [[selected[0], n] for n in adj.get(selected[0], [])][:5]
        trace.graph_paths = graph_paths

        # Source + evidence pointers
        source_ids: list[str] = []
        evidence_ids: list[str] = []
        method_nodes: list[str] = []
        multimodal_links: list[str] = []
        for nid in selected:
            node = self.graph.get_node(nid)
            if node is None:
                continue
            if node.source_pointer:
                source_ids.append(node.source_pointer)
            if node.evidence_pointer:
                evidence_ids.append(node.evidence_pointer)
            if node.type == "METHOD":
                method_nodes.append(nid)
            # cross-modal links: neighbors of a different modality
            for edge, nb in self.graph.neighbors(nid):
                if nb.modality != node.modality:
                    multimodal_links.append(f"{nid}-{edge.edge_type}->{nb.id}")
        trace.source_ids = source_ids
        trace.evidence_ids = evidence_ids
        trace.method_nodes = method_nodes
        trace.multimodal_links = multimodal_links

        # Contradictions preserved within the selection
        contradictions = [c for c in self.graph._contradictions
                          if c.get("node_a") in selected or c.get("node_b") in selected]

        bundle_id = f"eb:{_uuid(query)}"
        # Build capsules for selected references
        capsules = self.graph.capsules_for_context(selected, max_capsules=max_references)

        gap: ResearchGap | None = None
        if not selected:
            # Insufficient evidence -> ResearchGap (valid successful outcome)
            gap = self.graph.create_gap(
                question=query,
                missing_evidence=[f"no active references for: {query}"],
                territory=domains[0] if domains else "",
                confidence=0.0,
            )
            trace.research_gaps = [gap.id]
            self._queries_without_context += 1
        else:
            self._queries_with_context += 1

        bundle = EvidenceBundle(
            bundle_id=bundle_id, task_id=task_id, trace_id=trace.trace_id,
            references=capsules, graph_paths=graph_paths,
            method_nodes=method_nodes, contradictions=contradictions,
            research_gap=gap, source_count=len(source_ids),
            has_research_context=bool(selected),
        )
        self._traces.append(trace)
        self._bundles.append(bundle)
        return bundle

    # -- observability ----------------------------------------------------

    def traces(self) -> list[ResearchTrace]:
        return list(self._traces)

    def metrics(self) -> dict[str, Any]:
        return {
            "queries_with_research_context": self._queries_with_context,
            "queries_without_research_context": self._queries_without_context,
            "total_traces": len(self._traces),
            "research_gaps": sum(1 for b in self._bundles if b.research_gap is not None),
        }


def _default_retriever(query: str, graph: SovereignHypergraph, limit: int) -> list[tuple[str, float]]:
    """Label/substring match over hypergraph nodes with integer relevance.

    Returns (node_id, score) tuples. Score = number of query tokens found in
    the label + 2.0 if the whole phrase matches. The gate rejects candidates
    below its relevance threshold (default 1.0), so a node sharing at least one
    meaningful token is considered; relevance rejection plus the
    ACTIVE_REFERENCE (validated + traceable) check filter the rest.
    """
    q = query.lower()
    q_tokens = [t for t in q.split() if t]
    scored: list[tuple[float, str]] = []
    for node in graph._nodes.values():
        label = (node.label or "").lower()
        matched = sum(1 for tok in q_tokens if tok and tok in label)
        if matched == 0 and not (q and q in label):
            continue
        score = float(matched)
        if q and q in label:
            score += 2.0
        scored.append((score, node.id))
    scored.sort(reverse=True)
    return [(nid, score) for score, nid in scored[:limit]]
