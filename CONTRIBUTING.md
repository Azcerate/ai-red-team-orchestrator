# Contributing to airt

Thanks for helping make AI systems safer. airt is for **authorized, defensive**
testing only — see [ETHICAL_USE.md](ETHICAL_USE.md).

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Adding a probe (in-tree)
Subclass `Probe`, set `name`/`category`/`attack_type`/`description`, implement
`generate()`, and decorate with `@register` in `orchestrator/probes/library.py`.
Set `phrase_target` on items when detection can be deterministic (canary/marker).
Run `airt probes list` to confirm it registers. Add a test in `tests/test_probes.py`.

## Publishing a probe as a plugin (out-of-tree)
Ship a package that exposes a `Probe` subclass and declares an entry point:
```toml
# your package's pyproject.toml
[project.entry-points."airt.probes"]
my_probe = "my_pkg.module:MyProbe"
```
After `pip install your-package`, `airt probes list` will include it automatically.

## Categories
Use an existing airt category where possible so findings map to OWASP/MITRE/NIST.
To add a new category, update `frameworks/*.yml`, `scoring/scorer.py`
(`CATEGORY_WEIGHT`), and `scoring/aggregate.py` (`CATEGORY_CODE`).

## PRs
- Keep changes focused; add/adjust tests; `pytest` must pass.
- No real secrets, client data, or live exploit payloads in the repo.
- Conventional commit messages appreciated (`feat:`, `fix:`, `docs:`).
