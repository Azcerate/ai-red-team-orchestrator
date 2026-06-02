from pathlib import Path
import orchestrator


def test_framework_data_present():
    base = Path(orchestrator.__file__).parent / "frameworks"
    for f in ("owasp_llm_2025.yml", "mitre_atlas.yml", "nist_csf_2.yml"):
        assert (base / f).exists(), f"missing packaged data: {f}"


def test_init_templates_bundled():
    base = Path(orchestrator.__file__).parent / "templates"
    assert (base / "config" / "campaigns" / "example.yml").exists()
    assert (base / "corpus" / "example_canary.csv").exists()
    assert (base / "mock_target.py").exists()
