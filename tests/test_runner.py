import json
from orchestrator.runners.http_runner import HttpRunner, _dig


def test_dig_dotted_with_list_index():
    data = {"choices": [{"message": {"content": "hello"}}]}
    assert _dig(data, "choices.0.message.content") == "hello"
    assert _dig({"a": {"b": 1}}, "a.b") == 1
    assert _dig({"a": 1}, "x.y") is None


def test_payload_template_json_escapes_prompt():
    cfg = {"base_url": "http://x", "body_template":
           '{"model":"m","messages":[{"role":"user","content":{{PROMPT}}}]}'}
    r = HttpRunner(cfg, "run", "c")
    payload = r._payload('say "hi"\nnewline')
    assert payload["messages"][0]["content"] == 'say "hi"\nnewline'


def test_payload_default_tmc_shape():
    r = HttpRunner({"base_url": "http://x"}, "run", "c")
    p = r._payload("hello")
    assert p == {"message": "hello", "conversation_id": None}
