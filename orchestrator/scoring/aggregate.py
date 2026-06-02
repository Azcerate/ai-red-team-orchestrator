"""Aggregate scored results into metrics + findings."""
from __future__ import annotations

from collections import defaultdict

from ..core.ids import finding_id
from ..core.models import Finding, TestResult
from .scorer import SEVERITY_ORDER

# short codes used in finding IDs
CATEGORY_CODE = {
    "canary_leakage": "CAN", "rag_fishing": "RAG", "idor_rbac": "IDOR",
    "prompt_injection": "INJ", "jailbreak": "JB", "excessive_agency": "AGCY",
    "unsafe_output": "OUT", "context_overflow": "CTX",
    "rate_limit_weakness": "RATE", "offtopic_abuse": "OFF", "uncategorized": "GEN",
}


def category_asr(results: list[TestResult]) -> dict[str, float]:
    succ = defaultdict(int)
    denom = defaultdict(int)
    for r in results:
        if r.success is None:  # inconclusive/errored excluded
            continue
        denom[r.category] += 1
        if r.success:
            succ[r.category] += 1
    return {c: (succ[c] / denom[c]) for c in denom if denom[c] > 0}


def overall_asr(results: list[TestResult]) -> float:
    scored = [r for r in results if r.success is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.success) / len(scored)


def severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


def build_findings(results: list[TestResult], campaign_id: str) -> list[Finding]:
    """Cluster successful results by category into ranked findings."""
    by_cat: dict[str, list[TestResult]] = defaultdict(list)
    for r in results:
        by_cat[r.category].append(r)

    findings: list[Finding] = []
    counter: dict[str, int] = defaultdict(int)
    for cat, rows in by_cat.items():
        succ = [r for r in rows if r.success]
        if not succ:
            continue
        total = len(rows)
        errored = sum(1 for r in rows if r.success is None)
        sev = _max_sev(succ)
        confs = [r.judge_confidence for r in succ if r.judge_confidence is not None]
        counter[cat] += 1
        code = CATEGORY_CODE.get(cat, "GEN")
        sample = succ[0]
        findings.append(Finding(
            id=finding_id(campaign_id, code, counter[cat]),
            title=_title(cat),
            category=cat,
            severity=sev,
            asr_success=len(succ),
            asr_total=total,
            asr_errored=errored,
            mean_confidence=(sum(confs) / len(confs)) if confs else None,
            review_status="confirmed" if any(r.phrase_check for r in succ) else "auto",
            framework_refs=sample.framework_refs,
            evidence_ids=[r.evidence_id for r in succ if r.evidence_id][:10],
            sample_prompt=sample.prompt[:600],
            sample_response=(sample.response_text or "")[:600],
        ))
    findings.sort(key=lambda f: SEVERITY_ORDER.index(f.severity), reverse=True)
    return findings


def _max_sev(rows: list[TestResult]) -> str:
    sevs = [r.severity for r in rows if r.severity]
    if not sevs:
        return "info"
    return max(sevs, key=lambda s: SEVERITY_ORDER.index(s))


def _title(cat: str) -> str:
    return cat.replace("_", " ").title()
