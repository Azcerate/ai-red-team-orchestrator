# Judge Validation

airt's findings depend on a two-stage detector: a **deterministic phrase/canary
check** (ground truth when it fires) and an **LLM-as-judge** for semantic cases.
Because the LLM judge is probabilistic, airt makes its reliability **measurable**
instead of asking you to trust it.

## Why it matters
A red-team report is only as credible as its detector. If you can hand a buyer or
auditor precision/recall on a human-labeled sample, you move from "an AI said so"
to "a validated methodology." This is a core differentiator vs. tools that report
detector hits without measuring detector quality.

## Workflow
1. Run a campaign and produce results.
2. Export a stratified labeling sheet (oversamples low-confidence cases):
   ```bash
   airt gold-template --run-id <RUN_ID> --out gold/<name>.csv --per-category 20
   ```
3. A human fills the `human_label` column (`success` / `fail` / `partial`).
4. Score the judge against the gold set:
   ```bash
   airt validate-judge --run-id <RUN_ID> --gold gold/<name>.csv
   # -> precision, recall, F1, Cohen's kappa, confusion matrix
   ```

## Metrics reported
- **Precision** — of findings the judge flagged, how many were real (low = noisy reports).
- **Recall** — of real issues, how many the judge caught (low = missed attacks).
- **F1** — harmonic mean of the two.
- **Cohen's κ** — agreement beyond chance (κ > 0.6 substantial, > 0.8 near-expert).

## Produce real numbers from your own data
Generate genuine metrics from any run (including imported legacy/garak results):
```bash
airt import-legacy --glob "path/to/*_results_*.csv" --campaign-id tmc   # -> RUN_ID
airt gold-template --run-id <RUN_ID> --out gold/tmc.csv --per-category 25
# fill the human_label column by hand (success | fail | partial), then:
airt validate-judge --run-id <RUN_ID> --gold gold/tmc.csv
```

## Reporting guidance
Quote **your measured** figures in the report methodology. Example *format only* —
the numbers below are illustrative placeholders, not airt's measured results; replace
them with your real `validate-judge` output:
> "The automated judge was validated on an N-sample human-labeled gold set
> (stratified by category and confidence): precision X.XX, recall X.XX, F1 X.XX,
> κ X.XX. Findings below 0.70 confidence were manually reviewed."

> ⚠️ Don't describe the judge as "validated" until you've actually run `validate-judge`
> against a gold set you labeled. Until then, call it a *workflow*.

## Calibration
Bucket results by judge confidence and check that, e.g., "0.9 confidence" is right
~90% of the time. Adjust `min_confidence_for_success` in `config/judge.yml` from
real data, and route the `needs_review` band to human sign-off before findings hit
the report at full severity.
