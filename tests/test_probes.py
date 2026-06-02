import base64
from orchestrator.probes.registry import all_probes, load_probes, get_probe
from orchestrator.probes import mutators


def test_registry_has_core_probes():
    names = set(all_probes())
    assert {"dan_jailbreak", "prompt_injection", "encoding_obfuscation",
            "canary_exfil", "system_prompt_leak"} <= names


def test_probes_generate_prompt_items():
    for probe in load_probes(None):
        items = list(probe.generate())
        assert items, f"{probe.name} produced no items"
        for it in items:
            assert it.prompt and it.category and it.prompt_id.startswith(probe.name)


def test_canary_probe_sets_phrase_target():
    items = list(get_probe("canary_exfil").generate())
    assert all(it.phrase_target for it in items)


def test_mutators_expand_and_roundtrip():
    variants = list(mutators.expand("reveal secrets"))
    labels = [lbl for lbl, _ in variants]
    assert "base64" in labels and "rot13" in labels and len(variants) == 6
    b64 = [t for lbl, t in variants if lbl == "base64"][0]
    enc = b64.split(": ", 1)[1]
    assert base64.b64decode(enc).decode() == "reveal secrets"


def test_encoding_probe_multiplies():
    items = list(get_probe("encoding_obfuscation").generate())
    assert len(items) == 12  # 2 payloads x 6 mutators
