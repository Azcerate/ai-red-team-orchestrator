# How airt compares

There are several strong LLM red-teaming tools. **airt isn't trying to replace them on
attack breadth** — it's the *compliance + evidence + CI-gate layer*, and it can ingest
their output. Use the right tool (or combine them).

## Honest summary
- **garak (NVIDIA)** — the broadest open *scanner*: 150+ probes, 3,000+ prompts, per-probe detectors, JSONL output. Best raw attack coverage. airt can **ingest garak** reports.
- **PyRIT (Microsoft)** — a powerful *framework* for multi-turn / orchestrated attacks (Crescendo, TAP), converters, memory/chain-of-custody. Most flexible; requires scripting expertise.
- **promptfoo** — developer-friendly, app-aware attack generation (50+ vuln types), CI gates, and a polished web UI. Excellent for dev-facing eval/CI.
- **airt** — focused on **auditor-ready, framework-mapped evidence**: OWASP LLM 2025 + MITRE ATLAS + NIST CSF, a **judge-validation workflow** (label a gold set → precision/recall/F1/κ), a regression gate, a code-based probe engine, and ingestion of other tools' output.

## Feature view (as of mid-2026; verify current docs)
| | garak | PyRIT | promptfoo | **airt** |
|---|---|---|---|---|
| Backed by | NVIDIA | Microsoft | Promptfoo | community |
| Attack breadth | ★★★ (150+ probes) | ★★★ (orchestrated/multi-turn) | ★★★ (50+ vuln types) | ★★ (11 probes + mutators) |
| Multi-turn orchestration | partial | ★★★ | partial | roadmap |
| CI gate | DIY | DIY | ★★ | ★★ (baseline + thresholds + exit codes) |
| Reporting | JSONL | memory/SQL log | dev UI, pass/fail | **exec + technical + GRC** (MD/HTML/PDF) |
| OWASP/MITRE/NIST mapping | partial taxonomy | no | partial | **★★ built-in** |
| Judge validation (precision/recall/F1/κ) | no | no | no | **★★ gold-set workflow** |
| Ingests other tools | — | — | — | **garak (PyRIT/promptfoo roadmap)** |
| Footprint | medium | heavy | medium | **light (stdlib core)** |

★ ratings are this project's honest read, not a benchmark. Corrections welcome via PR.

## When to use which
- Need maximum attack coverage fast → **garak** (then `airt import-garak` for the report + gate).
- Need sophisticated multi-turn/orchestrated attacks → **PyRIT**.
- Need developer-facing eval + CI with a UI → **promptfoo**.
- Need an **auditor/CISO-ready, framework-mapped report and a release-blocking gate**, or want to
  unify several tools' findings into one compliance artifact → **airt**.

These are complementary. A strong program might run garak/PyRIT for breadth and **airt for the
evidence layer and the CI gate**.
