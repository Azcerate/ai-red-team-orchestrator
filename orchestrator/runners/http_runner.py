"""HTTP runner — sends prompts to a target and captures responses.

Works with any JSON HTTP target via config:
  - body_template: JSON string with the {{PROMPT}} placeholder (auto JSON-escaped).
                   If omitted, sends {message_field: prompt, conversation_id: null} (TMC default).
  - response_path: dotted path into the JSON response, supports list indices,
                   e.g. "choices.0.message.content" (OpenAI), "content.0.text" (Anthropic),
                   "response" (Ollama / TMC).
  - success_field: optional; if set, response is "successful" only when truthy.
                   If omitted, HTTP 2xx counts as success.
  - headers: ${ENV_VAR} references resolved at runtime (API keys never stored in files).

Adds retries + exponential backoff. `requests` imported lazily.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from ..core.ids import now_iso, result_id
from ..core.models import PromptItem, TestResult


class HttpRunner:
    def __init__(self, target_cfg: dict, run_id: str, campaign_id: str):
        self.cfg = target_cfg
        self.run_id = run_id
        self.campaign_id = campaign_id
        self.url = target_cfg["base_url"]
        self.method = target_cfg.get("method", "POST")
        self.timeout = target_cfg.get("timeout_seconds", 120)
        self.retries = target_cfg.get("retries", 2)
        self.backoff = target_cfg.get("backoff_seconds", 2)
        self.body_template = target_cfg.get("body_template")
        self.response_path = target_cfg.get("response_path", target_cfg.get("response_field", "response"))
        self.success_field = target_cfg.get("success_field")          # optional
        self.message_field = target_cfg.get("message_field", "message")
        self.conv_field = target_cfg.get("conversation_id_field", "conversation_id")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        for k, v in (self.cfg.get("headers") or {}).items():
            headers[k] = _expand_env(v)
        return headers

    def _payload(self, prompt: str) -> dict[str, Any]:
        if self.body_template:
            return json.loads(self.body_template.replace("{{PROMPT}}", json.dumps(prompt)))
        return {self.message_field: prompt, self.conv_field: None}

    def run(self, item: PromptItem) -> TestResult:
        import requests  # lazy
        last_error = None
        status = None
        for attempt in range(self.retries + 1):
            start = time.time()
            try:
                resp = requests.request(self.method, self.url, json=self._payload(item.prompt),
                                        headers=self._headers(), timeout=self.timeout)
                latency = int((time.time() - start) * 1000)
                status = resp.status_code
                try:
                    data = resp.json()
                except ValueError:
                    data = {}
                ok = resp.ok and (bool(_dig(data, self.success_field)) if self.success_field else True)
                if ok:
                    text = _dig(data, self.response_path)
                    if isinstance(text, (dict, list)):
                        text = json.dumps(text)
                    return self._result(item, text if text is not None else "", status, latency,
                                        _dig(data, self.conv_field), None)
                last_error = (_dig(data, "error") if isinstance(data, dict) else None) or f"HTTP {status}"
                if status == 429 and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt)); continue
                return self._result(item, None, status, latency, None, str(last_error))
            except Exception as e:
                last_error = str(e)
                if attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
        return self._result(item, None, status, None, None, last_error or "unknown error")

    def _result(self, item, text, status, latency, conv, error) -> TestResult:
        return TestResult(
            result_id=result_id(), run_id=self.run_id, campaign_id=self.campaign_id,
            timestamp=now_iso(), prompt_id=item.prompt_id, prompt=item.prompt,
            category=item.category, attack_type=item.attack_type, phrase_target=item.phrase_target,
            target_id=self.cfg.get("id", ""), request_meta={"url": self.url, "method": self.method},
            response_text=text, http_status=status, latency_ms=latency,
            conversation_id=conv if isinstance(conv, str) else None, error=error)


def _expand_env(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


def _dig(data, path):
    """Walk a dotted path with dict keys and integer list indices."""
    if not path:
        return None
    cur = data
    for part in str(path).split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if cur is None:
            return None
    return cur
