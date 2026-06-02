"""airt CLI (stdlib argparse)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .core.errors import (EXIT_AUTHORIZATION, EXIT_GATE_FAIL, EXIT_INTERNAL,
                          EXIT_OK, EXIT_USAGE, AirtError, AuthorizationError)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="airt"); sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--campaign", required=True); r.add_argument("--limit", type=int)
    r.add_argument("--category"); r.add_argument("--concurrency", type=int, default=2)
    r.add_argument("--dry-run", action="store_true"); r.add_argument("--no-redact", action="store_true")
    rep = sub.add_parser("report"); rep.add_argument("--run-id", required=True); rep.add_argument("--format", default="md"); rep.add_argument("--report")
    g = sub.add_parser("gate"); g.add_argument("--run-id", required=True); g.add_argument("--baseline", required=True)
    g.add_argument("--thresholds", required=True); g.add_argument("--campaign-id", default="tmc"); g.add_argument("--json", action="store_true")
    imp = sub.add_parser("import-legacy"); imp.add_argument("--glob", required=True); imp.add_argument("--campaign-id", default="legacy")
    b = sub.add_parser("baseline-create"); b.add_argument("--run-id", required=True); b.add_argument("--out", required=True); b.add_argument("--campaign-id", default="tmc")
    rc = sub.add_parser("recon"); rc.add_argument("--target", default="config/target.yml"); rc.add_argument("--campaign-id", default="tmc")
    rc.add_argument("--n", type=int, default=50); rc.add_argument("--rpm", type=float, default=120.0)
    gt = sub.add_parser("gold-template"); gt.add_argument("--run-id", required=True); gt.add_argument("--out", required=True); gt.add_argument("--per-category", type=int, default=20)
    vj = sub.add_parser("validate-judge"); vj.add_argument("--run-id", required=True); vj.add_argument("--gold", required=True)
    for name in ("judge", "score", "export", "init"):
        sp = sub.add_parser(name); sp.add_argument("args", nargs="*")
    args = p.parse_args(argv)
    try:
        return _dispatch(args)
    except AuthorizationError as e:
        print(f"AUTHORIZATION ERROR: {e}", file=sys.stderr); return EXIT_AUTHORIZATION
    except AirtError as e:
        print(f"ERROR: {e}", file=sys.stderr); return EXIT_USAGE
    except NotImplementedError as e:
        print(f"NOT IMPLEMENTED: {e}", file=sys.stderr); return EXIT_USAGE
    except Exception as e:
        print(f"INTERNAL ERROR: {e}", file=sys.stderr); return EXIT_INTERNAL


def _dispatch(args) -> int:
    if args.cmd == "run":
        from .core.pipeline import run_campaign
        run_campaign(args.campaign, limit=args.limit, category=args.category,
                     dry_run=args.dry_run, redact=not args.no_redact, concurrency=args.concurrency)
        return EXIT_OK
    if args.cmd == "report":
        from .storage.jsonl import read_results
        from .reporting.builder import build_report
        from .reporting.render_md import render_markdown
        from .reporting.render_html import render_html
        results = read_results(args.run_id); rcfg = {}
        if args.report:
            from .config.loader import load_yaml; rcfg = load_yaml(args.report).get("report", {})
        model = build_report(results, rcfg.get("campaign_id", "tmc"), args.run_id, rcfg)
        for fmt in args.format.split(","):
            fmt = fmt.strip()
            if fmt == "md": print("wrote", render_markdown(model))
            elif fmt == "html": print("wrote", render_html(model))
            elif fmt == "pdf":
                from .reporting.render_html import render_pdf; print("wrote", render_pdf(model))
        return EXIT_OK
    if args.cmd == "gate":
        from .storage.jsonl import read_results
        from .config.loader import load_yaml
        from .gates.evaluator import evaluate_gate, gate_summary, gate_to_dict
        results = read_results(args.run_id)
        rules = load_yaml(args.thresholds).get("gate", {}).get("rules", [])
        gr = evaluate_gate(results, args.campaign_id, args.run_id, args.baseline, rules)
        print(json.dumps(gate_to_dict(gr), indent=2) if args.json else gate_summary(gr))
        return EXIT_OK if gr.passed else EXIT_GATE_FAIL
    if args.cmd == "import-legacy":
        import glob as _glob
        from .storage.legacy import import_legacy_csv
        from .storage.jsonl import write_results
        from .core.ids import mint_run_id
        from .scoring.scorer import score_result
        from .frameworks.mapper import FrameworkMapper
        paths = [Path(p) for p in sorted(_glob.glob(args.glob))] if any(c in args.glob for c in "*?[") else [Path(args.glob)]
        if not paths:
            print(f"no files matched: {args.glob}", file=sys.stderr); return EXIT_USAGE
        run_id = mint_run_id(args.campaign_id); mapper = FrameworkMapper(); all_results = []
        for pth in paths:
            for res in import_legacy_csv(pth, run_id, args.campaign_id):
                all_results.append(mapper.map_result(score_result(res)))
        write_results(run_id, all_results)
        print(f"imported {len(all_results)} rows from {len(paths)} file(s) -> run_id={run_id}")
        return EXIT_OK
    if args.cmd == "baseline-create":
        from .storage.jsonl import read_results
        from .gates.evaluator import metrics_for
        from .core.ids import now_iso
        results = read_results(args.run_id)
        baseline = {"campaign_id": args.campaign_id, "run_id": args.run_id, "created": now_iso(),
                    "metrics": metrics_for(results, args.campaign_id)}
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(baseline, indent=2), encoding="utf-8")
        print(f"baseline written -> {args.out}"); return EXIT_OK
    if args.cmd == "recon":
        from .config.loader import load_yaml
        from .config.schemas import validate_target, assert_authorized
        from .runners.recon import probe_rate_limit, recon_to_result
        from .storage.jsonl import append_result
        from .core.ids import mint_run_id
        target = validate_target(load_yaml(args.target)); assert_authorized(target)
        rl = probe_rate_limit(target, n=args.n, rpm=args.rpm)
        run_id = mint_run_id(args.campaign_id)
        res = recon_to_result(rl, run_id, args.campaign_id, target.get("id", ""))
        append_result(run_id, res)
        print(f"recon: {rl.notes} -> {res.severity} (run_id={run_id})"); return EXIT_OK
    if args.cmd == "gold-template":
        from .storage.jsonl import read_results
        from .validation.judge_eval import write_gold_template
        n = write_gold_template(read_results(args.run_id), args.out, per_category=args.per_category)
        print(f"wrote gold template with {n} rows -> {args.out} (fill in human_label)"); return EXIT_OK
    if args.cmd == "validate-judge":
        from .storage.jsonl import read_results
        from .validation.judge_eval import evaluate_judge, metrics_report
        results = read_results(args.run_id)
        judge_by_key = {r.prompt_id: (r.judge_label or "") for r in results}
        print(metrics_report(evaluate_judge(args.gold, judge_by_key, key="prompt_id"))); return EXIT_OK
    raise NotImplementedError(f"'{args.cmd}' is a stub in the MVP scaffold")


if __name__ == "__main__":
    raise SystemExit(main())
