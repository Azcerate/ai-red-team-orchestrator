"""Import legacy prompt_tester/injection_judge result CSVs into TestResult.

This turns your existing ~1,100 rows across 14 result files into report data
immediately, with no new test runs. Category is inferred from the filename
(override with the `category` arg).
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..core.ids import result_id, now_iso
from ..core.models import TestResult

# filename keyword -> category
FILENAME_CATEGORY = [
    ("canary", "canary_leakage"),
    ("fishing", "rag_fishing"),
    ("rag_leakage_auth", "idor_rbac"),
    ("rag", "rag_fishing"),
    ("jailbreak", "jailbreak"),
    ("narrative", "jailbreak"),
    ("obfuscation", "prompt_injection"),
    ("injection", "prompt_injection"),
    ("harmful_prompt_injections", "prompt_injection"),
    ("harmful", "unsafe_output"),
    ("offtopic", "offtopic_abuse"),
    ("long_context", "context_overflow"),
    ("context", "context_overflow"),
    ("probe", "rate_limit_weakness"),
]

_LABEL_MAP = {
    "SUCCESS": "success", "POSSIBLE": "partial", "NO_SUCCESS": "fail",
    "ERROR": "error", "SKIP": "skipped", "UNKNOWN": "error",
}


def infer_category(filename: str) -> str:
    name = filename.lower()
    for key, cat in FILENAME_CATEGORY:
        if key in name:
            return cat
    return "uncategorized"


def _phrase_to_bool(value: str | None) -> bool | None:
    if not value:
        return None
    v = value.strip().upper()
    if v == "SUCCESS":
        return True
    if v == "NO_SUCCESS":
        return False
    return None


def import_legacy_csv(path: str | Path, run_id: str, campaign_id: str,
                      category: str | None = None) -> list[TestResult]:
    p = Path(path)
    category = category or infer_category(p.name)
    results: list[TestResult] = []
    with p.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            resp = row.get("response") or row.get("response_text") or ""
            is_error = resp.startswith("ERROR:")
            conf_raw = row.get("injection_confidence")
            try:
                conf = (float(conf_raw) / 100.0) if conf_raw not in (None, "") else None
            except ValueError:
                conf = None
            label = _LABEL_MAP.get((row.get("injection_label") or "").strip().upper())
            reasons_raw = row.get("injection_reasons") or ""
            reasons = [r.strip() for r in reasons_raw.split("|") if r.strip()]
            phrase = _phrase_to_bool(row.get("phrase_check"))
            try:
                latency = int(float(row["response_time_ms"])) if row.get("response_time_ms") else None
            except (ValueError, KeyError):
                latency = None
            try:
                status = int(row["status_code"]) if row.get("status_code") else None
            except ValueError:
                status = None
            results.append(TestResult(
                result_id=result_id(),
                run_id=run_id,
                campaign_id=campaign_id,
                timestamp=row.get("timestamp") or now_iso(),
                prompt_id=f"{category}:{row.get('id', '')}",
                prompt=row.get("prompt", ""),
                category=category,
                attack_type=row.get("technique", ""),
                response_text=None if is_error else resp,
                http_status=status,
                latency_ms=latency,
                error=resp if is_error else None,
                phrase_check=phrase,
                judge_label=label,
                judge_confidence=conf,
                judge_reasons=reasons,
            ))
    return results
