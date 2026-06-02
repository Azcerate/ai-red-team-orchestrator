"""Probe base class. A probe generates adversarial PromptItems (code, not CSV).

Subclasses set name/category/attack_type and implement generate(). They may set
a phrase_target on items (deterministic canary/phrase detection) or rely on the
LLM-as-judge. Probes flow into the SAME pipeline as corpus files.
"""
from __future__ import annotations

from typing import Iterable

from ..core.models import PromptItem


class Probe:
    name: str = "probe"
    category: str = "uncategorized"
    attack_type: str = ""
    description: str = ""

    def generate(self) -> Iterable[PromptItem]:  # pragma: no cover - abstract
        raise NotImplementedError

    def item(self, idx, prompt: str, phrase_target: str | None = None,
             attack_type: str | None = None) -> PromptItem:
        return PromptItem(
            prompt_id=f"{self.name}:{idx}",
            prompt=prompt,
            category=self.category,
            attack_type=attack_type or self.attack_type or self.name,
            phrase_target=phrase_target,
            source_file=f"probe:{self.name}",
        )
