"""Redaction of sensitive data before evidence is persisted/reported."""
from __future__ import annotations

import re

from ..corpus.loader import KNOWN_CANARIES

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9]{16,}"), "[REDACTED_KEY]"),
]


def redact(text: str | None, extra_canaries: list[str] | None = None) -> str:
    if not text:
        return ""
    out = text
    for token in list(KNOWN_CANARIES) + list(extra_canaries or []):
        if token:
            out = out.replace(token, "[REDACTED_CANARY]")
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
