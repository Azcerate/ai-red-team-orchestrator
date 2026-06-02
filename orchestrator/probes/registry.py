"""Probe registry: register, list, and load probes by name."""
from __future__ import annotations

from .base import Probe

_REGISTRY: dict[str, type[Probe]] = {}


def register(cls: type[Probe]) -> type[Probe]:
    if not getattr(cls, "name", None):
        raise ValueError("probe class must define a name")
    _REGISTRY[cls.name] = cls
    return cls


def _ensure_loaded() -> None:
    # importing the library module triggers @register decorators
    from . import library  # noqa: F401


def all_probes() -> dict[str, type[Probe]]:
    _ensure_loaded()
    return dict(_REGISTRY)


def get_probe(name: str) -> Probe:
    _ensure_loaded()
    if name not in _REGISTRY:
        raise KeyError(f"unknown probe: {name} (see `airt probes list`)")
    return _REGISTRY[name]()


def load_probes(names) -> list[Probe]:
    _ensure_loaded()
    if names in (None, "all", ["all"]):
        return [cls() for cls in _REGISTRY.values()]
    return [get_probe(n) for n in names]
