# Usage Guide

A practical walkthrough of airt — from install to a validated, framework-mapped report
and a CI gate.

> The CLI is `airt`. If `airt` isn't on your PATH after install, use the equivalent
> module form anywhere: `python -m orchestrator.cli <command> ...`.

> ⚠️ **Authorized, defensive testing only.** Run only against systems you own or are
> explicitly authorized to test. `airt run` refuses targets not marked `authorized: true`.

---

## 1. Install
```bash
pip install airt-llm
airt init                 # scaffolds config/, corpus/, and mock_target.py into the current dir
```
From source (development):
```bash
git clone https://github.com/Azcerate/ai-red-team-orchestrator && cd ai-red-team-orchestrator
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]" && pytest
```

## 2. Offline demo (no API key)
Start the bundled mock target in one terminal:
```bash
python mock_target.py
```
In another terminal:
```bash
airt run --campaign config/campaigns/example.yml
# copy the printed run_id, then:
airt report --run-id <RUN_ID> --format md,html --report config/report.yml
airt baseline-create --run-id <RUN_ID> --out baselines/example.json --campaign-id example
airt gate --run-id <RUN_ID> --baseline baselines/example.json --thresholds config/gate.yml --campaign-id example
```
Expected: a Critical canary finding and `GATE: FAIL` (exit code 1).

## 3. Run against a real target
Point a campaign's `target_config` at a provider preset in `config/targets/`
(OpenAI, Anthropic, Ollama, or generic). Set the API key and authorize the target:
```bash
export OPENAI_API_KEY=sk-...        # or ANTHROPIC_API_KEY; Ollama needs no key
# in the preset, set: authorized: true   (only with permission to test it)
airt run --campaign config/campaigns/<your>.yml --limit 10
airt report --run-id <RUN_ID> --format md,html,pdf --report config/report.yml
```
Any JSON HTTP API works via `body_template` (with `{{PROMPT}}`) + dotted `response_path`
(e.g. `choices.0.message.content`).

## 4. Probes
```bash
airt probes list                                   # 11 built-in probes
airt run --campaign config/campaigns/example.yml --probes dan_jailbreak,prompt_injection,rag_fishing
```
Add your own by subclassing `Probe` and `@register` in `orchestrator/probes/library.py`,
or ship a plugin package exposing a `Probe` under the `airt.probes` entry point
(see [CONTRIBUTING](../CONTRIBUTING.md)).

## 5. Validate the judge (turn reliability into a number)
```bash
# 1. produce results (live run, or import existing data)
airt import-legacy --glob "path/to/*_results_*.csv" --campaign-id myrun   # -> RUN_ID
# or: airt import-garak --report garak.report.jsonl --campaign-id garak
# 2. export a labeling sheet (includes prompt + response excerpts)
airt gold-template --run-id <RUN_ID> --out gold/myrun.csv --per-category 25
# 3. fill the human_label column by hand: success | fail | partial
# 4. measure
airt validate-judge --run-id <RUN_ID> --gold gold/myrun.csv
# -> precision / recall / F1 / Cohen's kappa
```
See [judge-validation.md](judge-validation.md) for labeling guidance. Don't describe the
judge as "validated" until you've actually run this against a gold set you labeled.

## 6. CI gate (GitHub Action)
```yaml
- uses: Azcerate/ai-red-team-orchestrator@main
  with:
    campaign: config/campaigns/example.yml
    baseline: baselines/example.json
    thresholds: config/gate.yml
    campaign-id: example
```

## 7. Interop & comparison
- Ingest NVIDIA garak: `airt import-garak --report <file>.report.jsonl`
- How airt compares to garak / PyRIT / promptfoo: [comparison.md](comparison.md)

## Command reference
`run · probes · report · gate · recon · import-legacy · import-garak · baseline-create · gold-template · validate-judge · init`
Exit codes: `0` ok · `1` gate fail · `2` usage/config · `3` authorization · `4` internal.
