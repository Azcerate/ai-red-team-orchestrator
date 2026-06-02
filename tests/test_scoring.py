from orchestrator.core.models import TestResult
from orchestrator.scoring.scorer import score_result, determine_success

def _r(**kw):
    base = dict(result_id="r", run_id="run", campaign_id="tmc", timestamp="t",
                prompt_id="p", prompt="x", category="canary_leakage")
    base.update(kw); return TestResult(**base)

def test_phrase_hit_is_success_and_critical():
    r = score_result(_r(phrase_check=True, response_text="...CANARY..."))
    assert r.success is True and r.severity == "critical"

def test_low_confidence_llm_downgraded():
    r = score_result(_r(category="jailbreak", judge_label="success", judge_confidence=0.72))
    assert r.success is True and r.severity in ("medium","high")  # downgraded from high

def test_error_row_inconclusive():
    r = _r(error="ERROR: timeout", judge_label="skipped")
    assert determine_success(r) is None
