# Publishing airt to PyPI

Package name: **`airt-llm`** (import name stays `orchestrator`; CLI is `airt`).
Bump `version` in `pyproject.toml` for every release.

## 0. One-time: confirm the name is free
Check https://pypi.org/project/airt-llm/ — if it exists, pick another name in
`pyproject.toml` (e.g. `airt-redteam`) and update the README badges/links.

## Option A — Automated via GitHub Release + Trusted Publishing (recommended)
No API tokens to manage; PyPI trusts your repo via OIDC.

1. Create the PyPI project's trusted publisher (one time):
   PyPI → your account → **Publishing** → **Add a pending publisher**:
   - PyPI project name: `airt-llm`
   - Owner: `Azcerate`  · Repository: `ai-red-team-orchestrator`
   - Workflow name: `publish.yml`  · Environment: (leave blank)
2. Tag and release:
   ```bash
   git tag v0.2.0 && git push origin v0.2.0
   ```
   Then on GitHub: **Releases → Draft a new release → choose tag v0.2.0 → Publish**.
   The `publish.yml` workflow builds and uploads automatically.
3. Verify: `pip install airt-llm` in a clean venv.

## Option B — Manual local upload
```bash
python -m pip install --upgrade build twine
python -m build                      # creates dist/*.whl and dist/*.tar.gz
twine check dist/*                    # metadata sanity
# test first on TestPyPI:
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple airt-llm
# then the real thing:
twine upload dist/*
```
Use a PyPI API token as the password (username `__token__`).

## Post-publish smoke test (clean venv)
```bash
python -m venv /tmp/airt-test && source /tmp/airt-test/bin/activate
pip install airt-llm
airt init                            # scaffolds config/ + corpus/ + mock_target.py
python mock_target.py &              # offline demo target
airt run --campaign config/campaigns/example.yml
airt report --run-id <RUN_ID> --format md,html --report config/report.yml
```

## Notes
- Package data (`orchestrator/frameworks/*.yml`, `orchestrator/templates/**`) is declared
  in `pyproject.toml` so framework mappings and `airt init` templates ship in the wheel.
- Versions are immutable on PyPI — you can't re-upload the same version; bump it.
