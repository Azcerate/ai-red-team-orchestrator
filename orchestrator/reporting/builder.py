"""Assemble a ReportModel from scored results + findings (client-grade)."""
from __future__ import annotations
from dataclasses import dataclass, field
from ..core.ids import now_iso
from ..core.models import Finding, TestResult
from ..frameworks.mapper import FrameworkMapper
from ..scoring.aggregate import (build_findings, category_asr, overall_asr, severity_counts)


@dataclass
class ReportModel:
    campaign_id: str
    run_id: str
    client: str
    target_name: str
    overall_rating: str
    overall_asr: float
    category_asr: dict
    severity_counts: dict
    findings: list
    framework_rollup: list
    total_tests: int
    errored: int
    generated: str
    scope: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


def _overall_rating(counts: dict) -> str:
    for sev in ("critical", "high", "medium", "low"):
        if counts.get(sev):
            return sev.upper()
    return "INFORMATIONAL"


def build_report(results, campaign_id: str, run_id: str, report_cfg=None) -> ReportModel:
    report_cfg = report_cfg or {}
    mapper = FrameworkMapper()
    findings = build_findings(results, campaign_id)
    for f in findings:
        if not f.framework_refs:
            f.framework_refs = mapper.refs_for(f.category)
        if not f.remediation:
            f.remediation = mapper.remediation_for(f.category)
    counts = severity_counts(findings)
    rollup = _framework_rollup(findings, mapper)
    return ReportModel(
        campaign_id=campaign_id, run_id=run_id,
        client=report_cfg.get("client", "Client"),
        target_name=report_cfg.get("target_name", campaign_id),
        overall_rating=_overall_rating(counts),
        overall_asr=overall_asr(results),
        category_asr=category_asr(results),
        severity_counts=counts, findings=findings, framework_rollup=rollup,
        total_tests=len(results),
        errored=sum(1 for r in results if r.success is None),
        generated=now_iso(), scope=report_cfg.get("scope", {}), meta=report_cfg)


def _framework_rollup(findings, mapper) -> list:
    rows = []; seen = set()
    for f in findings:
        if f.category in seen:
            continue
        seen.add(f.category)
        refs = {}
        for r in f.framework_refs:
            refs.setdefault(r["framework"], r)
        rows.append({"category": f.category, "owasp": _fmt(refs.get("owasp_llm_2025")),
                     "atlas": _fmt(refs.get("mitre_atlas")), "nist": _fmt(refs.get("nist_csf_2")),
                     "remediation": f.remediation or mapper.remediation_for(f.category)})
    return rows


def _fmt(ref) -> str:
    if not ref:
        return "-"
    return f"{ref.get('id')} {ref.get('name')}"
