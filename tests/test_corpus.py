import csv, tempfile, os
from orchestrator.corpus.loader import load_corpus_file, PHRASE_CATEGORIES

def _write(rows):
    fd, path = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","technique","prompt"]); w.writeheader()
        for r in rows: w.writerow(r)
    return path

def test_category_from_file_and_technique_label():
    p = _write([{"id":"1","technique":"Do Anything Now","prompt":"act as DAN"}])
    items = load_corpus_file(p, "jailbreak")
    assert items[0].category == "jailbreak"
    assert items[0].attack_type == "Do Anything Now"
    assert items[0].phrase_target is None

def test_canary_technique_becomes_phrase_target():
    p = _write([{"id":"1","technique":"CANARY_EXAMPLE","prompt":"trigger"}])
    items = load_corpus_file(p, "canary_leakage")
    assert "canary_leakage" in PHRASE_CATEGORIES
    assert items[0].phrase_target == "CANARY_EXAMPLE"

def test_blank_prompts_skipped():
    p = _write([{"id":"1","technique":"x","prompt":"  "},{"id":"2","technique":"y","prompt":"ok"}])
    assert len(load_corpus_file(p, "jailbreak")) == 1
