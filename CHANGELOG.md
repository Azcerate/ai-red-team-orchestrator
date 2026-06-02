# Changelog

## 0.2.0
- Probe engine: code-based probes + mutators (`airt probes list`, `airt run --probes`).
- 11 starter probes across jailbreak, injection, RAG/canary, IDOR/RBAC, agency, etc.
- Entry-point plugin discovery (`airt.probes`) for third-party probe packages.
- Real-provider targets: templated body + dotted response path; OpenAI/Anthropic/Ollama presets.
- `airt import-garak` to ingest NVIDIA garak reports.
- GitHub Action (`action.yml`), Dockerfile, PyPI-ready packaging.
- Judge-validation docs; report-card hero image.

## 0.1.0
- Initial release: runner, ensemble judge (Ollama/Anthropic/OpenAI), scoring,
  OWASP/MITRE/NIST mapping, client-grade reports, regression gate, judge validation,
  legacy CSV import.
