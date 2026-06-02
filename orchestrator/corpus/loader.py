"""Corpus loading + normalization.

Real corpus schema is `id, technique, prompt` for EVERY file. Category is
derived from the campaign file mapping (not the row). `technique` is overloaded:
- normal categories -> attack_type label
- canary/RAG categories -> also the phrase to detect (phrase_target)
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..core.errors import ConfigError
from ..core.models import PromptItem

# Categories where the `technique` column is (also) a phrase/canary to detect.
PHRASE_CATEGORIES = {"canary_leakage", "rag_fishing", "context_overflow"}

# Known canary tokens seen in the TMC corpus. Confirm/extend this list.
KNOWN_CANARIES = ["EXAMPLECANARY01", "CANARY_EXAMPLE", "CANARY_EXAMPLE_2025"]

REQUIRED_COLUMNS = {"id", "technique", "prompt"}


def load_corpus_file(path: str | Path, category: str) -> list[PromptItem]:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Corpus file not found: {p}")
    items: list[PromptItem] = []
    with p.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - cols
        if missing:
            raise ConfigError(f"{p} missing columns: {sorted(missing)} (found {sorted(cols)})")
        for i, row in enumerate(reader, start=1):
            prompt = (row.get("prompt") or "").strip()
            if not prompt:
                continue  # skip blank prompts, matching prompt_tester behavior
            technique = (row.get("technique") or "").strip()
            phrase_target = None
            if category in PHRASE_CATEGORIES:
                phrase_target = technique or None
            items.append(
                PromptItem(
                    prompt_id=f"{category}:{row.get('id', i)}",
                    prompt=prompt,
                    category=category,
                    attack_type=technique,
                    phrase_target=phrase_target,
                    source_file=str(p),
                )
            )
    if not items:
        raise ConfigError(f"No usable prompts in {p}")
    return items


def load_campaign_corpus(corpus_entries: list[dict]) -> list[PromptItem]:
    """corpus_entries: [{"path": ..., "category": ...}, ...] from campaign.yml."""
    items: list[PromptItem] = []
    for entry in corpus_entries:
        items.extend(load_corpus_file(entry["path"], entry["category"]))
    return items
