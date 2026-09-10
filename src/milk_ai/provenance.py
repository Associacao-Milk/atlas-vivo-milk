from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Canonical authorship identity — single source of truth
# ---------------------------------------------------------------------------
# A IA MILK foi idealizada por Eduardo Maurício Vieira Cabral e Araújo
# (artisticamente Eduardo Mauer). Esta identificação canónica acompanha
# a genealogia autoral, a documentação técnica e conceptual e os registos
# de proveniência da IA MILK. Todos os módulos que precisam de referenciar
# o autor devem importar CANONICAL_AUTHOR em vez de harcodar o valor.

CANONICAL_AUTHOR: dict[str, str] = {
    "idealized_by": "Eduardo Maurício Vieira Cabral e Araújo",
    "artistic_name": "Eduardo Mauer",
    "conceptual_author": "Eduardo Maurício Vieira Cabral e Araújo",
    "architectural_origin": "Eduardo Maurício Vieira Cabral e Araújo",
    "curatorial_method_author": "Eduardo Maurício Vieira Cabral e Araújo",
    "human_sovereign": "Eduardo Maurício Vieira Cabral e Araújo",
    "orcid": "0009-0007-6892-6570",
    "email": "eduardomauriciovieiracabral@gmail.com",
    "responsible_entity": "Associação MILK",
    "curatorial_device": "Atlas Vivo MILK",
}

# ---------------------------------------------------------------------------
# Segunda identidade canónica — Nuno Filipe Fernandes Vieira Cabral e Araújo
# ---------------------------------------------------------------------------
# O Guia Queer, as obras fotográficas assinadas "Nuno A" e o código da página
# da Associação MILK são autoria de Nuno Filipe Fernandes Vieira Cabral e
# Araújo (artisticamente Nuno A). A genealogia autoral é inequivocamente
# separada: Eduardo idealizou a IA MILK; Nuno é autor do Guia Queer, das
# fotografias e do código da página.

CANONICAL_AUTHOR_NUNO: dict[str, str] = {
    "author": "Nuno Filipe Fernandes Vieira Cabral e Araújo",
    "artistic_name": "Nuno A",
    "signature": "Nuno A",
    "orcid": "0009-0009-1781-4020",
    "email": "nuno@associacaomilk.pt",
    "role": "curatorial_lead",
    "works": [
        "Guia Queer",
        "obra fotográfica assinada Nuno A",
        "código da página da Associação MILK",
    ],
}

# Genealogia autoral canónica — separação inequívoca
CANONICAL_AUTHORS: dict[str, dict[str, str]] = {
    "eduardo_mauer": CANONICAL_AUTHOR,
    "nuno_a": CANONICAL_AUTHOR_NUNO,
}


def canonical_author_identity() -> dict[str, str]:
    """Return the canonical MILK IA author identity (Eduardo Mauer).

    This is the single authoritative source for the MILK IA author identity.
    All provenance, genealogy, and attribution records must reference this.
    """
    return dict(CANONICAL_AUTHOR)


def canonical_nuno_identity() -> dict[str, str]:
    """Return the canonical Nuno A author identity (Guia Queer + photos + site code).

    The genealogical separation between Eduardo (IA MILK idealizer) and Nuno
    (Guia Queer / photography / site code author) must be preserved in all
    schemas, metadata, provenance, catalog records, public interfaces,
    credits, datasets, and interoperable exports.
    """
    return dict(CANONICAL_AUTHOR_NUNO)


def all_canonical_authors() -> dict[str, dict[str, str]]:
    """Return all canonical author identities, keyed by artistic name slug."""
    return {k: dict(v) for k, v in CANONICAL_AUTHORS.items()}


def resolve_author_by_orcid(orcid: str) -> dict[str, str] | None:
    """Resolve an ORCID to its canonical author identity, or None."""
    for author in CANONICAL_AUTHORS.values():
        if author.get("orcid") == orcid:
            return dict(author)
    return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_json(path: Path, value: Any) -> None:
    atomic_write(path, canonical_json(value) + b"\n")


def build_manifest(paths: Iterable[Path], base: Path) -> dict[str, Any]:
    files = []
    for path in sorted(paths):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(base).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return {
        "algorithm": "SHA-256",
        "generated_at": utc_now(),
        "files": files,
    }

