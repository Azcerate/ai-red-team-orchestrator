"""YAML config loading + light validation + ${ENV} expansion."""
from __future__ import annotations

import os
import re
from pathlib import Path

from ..core.errors import ConfigError

_ENV = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_yaml(path: str | Path) -> dict:
    import yaml  # lazy
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Config not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return _expand(data)


def _expand(obj):
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    if isinstance(obj, str):
        return _ENV.sub(lambda m: os.environ.get(m.group(1), ""), obj)
    return obj


def require(cfg: dict, *keys: str) -> None:
    missing = [k for k in keys if k not in cfg]
    if missing:
        raise ConfigError(f"Missing required config keys: {missing}")
