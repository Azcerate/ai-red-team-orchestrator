"""Recon detectors (ports of temperature_probe + rate_limiter)."""
from __future__ import annotations
import threading, time
from dataclasses import dataclass
from ..core.ids import now_iso, result_id
from ..core.models import TestResult


@dataclass
class ReconResult:
    determinism: float | None = None
    successful: int = 0
    rate_limit_rpm: float | None = None
    rate_limited: bool = False
    notes: str = ""


def _send(target, message):
    import requests
    headers = {"Content-Type": "application/json"}
    for k, v in (target.get("headers") or {}).items():
        headers[k] = v
    try:
        rr = requests.post(target["base_url"],
                           json={target.get("message_field","message"): message,
                                 target.get("conversation_id_field","conversation_id"): None},
                           headers=headers, timeout=target.get("timeout_seconds", 60))
        try: data = rr.json()
        except ValueError: data = {}
        ok = rr.ok and bool(data.get(target.get("success_field","success")))
        return ok, data.get(target.get("response_field","response")), rr.status_code
    except Exception:
        return False, None, 0


def probe_determinism(target, message="What is your return policy?", n=10, rpm=30.0) -> ReconResult:
    delay = 60.0/rpm; responses=[]; successful=0
    for i in range(n):
        ok, text, _ = _send(target, message)
        if ok and text: responses.append(text); successful+=1
        if i < n-1: time.sleep(delay)
    uniq = len(set(responses)) if responses else 0
    det = (uniq/successful) if successful else None
    return ReconResult(determinism=det, successful=successful, notes=f"{uniq} unique of {successful} successful")


def probe_rate_limit(target, n=50, rpm=120.0) -> ReconResult:
    delay=60.0/rpm; info={}; rate_limited=threading.Event(); start=time.time()
    def worker(i, scheduled):
        w=scheduled-time.time()
        if w>0: time.sleep(w)
        import requests
        try:
            rr=requests.post(target["base_url"],
                json={target.get("message_field","message"):"Hello", target.get("conversation_id_field","conversation_id"):None},
                headers={"Content-Type":"application/json"}, timeout=target.get("timeout_seconds",60))
            status=rr.status_code
        except Exception:
            status=0
        if status==429 and not rate_limited.is_set():
            rate_limited.set(); elapsed=time.time()-start
            info["rpm"]=(i/elapsed)*60 if elapsed>0 else 0
    threads=[]
    for i in range(1,n+1):
        if rate_limited.is_set(): break
        t=threading.Thread(target=worker,args=(i,start+(i-1)*delay),daemon=True); t.start(); threads.append(t)
        if i%10==0: time.sleep(0.01)
    for t in threads: t.join(timeout=30)
    return ReconResult(rate_limited=rate_limited.is_set(), rate_limit_rpm=info.get("rpm"),
                       notes=("rate limit detected" if rate_limited.is_set() else f"no rate limit up to {rpm} rpm"))


def recon_to_result(rl, run_id, campaign_id, target_id="") -> TestResult:
    leaked = not rl.rate_limited
    return TestResult(result_id=result_id(), run_id=run_id, campaign_id=campaign_id, timestamp=now_iso(),
        prompt_id="recon:rate_limit", prompt="[recon] burst of requests to detect rate limiting",
        category="rate_limit_weakness", attack_type="rate_limit_probe", target_id=target_id,
        response_text=rl.notes, judge_label="success" if leaked else "fail", judge_confidence=1.0,
        judge_reasons=[rl.notes], phrase_check=None, success=leaked,
        severity="medium" if leaked else "info")
