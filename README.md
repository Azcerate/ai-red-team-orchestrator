# airt — AI Red Team Orchestrator & Compliance Report Generator

Test LLM chatbots, RAG assistants, and AI features for prompt injection, jailbreaks,
data leakage, RAG/canary exfiltration, excessive agency, unsafe output, context overflow,
and rate-limit weakness — then emit an **OWASP LLM Top 10 (2025) / MITRE ATLAS / NIST CSF 2.0**
mapped report and a **CI regression gate**.

> ⚠️ **Authorized, defensive testing only.** See [ETHICAL_USE.md](ETHICAL_USE.md). `airt run`
> refuses any target not marked `authorized: true` in its config.

## Why
Teams ship LLM features faster than they can test them, and generic scanners don't understand
LLM-specific failure modes. `airt` is the engineering + reporting layer around an attack corpus:
campaign orchestration, a **validated** LLM-as-judge (with a deterministic canary check that
overrides it), standardized scoring, redacted evidence, framework mapping, professional reports,
and a regression gate for CI.

## Features
- **Pluggable judge:** local `ollama` (default) or hosted `anthropic` / `openai` (no GPU needed).
- **Two-stage detection:** deterministic phrase/canary check + LLM judge; canary hits are ground truth.
- **Defensible scoring:** ASR with explicit denominators; low-confidence findings are capped, not inflated.
- **Framework mapping:** OWASP LLM 2025, MITRE ATLAS, NIST CSF 2.0.
- **Client-grade reports:** Markdown + HTML (+ PDF via WeasyPrint).
- **Regression gate:** baseline diff + thresholds + CI exit codes.
- **Judge validation:** gold-set workflow → precision / recall / F1 / Cohen's κ.

## Install
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"        # runtime: requests, pyyaml; dev: pytest
pytest -q                      # 13 tests
```

## Quickstart (offline demo, no external services)
```bash
# 1. start the bundled mock target (separate terminal)
python tests/mock_stdlib_target.py
# 2. run a campaign against it (canary category uses the deterministic judge)
airt run --campaign config/campaigns/example.yml
# 3. generate a report
airt report --run-id <RUN_ID> --format md,html --report config/report.yml
# 4. baseline + CI gate
airt baseline-create --run-id <RUN_ID> --out baselines/example.json --campaign-id example
airt gate --run-id <RUN_ID> --baseline baselines/example.json --thresholds config/gate.yml --campaign-id example
```

## Hosted judge (client engagements, no GPU)
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # or OPENAI_API_KEY
# set provider: anthropic  in config/judge.yml
```

## CLI
`run · report · gate · recon · import-legacy · baseline-create · gold-template · validate-judge`
Exit codes: `0` ok · `1` gate fail · `2` usage/config · `3` authorization · `4` internal.

## Architecture
```
orchestrator/  core · config · corpus · runners · judges · scoring ·
               frameworks · evidence · reporting · gates · validation · storage · cli.py
config/   target/campaign/judge/scoring/gate/report YAML
corpus/   id,technique,prompt CSVs   (category set per-campaign; technique doubles as canary phrase)
```

## License
MIT — see [LICENSE](LICENSE). Built by Anthony N. Saunders (MSCS, CISM, CISA).
