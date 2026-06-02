"""Stable / unique ID generation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mint_run_id(campaign_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}_{campaign_id}"


def result_id() -> str:
    return uuid.uuid4().hex


def short_id(value: str, n: int = 6) -> str:
    return value[:n]


def evidence_id(result_id_value: str) -> str:
    return f"EV-{short_id(result_id_value)}"


def finding_id(campaign_id: str, category_code: str, n: int) -> str:
    return f"AIRT-{campaign_id.upper()}-{category_code.upper()}-{n:03d}"
