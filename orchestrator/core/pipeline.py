"""End-to-end orchestration: load -> run -> judge -> score -> map -> evidence -> persist.

This wires the modules together. The runner/judge make network calls, so the
pipeline is import-safe but requires a reachable target + judge at runtime.
"""
from __future__ import annotations

import concurrent.futures as cf

from ..config.loader import load_yaml
from ..config.schemas import assert_authorized, validate_campaign, validate_target
from ..corpus.loader import load_campaign_corpus
from ..evidence.store import attach_evidence
from ..frameworks.mapper import FrameworkMapper
from ..judges.ensemble import EnsembleJudge
from ..runners.http_runner import HttpRunner
from ..scoring.scorer import score_result
from ..storage.jsonl import write_results
from .ids import mint_run_id
from .models import TestResult


def run_campaign(campaign_path: str, limit: int | None = None,
                 category: str | None = None, dry_run: bool = False,
                 redact: bool = True, concurrency: int = 2) -> str:
    campaign = validate_campaign(load_yaml(campaign_path))
    target = validate_target(load_yaml(_target_path(campaign)))
    assert_authorized(target)                       # ROE gate (raises if not authorized)

    items = load_campaign_corpus(campaign["corpus"])
    if category:
        items = [i for i in items if i.category == category]
    if limit:
        items = items[:limit]

    run_id = mint_run_id(campaign["id"])
    if dry_run:
        print(f"[dry-run] {len(items)} prompts across "
              f"{len({i.category for i in items})} categories against "
              f"{target.get('base_url')} — no requests sent. run_id={run_id}")
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
    # campaign references a target id; for MVP we load config/target.yml
    return campaign.get("target_config", "config/target.yml")
