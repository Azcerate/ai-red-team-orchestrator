"""Runner protocol."""
from __future__ import annotations

from typing import Protocol

from ..core.models import PromptItem, TestResult


class Runner(Protocol):
    def run(self, item: PromptItem) -> TestResult:
        """Send one prompt to the target and return a populated TestResult
        (response_text, http_status, latency_ms, error). Detection fields are
        left None for the judge stage."""
        ...
