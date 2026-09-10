"""MILK IA — Sovereign Hypergraph Research Consciousness.

Permanent relational, multimodal, multisensory, adaptive intelligence
system. Knowledge is a living network of relations, not passive storage.

This module implements the HYPERGRAPH MEMORY LAYER — a lightweight overlay
over existing MILK infrastructure (Control Plane, Adaptive Policy, Evidence
Fabric, Gap Engine, Vector Index, Conceptual Engine). No duplication of
content; relations only.

Core principles:
  - RESEARCH BEFORE REASONING: reasoning without research is forbidden
  - ACTIVE_REFERENCE: observed + validated + retrievable + traceable → active
  - MULTIMODAL: text, image, sound, body, territory, code as first-class
  - MULTISENSORY: visual, auditory, spatial, temporal, movement patterns
  - AESTHETIC: retrieval by aesthetic affinity, not just topic
  - CONTRADICTION PRESERVATION: never merge conflicting sources
  - RESEARCH GAPS: when evidence is insufficient, create searchable gaps
  - TOKEN EFFICIENCY: reference capsules, not full corpus loading
  - AUTHORSHIP IMMUTABILITY: Eduardo Mauer and Nuno A are sacred, distinct

Reuses: conceptual_engine, gap_engine, cognitive_control_plane, adaptive_engine,
provenance, evidence_bundles, retrieval, ontology, export_ngsi.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Hypergraph node and edge types (from directive)
# ---------------------------------------------------------------------------

NODE_TYPES = (
    "AUTHOR", "PERSON", "COLLECTIVE", "WORK", "PROJECT", "DOCUMENT", "TEXT",
    "BOOK", "ARTICLE", "PHOTO", "IMAGE", "VIDEO", "VOICE", "SOUND", "MUSIC",
    "OBJECT", "ARTIFACT", "BODY", "GESTURE", "PERFORMANCE", "INSTALLATION",
    "EVENT", "PLACE", "TERRITORY", "ROUTE", "TOPONYM", "METHOD", "DEVICE",
    "TOOL", "PROCESS", "QUESTION", "MEMORY", "EPISODE", "PATTERN", "OUTCOME",
    "DECISION", "INSIGHT", "CONCEPT", "THEORY", "EMOTION", "ATMOSPHERE",
    "AESTHETIC", "SENSATION", "EVIDENCE", "RESEARCH_GAP",
)

EDGE_TYPES = (
    "AUTHORED_BY", "LOCATED_IN", "PART_OF", "INSPIRED_BY", "INFLUENCED_BY",
    "DERIVED_FROM", "APPLIED_IN", "SUPPORTS", "CONTRADICTS", "EXPANDS",
    "EXTENDS", "REFINES", "VALIDATED_BY", "QUESTIONED_BY", "OBSERVED_IN",
    "RELATED_TO", "ANALOGOUS_TO", "ECHOES", "RESONATES_WITH", "SIMILAR_TO",
    "CO_OCCURS", "TEMPORALLY_LINKED", "HISTORICALLY_LINKED",
    "AESTHETICALLY_LINKED", "TERRITORIALLY_LINKED", "METHODOLOGICALLY_LINKED",
    "CURATORIALLY_LINKED", "SENSORIALLY_LINKED", "EMOTIONALLY_LINKED",
    "SUCCESSFUL_FOR", "FAILED_FOR", "DISCOVERED_THROUGH",
)

MULTIMODAL_TYPES = (
    "TEXT", "IMAGE", "PHOTOGRAPH", "DRAWING", "VIDEO", "VOICE", "SPEECH",
    "AUDIO", "SOUNDSCAPE", "MUSIC", "PERFORMANCE", "MOVEMENT", "GESTURE",
    "BODY", "OBJECT", "PLACE", "MAP", "TOPOGRAPHY", "TOPONYMY", "EVENT",
    "ORAL_HISTORY", "MEMORY", "ARCHIVE", "CURATORIAL_ACTION",
)

MULTISENSORY_DIMENSIONS = (
    "VISUAL_PATTERNS", "AUDITORY_PATTERNS", "SPATIAL_PATTERNS",
    "TEMPORAL_PATTERNS", "MOVEMENT_PATTERNS", "TACTILE_REFERENCES",
    "RHYTHMIC_STRUCTURES", "REPETITION", "ABSENCE", "SILENCE",
    "ATMOSPHERE", "AFFECT", "MOOD", "DENSITY", "CHAOS", "ORDER",
    "SURPRISE", "RUPTURE", "PARTICIPATION",
)

AESTHETIC_DIMENSIONS = (
    "RHYTHM", "FLOW", "TEXTURE", "TENSION", "SILENCE", "NOISE",
    "HUMOR", "IRONY", "STRANGENESS", "ABSURDITY", "PARTICIPATION",
    "EMERGENCE", "UNCERTAINTY", "PLAY", "SURPRISE",
    "COLLECTIVE_EXPERIENCE", "ATMOSPHERE", "MATERIALITY",
    "PRESENCE", "ABSENCE",
)

TEMPORAL_STATES = ("PAST", "PRESENT", "POSSIBLE_FUTURE")

VALIDATION_STATES = ("pending", "validated", "rejected", "speculative")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return hashlib.sha256(f"{_now()}{time.time_ns()}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Hypergraph node — lightweight relation pointer (no content duplication)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class HyperNode:
    """A node in the hypergraph. Stores metadata + relation pointers only."""
    id: str
    type: str
    label: str = ""
    modality: str = "text"
    source_pointer: str = ""        # URI/hash to original content (never copied)
    evidence_pointer: str = ""      # EvidenceBundle ID if applicable
    provenance: str = ""             # PROV-O activity URI
    validation_state: str = "pending"
    confidence: float = 0.0
    temporal_state: str = "present"
    created_at: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.type not in NODE_TYPES:
            raise ValueError(f"invalid node type: {self.type}")
        if self.validation_state not in VALIDATION_STATES:
            raise ValueError(f"invalid validation_state: {self.validation_state}")
        if self.temporal_state not in ("past", "present", "possible_future"):
            raise ValueError(f"invalid temporal_state: {self.temporal_state}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "label": self.label,
            "modality": self.modality, "source_pointer": self.source_pointer,
            "evidence_pointer": self.evidence_pointer,
            "provenance": self.provenance,
            "validation_state": self.validation_state,
            "confidence": self.confidence,
            "temporal_state": self.temporal_state,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Hypergraph edge — first-class object with full metadata
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class HyperEdge:
    """An edge in the hypergraph. Edges are first-class objects."""
    id: str
    source: str
    edge_type: str
    target: str
    confidence: float = 0.0
    provenance: str = ""
    timestamp: str = field(default_factory=_now)
    source_ref: str = ""             # what produced this edge
    evidence: str = ""               # evidence bundle pointer
    validation_state: str = "pending"
    outcome_score: float = 0.0       # for SUCCESSFUL_FOR / FAILED_FOR edges
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.edge_type not in EDGE_TYPES:
            raise ValueError(f"invalid edge type: {self.edge_type}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "source": self.source, "type": self.edge_type,
            "target": self.target, "confidence": self.confidence,
            "provenance": self.provenance, "timestamp": self.timestamp,
            "source_ref": self.source_ref, "evidence": self.evidence,
            "validation_state": self.validation_state,
            "outcome_score": self.outcome_score,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Reference Capsule — token-efficient knowledge transport
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ReferenceCapsule:
    """Compact reference for token-efficient worker context.

    Contains only pointers and key relations — never full content.
    Full sources are loaded only on demand.
    """
    id: str
    node_type: str
    label: str
    confidence: float
    relevance: float
    modality: str
    methods: list[str] = field(default_factory=list)
    key_relations: list[str] = field(default_factory=list)
    source_pointer: str = ""
    evidence_pointer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "type": self.node_type, "label": self.label,
            "confidence": self.confidence, "relevance": self.relevance,
            "modality": self.modality, "methods": self.methods,
            "key_relations": self.key_relations,
            "source_pointer": self.source_pointer,
            "evidence_pointer": self.evidence_pointer,
        }


# ---------------------------------------------------------------------------
# Research Gap — searchable knowledge absence
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ResearchGap:
    """A research gap — when evidence is insufficient, do not hallucinate."""
    id: str
    question: str
    missing_evidence: list[str] = field(default_factory=list)
    searched_paths: list[str] = field(default_factory=list)
    consulted_references: list[str] = field(default_factory=list)
    confidence: float = 0.0
    territory: str = ""
    possible_next_steps: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "question": self.question,
            "missing_evidence": self.missing_evidence,
            "searched_paths": self.searched_paths,
            "consulted_references": self.consulted_references,
            "confidence": self.confidence,
            "territory": self.territory,
            "possible_next_steps": self.possible_next_steps,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Discovery Path — serendipity, analogy, curatorial exploration
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DiscoveryPath:
    """A path through the hypergraph for meaningful discovery."""
    id: str
    path_type: str  # serendipity, analogy, curatorial, exploratory
    nodes: list[str] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)
    description: str = ""
    surprise_score: float = 0.0
    novelty_score: float = 0.0
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "path_type": self.path_type,
            "nodes": self.nodes, "edges": self.edges,
            "description": self.description,
            "surprise_score": self.surprise_score,
            "novelty_score": self.novelty_score,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Sovereign Hypergraph — the living memory layer
# ---------------------------------------------------------------------------

class SovereignHypergraph:
    """Permanent relational memory — lightweight hypergraph overlay.

    Stores relations only. Never duplicates content. Reuses existing
    MILK infrastructure for retrieval, evidence, and provenance.
    """

    def __init__(self):
        self._nodes: dict[str, HyperNode] = {}
        self._edges: dict[str, HyperEdge] = {}
        self._capsules: list[ReferenceCapsule] = []
        self._gaps: dict[str, ResearchGap] = {}
        self._paths: list[DiscoveryPath] = []
        self._contradictions: list[dict[str, Any]] = []
        self._outcome_edges: list[HyperEdge] = []
        self._temporal_links: list[dict[str, Any]] = []

    # --- Node operations ---

    def add_node(self, node: HyperNode) -> None:
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> HyperNode | None:
        return self._nodes.get(node_id)

    def nodes_by_type(self, node_type: str) -> list[HyperNode]:
        return [n for n in self._nodes.values() if n.type == node_type]

    def nodes_by_modality(self, modality: str) -> list[HyperNode]:
        return [n for n in self._nodes.values() if n.modality == modality]

    # --- Edge operations ---

    def add_edge(self, edge: HyperEdge) -> None:
        self._edges[edge.id] = edge
        if edge.edge_type in ("SUCCESSFUL_FOR", "FAILED_FOR"):
            self._outcome_edges.append(edge)

    def edges_by_type(self, edge_type: str) -> list[HyperEdge]:
        return [e for e in self._edges.values() if e.edge_type == edge_type]

    def edges_from(self, node_id: str) -> list[HyperEdge]:
        return [e for e in self._edges.values() if e.source == node_id]

    def edges_to(self, node_id: str) -> list[HyperEdge]:
        return [e for e in self._edges.values() if e.target == node_id]

    def neighbors(self, node_id: str) -> list[tuple[HyperEdge, HyperNode]]:
        result = []
        for e in self._edges.values():
            if e.source == node_id and e.target in self._nodes:
                result.append((e, self._nodes[e.target]))
            elif e.target == node_id and e.source in self._nodes:
                result.append((e, self._nodes[e.source]))
        return result

    # --- Graph traversal ---

    def traverse(self, source: str, max_depth: int = 3) -> dict[str, list[str]]:
        """BFS traversal from source node. Returns adjacency map."""
        visited: dict[str, list[str]] = {}
        queue: list[tuple[str, int]] = [(source, 0)]
        while queue:
            current, depth = queue.pop(0)
            if depth > max_depth:
                continue
            if current in visited:
                continue
            neighbors = []
            for e in self._edges.values():
                if e.source == current and e.target not in visited:
                    neighbors.append(e.target)
                    queue.append((e.target, depth + 1))
                elif e.target == current and e.source not in visited:
                    neighbors.append(e.source)
                    queue.append((e.source, depth + 1))
            visited[current] = neighbors
        return visited

    def path_between(self, source: str, target: str, max_depth: int = 4) -> list[list[str]]:
        """Find all paths between two nodes."""
        if source not in self._nodes or target not in self._nodes:
            return []
        paths: list[list[str]] = []
        queue: list[tuple[str, list[str]]] = [(source, [source])]
        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            if current == target and len(path) > 1:
                paths.append(path)
                continue
            for e in self._edges.values():
                nxt = None
                if e.source == current and e.target not in path:
                    nxt = e.target
                elif e.target == current and e.source not in path:
                    nxt = e.source
                if nxt:
                    queue.append((nxt, path + [nxt]))
        return paths[:20]

    # --- Reference capsules ---

    def create_capsule(self, node_id: str, relevance: float = 1.0) -> ReferenceCapsule | None:
        node = self._nodes.get(node_id)
        if not node:
            return None
        relations = [e.target for e in self.edges_from(node_id)] + \
                     [e.source for e in self.edges_to(node_id)]
        capsule = ReferenceCapsule(
            id=node.id, node_type=node.type, label=node.label,
            confidence=node.confidence, relevance=relevance,
            modality=node.modality,
            key_relations=list(set(relations))[:10],
            source_pointer=node.source_pointer,
            evidence_pointer=node.evidence_pointer,
        )
        self._capsules.append(capsule)
        return capsule

    def capsules_for_context(self, node_ids: list[str], max_capsules: int = 20) -> list[ReferenceCapsule]:
        """Generate token-efficient capsules for worker context."""
        capsules = []
        for nid in node_ids:
            c = self.create_capsule(nid)
            if c:
                capsules.append(c)
            if len(capsules) >= max_capsules:
                break
        return capsules

    # --- Research gaps ---

    def create_gap(self, question: str, missing_evidence: list[str] | None = None,
                    territory: str = "", confidence: float = 0.0) -> ResearchGap:
        gap = ResearchGap(
            id=f"gap:{_uuid()}", question=question,
            missing_evidence=missing_evidence or [],
            territory=territory, confidence=confidence,
        )
        self._gaps[gap.id] = gap
        return gap

    def search_gaps(self, query: str) -> list[ResearchGap]:
        """Searchable research gaps."""
        q = query.lower()
        return [g for g in self._gaps.values()
                if q in g.question.lower() or q in g.territory.lower()]

    # --- Discovery paths ---

    def create_path(self, path_type: str, nodes: list[str], description: str = "",
                    surprise: float = 0.0, novelty: float = 0.0) -> DiscoveryPath:
        path = DiscoveryPath(
            id=f"path:{_uuid()}", path_type=path_type,
            nodes=nodes, description=description,
            surprise_score=surprise, novelty_score=novelty,
        )
        self._paths.append(path)
        return path

    # --- Contradiction preservation ---

    def register_contradiction(self, node_a: str, node_b: str, evidence_a: str = "",
                                evidence_b: str = "", description: str = "") -> None:
        """Preserve contradictions. Never merge into false consensus."""
        self._contradictions.append({
            "id": f"contradiction:{_uuid()}",
            "node_a": node_a, "node_b": node_b,
            "evidence_a": evidence_a, "evidence_b": evidence_b,
            "description": description,
            "timestamp": _now(),
        })

    # --- Temporal links ---

    def link_temporal(self, node_id: str, temporal_state: str, description: str = "") -> None:
        self._temporal_links.append({
            "node": node_id, "temporal_state": temporal_state,
            "description": description, "timestamp": _now(),
        })

    # --- Outcome learning ---

    def record_outcome(self, method_id: str, task_type: str, success: bool,
                       confidence: float = 0.0, score: float = 0.0) -> None:
        """Record outcome edge for adaptive learning."""
        edge_type = "SUCCESSFUL_FOR" if success else "FAILED_FOR"
        edge = HyperEdge(
            id=f"outcome:{_uuid()}", source=method_id,
            edge_type=edge_type, target=task_type,
            confidence=confidence, outcome_score=score,
            validation_state="validated",
        )
        self.add_edge(edge)
        self._outcome_edges.append(edge)

    # --- Aesthetic reference engine ---

    def aesthetic_neighbors(self, node_id: str, dimension: str = "") -> list[HyperNode]:
        """Find nodes linked by aesthetic affinity."""
        aesthetic_edges = ["AESTHETICALLY_LINKED", "RESONATES_WITH",
                          "ECHOES", "ANALOGOUS_TO", "SIMILAR_TO",
                          "SENSORIALLY_LINKED", "EMOTIONALLY_LINKED"]
        result = []
        for e in self._edges.values():
            if e.edge_type not in aesthetic_edges:
                continue
            if dimension and dimension.lower() not in str(e.metadata).lower():
                continue
            other = e.target if e.source == node_id else (e.source if e.target == node_id else None)
            if other and other in self._nodes:
                result.append(self._nodes[other])
        return result

    # --- Multimodal retrieval ---

    def multimodal_neighbors(self, node_id: str) -> dict[str, list[HyperNode]]:
        """Return neighbors grouped by modality."""
        groups: dict[str, list[HyperNode]] = {}
        for edge, node in self.neighbors(node_id):
            mod = node.modality
            groups.setdefault(mod, []).append(node)
        return groups

    # --- Stats ---

    def stats(self) -> dict[str, Any]:
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "capsules": len(self._capsules),
            "research_gaps": len(self._gaps),
            "discovery_paths": len(self._paths),
            "contradictions_preserved": len(self._contradictions),
            "outcome_edges": len(self._outcome_edges),
            "temporal_links": len(self._temporal_links),
            "node_types": len(set(n.type for n in self._nodes.values())),
            "edge_types": len(set(e.edge_type for e in self._edges.values())),
            "modalities": len(set(n.modality for n in self._nodes.values())),
        }

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)
