"""Render a full client-grade Markdown report (stdlib only)."""
from __future__ import annotations
from pathlib import Path
from .builder import ReportModel


def render_markdown(model: ReportModel, out_dir: str = "reports") -> Path:
    L = []; a = L.append
    branding = (model.meta or {}).get("branding", {})
    company = branding.get("company_name", "DMCS Labs")
    a(f"# AI Red Team Assessment — {model.client}"); a("")
    a(f"**Prepared by:** {company}  ")
    a(f"**Target system:** {model.target_name}  ")
    a(f"**Run ID:** {model.run_id}  ")
    a(f"**Report generated:** {model.generated}  ")
    a(f"**Overall risk rating:** {model.overall_rating}"); a("")
    a("> Confidential — prepared for the named client under signed rules of engagement."); a("")
    a("## 1. Executive Summary"); a(""); a(_exec_summary(model)); a("")
    a("**Severity summary:** " + ", ".join(f"{s.title()}: {model.severity_counts.get(s,0)}"
        for s in ("critical","high","medium","low","info"))); a("")
    a("## 2. Scope & Rules of Engagement"); a("")
    scope = model.scope or {}
    a(f"- **Authorized target(s):** {scope.get('targets', model.target_name)}")
    a(f"- **Testing window:** {scope.get('window', 'see engagement record')}")
    a(f"- **Authorization:** {scope.get('authorization', 'signed authorization on file')}")
    a(f"- **Out of scope:** {scope.get('out_of_scope', 'all systems not explicitly named')}"); a("")
    a("## 3. Methodology"); a("")
    a("Adversarial test cases were executed against the target across multiple attack "
      "categories. Each response was evaluated by a two-stage pipeline: a deterministic "
      "phrase/canary check and an LLM-as-judge classifier. Deterministic canary hits are "
      "ground truth and override the judge. Findings are scored for success and severity, "
      "then mapped to OWASP LLM Top 10 (2025), MITRE ATLAS, and NIST CSF 2.0. ASR is "
      "successes over decisive attempts; errored/inconclusive attempts are excluded from the "
      "denominator and reported separately."); a("")
    a("## 4. Overall Results"); a("")
    a(f"- **Total test cases:** {model.total_tests}")
    a(f"- **Overall attack success rate:** {model.overall_asr:.0%}")
    a(f"- **Inconclusive / errored:** {model.errored}"); a("")
    a("### Category breakdown"); a(""); a("| Category | Attack success rate |"); a("|----------|---------------------|")
    for cat, asr in sorted(model.category_asr.items(), key=lambda x: -x[1]):
        a(f"| {cat} | {asr:.0%} |")
    a("")
    a("## 5. Findings Overview"); a("")
    a("| ID | Category | Severity | ASR | OWASP | Status |"); a("|----|----------|----------|-----|-------|--------|")
    for f in model.findings:
        owasp = next((r["id"] for r in f.framework_refs if r.get("framework")=="owasp_llm_2025"), "-")
        a(f"| {f.id} | {f.category} | {f.severity} | {f.asr:.0%} ({f.asr_success}/{f.asr_total - f.asr_errored}) | {owasp} | {f.review_status} |")
    a("")
    a("## 6. Detailed Findings")
    for f in model.findings:
        a(""); a(f"### {f.id} — {f.title} ({f.severity})")
        conf = f"{f.mean_confidence:.2f}" if f.mean_confidence is not None else "n/a"
        a(f"**ASR:** {f.asr:.0%} ({f.asr_success}/{f.asr_total}, {f.asr_errored} errored) · **Mean judge confidence:** {conf} · **Validation:** {f.review_status}")
        refs = " · ".join(f"{r.get('framework')}:{r.get('id')}" for r in f.framework_refs)
        a(f"**Framework mapping:** {refs or 'n/a'}"); a("")
        a(f"> **Prompt:** {f.sample_prompt}"); a(">"); a(f"> **Response:** {f.sample_response}"); a("")
        a(f"**Business impact:** {f.business_impact or _impact(f)}")
        a(f"**Remediation:** {f.remediation or 'See framework guidance.'}")
        a(f"**Evidence:** {', '.join(f.evidence_ids) or 'see appendix'}")
    a("")
    a("## 7. Framework Alignment"); a("")
    a("| Category | OWASP LLM 2025 | MITRE ATLAS | NIST CSF 2.0 | Remediation theme |")
    a("|----------|----------------|-------------|--------------|-------------------|")
    for r in model.framework_rollup:
        a(f"| {r['category']} | {r['owasp']} | {r['atlas']} | {r['nist']} | {r['remediation']} |")
    a("")
    a("## 8. Appendix — Evidence"); a("")
    a(f"Redacted prompt/response evidence is stored alongside this run (`results/{model.run_id}.evidence.jsonl`). Raw evidence is retained only when explicitly authorized."); a("")
    a("## 9. Limitations"); a("")
    a("This assessment reflects point-in-time testing of a non-deterministic system; the absence of a finding is not a guarantee of security. LLM-as-judge results carry inherent uncertainty — see judge-validation metrics for reliability figures."); a("")
    a("## 10. Next Steps"); a("")
    a("Prioritize remediation of Critical and High findings, then re-test using the included regression gate before the next release. Consider continuous monthly testing to detect model-behavior drift."); a("")
    a("## Legal Disclaimer"); a("")
    a("This assessment was conducted on systems the client owns or is authorized to test, under signed rules of engagement. Findings are provided for defensive remediation purposes only.")
    out = Path(out_dir) / f"{model.run_id}.md"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8"); return out


def _exec_summary(m: ReportModel) -> str:
    crit = m.severity_counts.get("critical",0); high = m.severity_counts.get("high",0)
    lead = (f"We executed {m.total_tests} adversarial test cases against {m.target_name}. "
            f"The overall risk rating is **{m.overall_rating}** ({crit} Critical, {high} High). "
            f"The overall attack success rate was {m.overall_asr:.0%}, with {m.errored} inconclusive or errored attempts.")
    if m.findings:
        t = m.findings[0]
        lead += f" The most serious issue is **{t.id} — {t.title}** ({t.severity}, ASR {t.asr:.0%})."
    return lead


def _impact(f) -> str:
    table = {"canary_leakage":"Unauthorized disclosure of sensitive/restricted data.",
        "rag_fishing":"Exposure of documents beyond the requesting user's entitlement.",
        "idor_rbac":"Authorization bypass enabling access to other users' data.",
        "prompt_injection":"Attacker control over assistant behavior and policy.",
        "jailbreak":"Bypass of safety/policy guardrails.",
        "unsafe_output":"Harmful or unsafe content delivered to users.",
        "context_overflow":"Degraded safety/availability under large inputs.",
        "rate_limit_weakness":"Denial-of-service and cost-abuse exposure.",
        "offtopic_abuse":"Brand/scope control bypass."}
    return table.get(f.category, "Security control weakness in the AI workflow.")
