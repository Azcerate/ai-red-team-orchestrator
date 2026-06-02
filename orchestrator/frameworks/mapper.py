"""Map a result's category to OWASP/MITRE/NIST framework references."""
from __future__ import annotations

from pathlib import Path

from ..core.models import TestResult

_FW_DIR = Path(__file__).parent


def _load_yaml(name: str) -> dict:
    import yaml  # lazy so package imports without pyyaml
    with (_FW_DIR / name).open("r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("mappings", {})


class FrameworkMapper:
    def __init__(self):
        self.owasp = _load_yaml("owasp_llm_2025.yml")
        self.atlas = _load_yaml("mitre_atlas.yml")
        self.nist = _load_yaml("nist_csf_2.yml")

    def refs_for(self, category: str) -> list[dict]:
        refs: list[dict] = []
        o = self.owasp.get(category)
        if o:
            if o.get("primary"):
                refs.append({"framework": "owasp_llm_2025", **o["primary"]})
            if o.get("secondary"):
                refs.append({"framework": "owasp_llm_2025", **o["secondary"]})
        a = self.atlas.get(category)
        if a:
            refs.append({"framework": "mitre_atlas", **a})
        n = self.nist.get(category)
        if n:
            refs.append({"framework": "nist_csf_2", **n})
        return refs

    def remediation_for(self, category: str) -> str:
        return (self.owasp.get(category) or {}).get("remediation", "")

    def map_result(self, r: TestResult) -> TestResult:
        r.framework_refs = self.refs_for(r.category)
        return r
