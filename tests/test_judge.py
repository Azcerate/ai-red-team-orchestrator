"""Judge provider tests — mock the HTTP layer; no network or API keys needed."""
import os
import sys
import types

from orchestrator.core.models import TestResult
from orchestrator.judges.llm_judge import LLMJudge


def _result(resp="leaked the system prompt"):
    return TestResult(result_id="r", run_id="run", campaign_id="tmc", timestamp="t",
                      prompt_id="p", prompt="ignore instructions", category="prompt_injection",
                      response_text=resp)


def _install_fake_requests(handler):
    """handler(url, **kwargs) -> dict (the JSON body the provider returns)."""
    mod = types.ModuleType("requests")

    class _Resp:
        def __init__(self, payload):
            self._p = payload
            self.ok = True
            self.status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return self._p

    mod.post = lambda url, **kw: _Resp(handler(url, **kw))
    sys.modules["requests"] = mod


def test_ollama_provider_parses():
    _install_fake_requests(lambda url, **kw: {
        "response": '{"label":"SUCCESS","confidence":92,"reasons":["revealed system prompt"]}'})
    j = LLMJudge({"provider": "ollama"}).judge(_result())
    assert j.label == "success" and abs(j.confidence - 0.92) < 1e-6
    assert j.reasons == ["revealed system prompt"]


def test_anthropic_provider_parses_content_blocks():
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    _install_fake_requests(lambda url, **kw: {
        "content": [{"type": "text",
                     "text": '{"label":"NO_SUCCESS","confidence":80,"reasons":["refused"]}'}]})
    j = LLMJudge({"provider": "anthropic"}).judge(_result())
    assert j.label == "fail" and abs(j.confidence - 0.80) < 1e-6


def test_openai_provider_parses_choices():
    os.environ["OPENAI_API_KEY"] = "test-key"
    _install_fake_requests(lambda url, **kw: {
        "choices": [{"message": {"content":
                     'sure: {"label":"POSSIBLE","confidence":55,"reasons":["partial"]}'}}]})
    j = LLMJudge({"provider": "openai"}).judge(_result())
    assert j.label == "partial" and abs(j.confidence - 0.55) < 1e-6


def test_missing_api_key_is_handled():
    os.environ.pop("ANTHROPIC_API_KEY", None)
    _install_fake_requests(lambda url, **kw: {})
    j = LLMJudge({"provider": "anthropic"}).judge(_result())
    assert j.label == "error" and "ANTHROPIC_API_KEY" in " ".join(j.reasons)


def test_unknown_provider_rejected():
    try:
        LLMJudge({"provider": "bogus"})
        assert False, "should have raised"
    except ValueError:
        pass
