"""End-to-end orchestration: load -> run -> judge -> score -> map -> evidence -> persist.

Prompt sources: corpus CSV files and/or code-based probes (the probe engine).
"""
from __future__ import annotations

import concurrent.futures as cf

from ..config.loader import load_yaml
from ..config.schemas import assert_authorized, validate_campaign, validate_target
from ..corpus.loader import load_campaign_corpus
from ..core.errors import ConfigError
from ..evidence.store import attach_evidence
from ..frameworks.mapper import FrameworkMapper
from ..judges.ensemble import EnsembleJudge
from ..runners.http_runner import HttpRunner
from ..scoring.scorer import score_result
from ..storage.jsonl import write_results
from .ids import mint_run_id
from .models import TestResult


def _gather_items(campaign, probes=None):
    items = []
    if campaign.get("corpus"):
        items.extend(load_campaign_corpus(campaign["corpus"]))
    probe_names = probes if probes is not None else campaign.get("probes")
    if probe_names:
        from ..probes.registry import load_probes
        for probe in load_probes(probe_names):
            items.extend(list(probe.generate()))
    return items


def run_campaign(campaign_path: str, limit: int | None = None,
                 category: str | None = None, dry_run: bool = False,
                 redact: bool = True, concurrency: int = 2,
                 probes=None) -> str:
    campaign = validate_campaign(load_yaml(campaign_path))
    target = validate_target(load_yaml(_target_path(campaign)))
    assert_authorized(target)                       # ROE gate

    items = _gather_items(campaign, probes)
    if category:
        items = [i for i in items if i.category == category]
    if limit:
        items = items[:limit]
    if not items:
        raise ConfigError("no prompts: provide corpus files and/or probes")

    run_id = mint_run_id(campaign["id"])
    if dry_run:
        cats = sorted({i.category for i in items})
        print(f"[dry-run] {len(items)} prompts across {len(cats)} categories "
              f"({', '.join(cats)}) against {target.get('base_url')} "
              f"— no requests sent. run_id={run_id}")
        return run_id

    judge_cfg = load_yaml(campaign["judge"]).get("judge", {}) if campaign.get("judge") else {}
    runner = HttpRunner(target, run_id, campaign["id"])
    judge = EnsembleJudge(judge_cfg)
    mapper = FrameworkMapper()
    extra_canaries = judge_cfg.get("extra_canaries")

    def process(item) -> TestResult:
        r = runner.run(item)
        r = judge.judge(r)
        r = score_result(r)
        r = mapper.map_result(r)
        r = attach_evidence(r, run_id, redact_enabled=redact, extra_canaries=extra_canaries)
        return r

    results: list[TestResult] = []
    with cf.ThreadPoolExecutor(max_workers=concurrency) as pool:
        for r in pool.map(process, items):
            results.append(r)

    write_results(run_id, results)
    print(f"run complete: {run_id} ({len(results)} results)")
    return run_id


def _target_path(campaign: dict) -> str:
    return campaign.get("target_config", "config/target.yml")
