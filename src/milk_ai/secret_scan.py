from __future__ import annotations

import hashlib
import math
import re
from dataclasses import asdict, dataclass


SECRET_NAME = r"[A-Z][A-Z0-9_]*(?:API_KEY|APP_PASSWORD|PASSWORD|PRIVATE_KEY|CLIENT_SECRET|ACCESS_TOKEN|AUTH_TOKEN|TOKEN|SECRET)[A-Z0-9_]*"
NAMED_LITERAL = re.compile(
    rf"(?P<prefix>\b(?P<name>{SECRET_NAME})\b[\s`\"'|]*[:=|][\s`\"'|]*)"
    r"(?P<value>[A-Za-z0-9_!%+./:@#\-$^&*]{12,})",
    flags=re.MULTILINE,
)
PRIVATE_KEY = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    flags=re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class SecretFinding:
    kind: str
    name: str
    line: int
    fingerprint: str
    start: int
    end: int

    def public_dict(self) -> dict:
        value = asdict(self)
        value.pop("start")
        value.pop("end")
        return value


def _entropy(value: str) -> float:
    frequencies = {char: value.count(char) / len(value) for char in set(value)}
    return -sum(probability * math.log2(probability) for probability in frequencies.values())


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def scan_secrets(text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for match in NAMED_LITERAL.finditer(text):
        value = match.group("value")
        lowered = value.casefold()
        if lowered.startswith(("http://", "https://", "os.environ", "none", "null", "redacted")):
            continue
        if _entropy(value) < 2.8 and len(value) < 24:
            continue
        findings.append(
            SecretFinding(
                kind="named_literal",
                name=match.group("name"),
                line=text.count("\n", 0, match.start("value")) + 1,
                fingerprint=_fingerprint(value),
                start=match.start("value"),
                end=match.end("value"),
            )
        )
    for match in PRIVATE_KEY.finditer(text):
        findings.append(
            SecretFinding(
                kind="private_key",
                name="PRIVATE_KEY_BLOCK",
                line=text.count("\n", 0, match.start()) + 1,
                fingerprint=_fingerprint(match.group(0)),
                start=match.start(),
                end=match.end(),
            )
        )
    unique: dict[tuple[int, int], SecretFinding] = {(f.start, f.end): f for f in findings}
    return sorted(unique.values(), key=lambda item: item.start)


def redact_secrets(text: str, findings: list[SecretFinding] | None = None) -> str:
    findings = findings if findings is not None else scan_secrets(text)
    redacted = text
    for finding in sorted(findings, key=lambda item: item.start, reverse=True):
        replacement = f"[SEGREDO_OCULTO:{finding.fingerprint}]"
        redacted = redacted[:finding.start] + replacement + redacted[finding.end:]
    return redacted

