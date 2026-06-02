"""Lightweight config validation helpers (stdlib; swap for pydantic later).

Kept intentionally small for the MVP. Promote to pydantic models in V1 for
strict typing and better error messages.
"""
from __future__ import annotations

from ..core.errors import AuthorizationError, ConfigError


def validate_target(cfg: dict) -> dict:
    t = cfg.get("target", cfg)
    if "base_url" not in t:
        raise ConfigError("target.base_url is required")
    return t


def assert_authorized(target_cfg: dict) -> None:
    """ROE gate: refuse to run against unauthorized targets."""
    if not target_cfg.get("authorized", False):
        raise AuthorizationError(
            f"Target '{target_cfg.get('id', '?')}' is not marked authorized. "
            "Set target.authorized: true only with signed rules of engagement."
        )


def validate_campaign(cfg: dict) -> dict:
    c = cfg.get("campaign", cfg)
    for key in ("id", "corpus"):
        if key not in c:
            raise ConfigError(f"campaign.{key} is required")
    return c
