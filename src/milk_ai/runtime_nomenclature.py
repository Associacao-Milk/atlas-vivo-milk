"""MILK IA — Official Runtime Nomenclature.

Single source of truth for the canonical runtime terminology. The old term
"shadow" is DEPRECATED. New writes MUST use the terms defined here.

Official concepts:
    VALIDATION_RUNTIME   (:8767) — where the current revision is tested/certified
    CANONICAL_RUNTIME    (:8766) — untouched until explicit promotion

Historical logs/receipts/events are immutable. Old machine-readable fields are
still READ for compatibility via the alias readers in this module, but every
NEW write emits only the new terminology.

This module is the *explicit* compatibility/migration registry referenced by
the ACTIVE_LEGACY_TERMS acceptance criterion.
"""
from __future__ import annotations

from typing import Any, Mapping

# ---------------------------------------------------------------------------
# Official runtime identities
# ---------------------------------------------------------------------------

VALIDATION_RUNTIME = "validation"
CANONICAL_RUNTIME = "canonical"

VALIDATION_RUNTIME_PORT = 8767
CANONICAL_RUNTIME_PORT = 8766

# Official schema / host identifiers (new writes only)
VALIDATION_SCHEMA = "ia_milk.validation.v1"
VALIDATION_HOST = "MILK-validation"
CANONICAL_SCHEMA = "ia_milk.canonical.v1"
CANONICAL_HOST = "MILK-canonical"

# Role -> schema/host mapping
ROLE_SCHEMA = {
    "validation": VALIDATION_SCHEMA,
    "canonical": CANONICAL_SCHEMA,
}
ROLE_HOST = {
    "validation": VALIDATION_HOST,
    "canonical": CANONICAL_HOST,
}

# Promotion lifecycle states
PROMOTION_REQUIRED = "promotion_required"
PROMOTION_READY = "promotion_ready"
PROMOTION_BLOCKED = "promotion_blocked"

# Official health / head-match field names (new writes)
VALIDATION_RUNTIME_REVISION = "validation_runtime_revision"
VALIDATION_RUNTIME_HEALTH = "validation_runtime_health"
VALIDATION_RUNTIME_HEAD_MATCH = "validation_runtime_head_match"
VALIDATION_POLICY_CONTAMINATION = "validation_policy_contamination"

# ---------------------------------------------------------------------------
# Official environment values (learning provenance firewall)
# ---------------------------------------------------------------------------

ENVIRONMENTS = (
    "production",
    "validation",
    "test",
    "simulation",
    "curatorial_experiment",
    "legacy_unknown",
)

# Only these environments may alter the canonical (production) AdaptivePolicy.
POLICY_MUTATING_ENVIRONMENTS = ("production", "curatorial_experiment")

# runtime_role values recorded in ResearchTrace
RUNTIME_ROLES = (
    "validation",
    "canonical",
    "test",
    "simulation",
    "curatorial_experiment",
)

# ---------------------------------------------------------------------------
# Legacy -> new terminology map
# ---------------------------------------------------------------------------
# This registry documents the deprecated terms that are READ for backward
# compatibility. No active API should EMIT these; readers below accept them
# transparently when parsing historical receipts.

LEGACY_TERM_ALIASES: dict[str, str] = {
    "shadow_revision": VALIDATION_RUNTIME_REVISION,
    "shadow_health": VALIDATION_RUNTIME_HEALTH,
    "shadow_head_match": VALIDATION_RUNTIME_HEAD_MATCH,
    "shadow_policy_contamination": VALIDATION_POLICY_CONTAMINATION,
    "shadow_match": VALIDATION_RUNTIME_HEAD_MATCH,
}

LEGACY_SCHEMA_ALIASES: dict[str, str] = {
    "ia_milk.shadow.v1": VALIDATION_SCHEMA,
}

LEGACY_HOST_ALIASES: dict[str, str] = {
    "MILK-shadow": VALIDATION_HOST,
}

LEGACY_ENVIRONMENT_ALIASES: dict[str, str] = {
    "shadow": "validation",
}


def normalize_environment(value: str | None) -> str:
    """Map a possibly-legacy environment label to an official environment value.

    Unknown/None values become ``legacy_unknown`` so historical events are never
    silently re-classified as production.
    """
    if not value:
        return "legacy_unknown"
    v = str(value).strip().lower()
    if v in LEGACY_ENVIRONMENT_ALIASES:
        return LEGACY_ENVIRONMENT_ALIASES[v]
    if v in ENVIRONMENTS:
        return v
    return "legacy_unknown"


def environment_can_mutate_policy(environment: str) -> bool:
    """True only for production or human-approved curatorial_experiment."""
    return normalize_environment(environment) in POLICY_MUTATING_ENVIRONMENTS


# ---------------------------------------------------------------------------
# Compatibility readers — accept legacy field names when reading historical
# machine-readable receipts, prefer the new name on new data.
# ---------------------------------------------------------------------------

def read_field(data: Mapping[str, Any], canonical_name: str, default: Any = None) -> Any:
    """Read a field by its canonical name, falling back to any legacy alias.

    Used to parse historical receipts (milk_production_readiness.json etc.)
    that still carry the deprecated ``shadow_*`` field names.
    """
    if canonical_name in data:
        return data[canonical_name]
    for legacy, new in LEGACY_TERM_ALIASES.items():
        if new == canonical_name and legacy in data:
            return data[legacy]
    return default


def read_validation_revision(data: Mapping[str, Any], default: Any = None) -> Any:
    return read_field(data, VALIDATION_RUNTIME_REVISION, default)


def read_validation_health(data: Mapping[str, Any], default: Any = None) -> Any:
    return read_field(data, VALIDATION_RUNTIME_HEALTH, default)


def read_validation_head_match(data: Mapping[str, Any], default: Any = None) -> Any:
    return read_field(data, VALIDATION_RUNTIME_HEAD_MATCH, default)


def normalize_schema(schema: str | None) -> str | None:
    if not schema:
        return schema
    return LEGACY_SCHEMA_ALIASES.get(schema, schema)


def normalize_host(host: str | None) -> str | None:
    if not host:
        return host
    return LEGACY_HOST_ALIASES.get(host, host)


def active_legacy_terms_in_text(text: str) -> list[str]:
    """Return the list of deprecated MILK legacy terms found in *text*.

    Only MILK-specific deprecated terms are flagged (not generic words like
    "shadow" appearing in third-party CSS/PyTorch). Used by the migration
    certification check.
    """
    hits: list[str] = []
    needles = (
        "shadow_revision", "shadow_health", "shadow_head_match",
        "shadow_policy_contamination", "shadow_match",
        'schema="ia_milk.shadow.v1"', "ia_milk.shadow.v1",
        'host="MILK-shadow"', "MILK-shadow",
        'environment="shadow"',
        "ShadowHandler", "SHADOW_START", "SHADOW_STOPPED",
        "shadow_runtime_revision",
    )
    low = text
    for n in needles:
        if n in low:
            hits.append(n)
    return hits
