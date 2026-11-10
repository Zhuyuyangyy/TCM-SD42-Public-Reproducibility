# Statistical method for the v23 class-sensitive addendum

The v23 addendum uses the frozen, aligned seed-42 prediction file containing the same **4,218 held-out records** for all four systems.

## Alignment gate

Before inference, aggregate Accuracy, Macro-F1, Weighted-F1, and Balanced Accuracy were recomputed for all four models and matched the frozen seed-42 results exactly. The six previously reported accuracy-difference bootstrap intervals were also reproduced to four decimal places. This gate was used to verify that the paired rows were aligned correctly.

## Ordinary paired bootstrap

For each of the six model pairs, the addendum computes paired uncertainty for:

- Macro-F1 difference, and
- Balanced Accuracy difference.

Parameters:

- 2,000 bootstrap resamples;
- random seed `20260516`;
- the same resampled record indices applied simultaneously to gold labels and both model prediction vectors;
- the frozen 42-label order used for every resample;
- difference defined as `first_model - second_model`;
- 95% percentile confidence intervals from the empirical bootstrap distribution.

These confidence intervals are class-sensitive paired uncertainty summaries. The multiplicity-controlled inferential test in the original analysis remains the exact two-sided McNemar test with Holm correction for the six pairwise **accuracy** comparisons.

### Historical ordinary Balanced Accuracy implementation and completed re-verification

The historical NumPy fast path averaged recall over the union of classes appearing in the resampled gold and prediction vectors. Prediction-only classes therefore entered the denominator as zero-recall categories. This differs from scikit-learn balanced_accuracy_score, which averages over classes present in y_true and excludes zero-support prediction-only rows.

The corrected gold-present implementation is on the PR #4 review branch. On 2026-11-10, it was checked against the authorized aligned seed-42 predictions (N = 4,218) and the ordinary paired bootstrap was rerun with 2,000 resamples and seed 20260516. The hardened parity check compared the corrected fast path with scikit-learn for all 2,000 resamples × four models: 8,000/8,000 comparisons passed, with maximum absolute difference 0. The historical union implementation separately reproduced the archived six-pair confidence intervals (G4, 6/6).

Only one of the six corrected ordinary-bootstrap BA intervals changed at four-decimal precision: the ZY-BERT-versus-InternLM3 upper endpoint changed from 0.0786 to 0.0787 (7.86 to 7.87 percentage points). The other 11 endpoints are unchanged, and no zero-exclusion verdict changed: five intervals exclude zero; the InternLM3-versus-MacBERT interval remains the only interval containing zero. Full-test-set BA point estimates, Macro-F1 intervals, and class-stratified BA intervals are unaffected.

The corrected aggregate output and full audit are in the [2026-11-10 BA re-verification audit](../audits/20261110_ba_reverification/README.md). The aligned six-field case-level prediction input is intentionally not distributed; the audit records its SHA-256 for provenance, and reproduction requires the authorized input in a controlled local environment. The historical aggregate CSV is preserved unchanged; the corrected output is a separate file in the audit directory. PR #4 is still open and unmerged, so this completed author-side re-verification is recorded on the review branch and has not yet changed public main.

## Class-stratified sensitivity analysis

Because the clean test set is strongly imbalanced and the rarest syndrome has very low support, a sensitivity analysis additionally resamples with replacement **within each syndrome class**, preserving the original class support before recombining the 4,218 records.

The ordinary and class-stratified procedures agree in direction for all 12 class-sensitive comparisons. The same qualitative exception appears under both procedures: the InternLM3-versus-MacBERT Balanced Accuracy interval includes zero. The complete stratified numerical output is published in `results/pairwise_class_sensitive_stratified_bootstrap_seed42.csv`; the aligned case-level input remains excluded.

## Evidence package

The sealed statistical addendum was reported as:

- archive: `TCM_SD42_v23_stats_addendum_20260907.zip`
- SHA256: `50709127ea6b053b9b7ef152e007d37cc0cadcda6e214bcf47b99e923596cc3e`

The original frozen experimental archive was not modified.

Portable source files are available in `code/pairwise_class_sensitive_bootstrap.py` and `code/verify_four_model_alignment.py`. They require an authorized local aligned input and do not assume the historical private server paths.


## Deduplication sensitivity (2026-10-22)

A post hoc record-level sensitivity analysis retained the minimum numeric ID suffix within each group. The primary set has n=4,218; S1 raw exact-text identity has n=4,206; and S2 has n=4,195 under Unicode NFKC, deletion of consecutive digit runs, and removal of punctuation, symbols, control characters and whitespace. Direct comparison against the archived count anchors supports digit deletion; the legacy sentinel mode does not reproduce the full-pool and clean-subset counts. S2 is an aggressive normalization stress test, not adjudicated semantic or patient-level deduplication: 9 groups exist only because numeric content differs and is deleted, including the only discordant-label group. The largest accuracy change is 0.0849 percentage points (0.085 pp rounded; conservatively ≤0.09 pp).

The aggregate pairwise cells and exact McNemar/Holm results are in `results/dedup_sensitivity_seed42.csv`; the computation script is `code/recompute_pairwise_stats.py`. The script requires an authorized local evidence tree containing the private aligned inputs and does not make those inputs public. The analysis is sensitivity evidence, not a replacement for the original primary analysis. Because repeated text can induce dependence, record-level bootstrap and McNemar inference do not account for all dependence among duplicate records.

## Bootstrap implementation note

`code/pairwise_stats.py` uses the archived choices-based, with-replacement index generator. The earlier public randrange-based implementation was also with-replacement but consumed the random-number stream differently, so its interval endpoints did not exactly reproduce the archived results.


## Implementation correction status

The corrected gold-present fast path, regression tests, and completed authorized-data re-verification are recorded on PR #4. The PR remains open and unmerged; `main` therefore retains the historical aggregate table. See **Historical ordinary Balanced Accuracy implementation and completed re-verification** above and the dated audit package for the corrected aggregate output and rerun instructions.
