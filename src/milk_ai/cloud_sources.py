from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, Mapping


CLOUD_DIRECTORY = re.compile(
    r"^(?:google drive|my drive|meu drive|o meu disco|shared drives|"
    r"drives partilhados|nextcloud|nextcloud docs)$",
    flags=re.IGNORECASE,
)


def _existing_directory(path: Path) -> Path | None:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return None
    return resolved if resolved.is_dir() else None


def _filesystem_roots() -> list[Path]:
    if os.name != "nt":
        return [Path("/")]
    roots: list[Path] = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        candidate = Path(f"{letter}:\\")
        try:
            if candidate.is_dir():
                roots.append(candidate)
        except OSError:
            continue
    return roots


def discover_cloud_sources(
    *,
    home: Path | None = None,
    environment: Mapping[str, str] | None = None,
    filesystem_roots: Iterable[Path] | None = None,
) -> list[Path]:
    """Descobre origens locais/sincronizadas sem contactar serviços externos."""
    env = dict(os.environ if environment is None else environment)
    user_home = (home or Path.home()).expanduser()
    raw: list[Path] = [user_home / "milk_ai"]

    for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if env.get(key):
            raw.append(Path(env[key]))
    raw.append(user_home / "OneDrive")

    for key in ("GOOGLE_DRIVE", "GOOGLE_DRIVE_ROOT", "NEXTCLOUD", "NEXTCLOUD_ROOT"):
        if env.get(key):
            raw.append(Path(env[key]))
    raw.extend((user_home / "Google Drive", user_home / "Nextcloud"))

    scan_roots = list(filesystem_roots) if filesystem_roots is not None else _filesystem_roots()
    for root in scan_roots:
        try:
            for child in root.iterdir():
                if child.is_dir() and CLOUD_DIRECTORY.fullmatch(child.name):
                    raw.append(child)
        except OSError:
            continue

    existing: list[Path] = []
    seen: set[str] = set()
    for candidate in raw:
        resolved = _existing_directory(candidate)
        if resolved is None:
            continue
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            existing.append(resolved)

    # Uma raiz superior já inclui as pastas sincronizadas que estejam dentro dela.
    compact: list[Path] = []
    for candidate in sorted(existing, key=lambda item: (len(item.parts), str(item).casefold())):
        if any(_is_within(candidate, parent) for parent in compact):
            continue
        compact.append(candidate)
    return compact


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False
