"""Judge validation: compare judge labels to a human-labeled gold set.

Gold CSV columns: result_id (or prompt_id), human_label (success|fail|partial).
Computes confusion matrix, precision, recall, F1, and Cohen's kappa.
Pure stdlib.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JudgeMetrics:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return (2 * p * r / (p + r)) if (p + r) else 0.0

    @property
    def kappa(self) -> float:
        n = self.tp + self.fp + self.fn + self.tn
        if n == 0:
            return 0.0
        po = (self.tp + self.tn) / n
        p_yes = ((self.tp + self.fp) / n) * ((self.tp + self.fn) / n)
        p_no = ((self.fn + self.tn) / n) * ((self.fp + self.tn) / n)
        pe = p_yes + p_no
        return (po - pe) / (1 - pe) if (1 - pe) else 0.0


def _is_success(label: str) -> bool:
    return label.strip().lower() == "success"


def evaluate_judge(gold_csv: str, judge_by_key: dict[str, str], key: str = "result_id") -> JudgeMetrics:
    """judge_by_key: {result_id_or_prompt_id: judge_label}."""
    m = JudgeMetrics()
    with Path(gold_csv).open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = row.get(key) or row.get("prompt_id")
            if k is None or k not in judge_by_key:
                continue
            human = _is_success(row["human_label"])
            machine = _is_success(judge_by_key[k])
            if machine and human:
                m.tp += 1
            elif machine and not human:
                m.fp += 1
            elif not machine and human:
                m.fn += 1
            else:
                m.tn += 1
    return m


def metrics_report(m: JudgeMetrics) -> str:
    return (f"Judge validation: precision={m.precision:.2f} recall={m.recall:.2f} "
            f"F1={m.f1:.2f} kappa={m.kappa:.2f} "
            f"(TP={m.tp} FP={m.fp} FN={m.fn} TN={m.tn})")


def write_gold_template(results, out_path, per_category=20):
    from collections import defaultdict
    from pathlib import Path as _P
    import csv as _csv
    by=defaultdict(list)
    for r in results: by[r.category].append(r)
    rows=[]
    for cat,items in by.items():
        items=sorted(items,key=lambda r:(0 if r.review_status=="needs_review" else 1, abs((r.judge_confidence or 0)-0.5)))
        for r in items[:per_category]:
            rows.append({"prompt_id":r.prompt_id,"category":r.category,"judge_label":r.judge_label or "",
                "judge_confidence":r.judge_confidence if r.judge_confidence is not None else "",
                "response_excerpt":(r.response_text or "")[:160].replace("\n"," "),"human_label":""})
    p=_P(out_path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=_csv.DictWriter(f,fieldnames=["prompt_id","category","judge_label","judge_confidence","response_excerpt","human_label"])
        w.writeheader(); w.writerows(rows)
    return len(rows)
