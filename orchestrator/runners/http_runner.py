"""HTTP runner — refactor of prompt_tester.py.

Improvements over the original script:
- parses the TMC `{success, response, conversation_id}` envelope (configurable)
- adds retries + exponential backoff (original had none)
- bounded concurrency is handled by the pipeline, not one-thread-per-request
- never mutates source files; returns TestResult objects

`requests` is imported lazily so the package imports without it installed.
"""
from __future__ import annotations

import os
import time
from typing import Any

from ..core.ids import result_id, now_iso
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
        self.success_field = target_cfg.get("success_field", "success")
        self.response_field = target_cfg.get("response_field", "response")
        self.conv_field = target_cfg.get("conversation_id_field", "conversation_id")
        self.message_field = target_cfg.get("message_field", "message")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        for k, v in (self.cfg.get("headers") or {}).items():
            headers[k] = _expand_env(v)
        return headers

    def run(self, item: PromptItem) -> TestResult:
        import requests  # lazy

        payload: dict[str, Any] = {self.message_field: item.prompt, self.conv_field: None}
        last_error = None
        status = None
        for attempt in range(self.retries + 1):
            start = time.time()
            try:
                resp = requests.request(
                    self.method, self.url, json=payload,
                    headers=self._headers(), timeout=self.timeout,
                )
                latency = int((time.time() - start) * 1000)
                status = resp.status_code
                try:
                    data = resp.json()
                except ValueError:
                    data = {}
                ok = resp.ok and bool(data.get(self.success_field))
                if ok:
                    return self._result(item, data.get(self.response_field, ""),
                                        status, latency,
                                        data.get(self.conv_field), None)
                # rate-limited or app-level failure
                last_error = data.get("error", f"HTTP {status}")
                if status == 429 and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                    continue
                return self._result(item, None, status, latency, None, last_error)
            except Exception as e:  # transport/timeout
                last_error = str(e)
                if attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
        return self._result(item, None, status, None, None, last_error or "unknown error")

    def _result(self, item, text, status, latency, conv, error) -> TestResult:
        return TestResult(
            result_id=result_id(),
            run_id=self.run_id,
            campaign_id=self.campaign_id,
            timestamp=now_iso(),
            prompt_id=item.prompt_id,
            prompt=item.prompt,
            category=item.category,
            attack_type=item.attack_type,
            phrase_target=item.phrase_target,
            target_id=self.cfg.get("id", ""),
            request_meta={"url": self.url, "method": self.method},
            response_text=text,
            http_status=status,
            latency_ms=latency,
            conversation_id=conv,
            error=error,
        )


def _expand_env(value: str) -> str:
    """Resolve ${VAR} references from environment at runtime."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value
