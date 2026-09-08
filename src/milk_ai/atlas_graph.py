from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_graph(documents: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Constrói um grafo factual a partir dos documentos já ingeridos."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def node(node_id: str, kind: str, **properties: Any) -> None:
        nodes.setdefault(node_id, {"id": node_id, "tipo": kind, **properties})

    def edge(source: str, relation: str, target: str) -> None:
        edges.append({"origem": source, "relacao": relation, "destino": target})

    document_count = 0
    chunk_count = 0
    for document in documents:
        metadata = document.get("metadata", {})
        source_id = str(metadata.get("source_id", ""))
        if not source_id:
            continue
        document_count += 1
        source_node = f"source:{source_id}"
        node(
            source_node,
            "fonte",
            source_id=source_id,
            nome=metadata.get("original_name"),
            visibilidade=metadata.get("visibility"),
            estado_epistemico=metadata.get("epistemic_state"),
            direitos=metadata.get("rights_status"),
            consentimento=metadata.get("consent_status"),
            rgpd=metadata.get("rgpd_status"),
            validacao_humana=metadata.get("human_validated", False),
        )
        for path in document.get("provenance_paths", []):
            path_node = f"path:{path}"
            node(path_node, "proveniencia", caminho=path)
            edge(source_node, "tem_proveniencia", path_node)
        for chunk in document.get("chunks", []):
            chunk_count += 1
            chunk_id = str(chunk.get("chunk_id", ""))
            if not chunk_id:
                continue
            chunk_node = f"chunk:{chunk_id}"
            node(
                chunk_node,
                "chunk",
                chunk_id=chunk_id,
                ordinal=chunk.get("ordinal"),
                heading=chunk.get("heading"),
            )
            edge(source_node, "contém", chunk_node)
            chunk_metadata = chunk.get("metadata", {})
            for key in ("territory", "municipality", "parish", "original_name"):
                value = chunk_metadata.get(key)
                if value:
                    metadata_node = f"metadata:{key}:{value}"
                    node(metadata_node, "metadado", campo=key, valor=value)
                    edge(chunk_node, f"tem_{key}", metadata_node)

    return {
        "schema": "ia_milk.atlas_graph.v1",
        "generated_at": _now(),
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "documents": document_count,
            "chunks": chunk_count,
            "nodes": len(nodes),
            "edges": len(edges),
        },
    }
