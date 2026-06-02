"""Evidence capture. Redacts by default; raw retained only on explicit opt-in."""
from __future__ import annotations

import json
from pathlib import Path

from ..core.ids import evidence_id
from ..core.models import TestResult
from .redact import redact


def attach_evidence(r: TestResult, run_id: str, redact_enabled: bool = True,
                    extra_canaries: list[str] | None = None,
                    evidence_dir: str = "results", max_chars: int = 600) -> TestResult:
    r.evidence_id = evidence_id(r.result_id)
    prompt = r.prompt[:max_chars]
    response = (r.response_text or "")[:max_chars]
    if redact_enabled:
        prompt = redact(prompt, extra_canaries)
        response = redact(response, extra_canaries)
    blob = {
        "evidence_id": r.evidence_id, "result_id": r.result_id,
        "category": r.category, "attack_type": r.attack_type,
        "prompt": prompt, "response": response,
        "http_status": r.http_status, "latency_ms": r.latency_ms,
    }
    path = Path(evidence_dir) / f"{run_id}.evidence.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(blob, ensure_ascii=False) + "\n")
    return r
