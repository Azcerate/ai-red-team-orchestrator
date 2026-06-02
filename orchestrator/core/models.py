"""Canonical data models for airt.

These dataclasses are the single source of truth that every stage
(runner -> judge -> scoring -> mapping -> reporting -> gate) reads and writes.
Pure stdlib so the package imports with no third-party deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# Judge label vocabulary (normalized from the real qwen3 judge output)
JUDGE_LABELS = {"success", "partial", "fail", "error", "skipped"}
SEVERITIES = ["critical", "high", "medium", "low", "info"]
REVIEW_STATES = {"auto", "needs_review", "confirmed", "dismissed"}


@dataclass
class PromptItem:
    """One row from a corpus CSV (real schema: id, technique, prompt).

    `category` is derived from the campaign file mapping, NOT the row.
    `attack_type` is the `technique` column. For canary/RAG categories the
    `technique` value is also the phrase to detect, captured in `phrase_target`.
    """
    prompt_id: str
    prompt: str
    category: str
    attack_type: str = ""
    phrase_target: str | None = None
    source_file: str = ""


@dataclass
class TestResult:
    """One executed + judged + scored test case."""
    # identity / lineage
    result_id: str
    run_id: str
    campaign_id: str
    timestamp: str

    # attack definition
    prompt_id: str
    prompt: str
    category: str
    attack_type: str = ""
    phrase_target: str | None = None

    # target / request metadata
    target_id: str = ""
    request_meta: dict[str, Any] = field(default_factory=dict)

    # response
    response_text: str | None = None
    http_status: int | None = None
    latency_ms: int | None = None
    conversation_id: str | None = None
    error: str | None = None

    # detection signals
    phrase_check: bool | None = None          # deterministic canary/phrase hit
    judge_label: str | None = None            # success|partial|fail|error|skipped
    judge_confidence: float | None = None     # normalized 0.0-1.0
    judge_reasons: list[str] = field(default_factory=list)

    # derived (filled by scoring / mapping)
    success: bool | None = None
    severity: str | None = None
    framework_refs: list[dict] = field(default_factory=list)
    evidence_id: str | None = None
    review_status: str = "auto"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    """A reported finding: a cluster of results for one category/issue."""
    id: str                       # e.g. AIRT-TMC-RAG-007
    title: str
    category: str
    severity: str
    asr_success: int = 0
    asr_total: int = 0
    asr_errored: int = 0
    mean_confidence: float | None = None
    review_status: str = "auto"
    framework_refs: list[dict] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    business_impact: str = ""
    remediation: str = ""
    sample_prompt: str = ""
    sample_response: str = ""

    @property
    def asr(self) -> float:
        denom = self.asr_total - self.asr_errored
        return (self.asr_success / denom) if denom > 0 else 0.0


@dataclass
class GateViolation:
    rule: str
    metric: str
    expected: str
    actual: Any
    severity: str = "fail"   # fail | warn


@dataclass
class GateResult:
    passed: bool
    run_id: str
    violations: list[GateViolation] = field(default_factory=list)
    warnings: list[GateViolation] = field(default_factory=list)
