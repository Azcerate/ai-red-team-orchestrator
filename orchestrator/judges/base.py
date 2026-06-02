"""Judge protocol + normalized judgement type."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..core.models import TestResult


@dataclass
class Judgement:
    label: str                       # success|partial|fail|error|skipped
    confidence: float                # normalized 0.0-1.0
    reasons: list[str] = field(default_factory=list)


class Judge(Protocol):
    def judge(self, result: TestResult) -> Judgement:
        ...
