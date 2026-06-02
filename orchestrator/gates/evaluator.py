"""Regression gate: compare a run's metrics to a baseline + thresholds."""
from __future__ import annotations

import json
from pathlib import Path

from ..core.models import GateResult, GateViolation, TestResult
from ..scoring.aggregate import build_findings, category_asr, overall_asr, severity_counts


def metrics_for(results: list[TestResult], campaign_id: str) -> dict:
    findings = build_findings(results, campaign_id)
    return {
        "asr": {"overall": overall_asr(results), **category_asr(results)},
        "count": {"severity": severity_counts(findings)},
    }


def _resolve(metric: str, metrics: dict):
    cur = metrics
    for part in metric.split("."):
        cur = (cur or {}).get(part) if isinstance(cur, dict) else None
    return cur if cur is not None else 0


def evaluate_gate(results: list[TestResult], campaign_id: str, run_id: str,
                  baseline_path: str, rules: list[dict]) -> GateResult:
    cur = metrics_for(results, campaign_id)
    base = json.loads(Path(baseline_path).read_text(encoding="utf-8")).get("metrics", {}) \
        if Path(baseline_path).exists() else {}

    violations: list[GateViolation] = []
    warnings: list[GateViolation] = []
    for rule in rules:
        actual = _resolve(rule["metric"], cur)
        op = rule["operator"]
        ok, expected = _check(op, actual, rule.get("value"), _resolve(rule["metric"], base))
        if not ok:
            v = GateViolation(rule=rule["id"], metric=rule["metric"],
                              expected=expected, actual=actual,
                              severity=rule.get("action", "fail"))
            (warnings if v.severity == "warn" else violations).append(v)
    return GateResult(passed=len(violations) == 0, run_id=run_id,
                      violations=violations, warnings=warnings)


def _check(op: str, actual, value, baseline):
    """Return (passed, expected_str). Supports ==, <=, <=baseline, <=baseline+X."""
    try:
        actual = float(actual)
    except (TypeError, ValueError):
        actual = 0.0
    if op == "==":
        return actual == float(value), f"=={value}"
    if op == "<=":
        return actual <= float(value), f"<={value}"
    if op == "<=baseline":
        b = float(baseline or 0)
        return actual <= b, f"<=baseline({b})"
    if op.startswith("<=baseline+"):
        delta = float(op.split("+", 1)[1])
        b = float(baseline or 0)
        return actual <= b + delta, f"<=baseline({b})+{delta}"
    return True, op


def gate_to_dict(gr: GateResult) -> dict:
    return {
        "passed": gr.passed, "run_id": gr.run_id,
        "violations": [vars(v) for v in gr.violations],
        "warnings": [vars(v) for v in gr.warnings],
    }


def gate_summary(gr: GateResult) -> str:
    head = "GATE: PASS" if gr.passed else "GATE: FAIL"
    lines = [f"{head} ({len(gr.violations)} violations, {len(gr.warnings)} warnings)"]
    for v in gr.violations:
        lines.append(f"  x {v.rule}: {v.metric}={v.actual} (expected {v.expected})")
    for w in gr.warnings:
        lines.append(f"  ! {w.rule}: {w.metric}={w.actual} (expected {w.expected})")
    return "\n".join(lines)
