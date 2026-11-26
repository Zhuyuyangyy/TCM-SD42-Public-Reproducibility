# Authoritative vs. Historical Bootstrap Tables (`results/`)

To preserve audit traceability while preventing accidental reuse of pre-correction numbers, the files in `results/` and `audits/` have distinct provenance roles:

## Authoritative publication-facing sources
- **`audits/20261110_ba_reverification/results/pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv`**: authoritative ordinary paired-bootstrap 95% CIs for Balanced Accuracy (`[0.0361, 0.0787]` for ZY-BERT vs InternLM3-8B) and unrounded full-sample differences rounded to 4 decimal places (`+5.77`, `+6.70`, `+10.59`, `+0.93`, `+4.82`, `+3.90` pp). Note on column naming: the historical 2026-11-10 audit table retains the column name `diff_obs_full_precision` for its 4-decimal unrounded-difference values (`0.0577`, `0.0670`, `0.1059`, `0.0093`, `0.0482`, `0.0390`), distinguishing them from `diff_obs` (`0.0669`, `0.0092`) computed from pre-rounded 4dp summary values, rather than storing full IEEE-754 floating-point precision.
- **`results/pairwise_macro_f1_bootstrap_seed42.csv`**: authoritative ordinary paired-bootstrap 95% CIs and observed differences for Macro-F1.
- **`results/pairwise_class_sensitive_stratified_bootstrap_seed42.csv`**: authoritative class-stratified paired-bootstrap 95% CIs, synchronized with the corrected `ordinary_ci_upper = 0.0787`, `diff_obs_unrounded_4dp` (`0.0670`, `0.0093`, etc.), and true 16-digit full-precision floating-point differences (`diff_obs_full_precision`, e.g., `0.0669567683389108` and `0.0092578040986868` for Balanced Accuracy) recomputed directly from the frozen 42x42 confusion matrices.

## Historical pre-reverification archive files (NOT authoritative for ordinary BA)
- **`results/pairwise_balanced_accuracy_bootstrap_seed42.csv`**: retained unchanged from the historical 2026-05 union-denominator fast path (`ci_upper = 0.0786` for ZY-BERT vs InternLM3-8B). Do not cite as the final ordinary BA CI.
- **`results/pairwise_class_sensitive_bootstrap_seed42.csv`**: retained unchanged from the historical combined export; its Macro-F1 intervals match `pairwise_macro_f1_bootstrap_seed42.csv`, while its Balanced Accuracy rows retain legacy `0.0786`, `0.0669`, and `0.0092`. Use `pairwise_macro_f1_bootstrap_seed42.csv` for Macro-F1 and `pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv` for ordinary Balanced Accuracy.
