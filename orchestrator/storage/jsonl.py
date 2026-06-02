"""Primary persistence: one JSON object per line (TestResult)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from ..core.models import TestResult


def write_results(run_id: str, results: Iterable[TestResult], results_dir: str = "results") -> Path:
    out = Path(results_dir) / f"{run_id}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    return out


def append_result(run_id: str, result: TestResult, results_dir: str = "results") -> None:
    out = Path(results_dir) / f"{run_id}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")


def read_results(run_id: str, results_dir: str = "results") -> list[TestResult]:
    path = Path(results_dir) / f"{run_id}.jsonl"
    return list(_iter_file(path))


def _iter_file(path: Path) -> Iterator[TestResult]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield TestResult(**json.loads(line))
