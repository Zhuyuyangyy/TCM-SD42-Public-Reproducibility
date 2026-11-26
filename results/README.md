# `results/` Guide: Authoritative vs. Historical Files and Matrix Denominators

> [!CAUTION]
> **Do NOT use historical pre-reverification files in this directory for publication numbers:**
> - `pairwise_balanced_accuracy_bootstrap_seed42.csv` (legacy 2026-05 union-denominator ordinary BA: `0.0786`, unrounded float in `diff_obs`)
> - `pairwise_class_sensitive_bootstrap_seed42.csv` (legacy combined export retaining `0.0786`, `0.0669`, `0.0092`)
>
> Both files remain in `results/` solely for audit traceability. Use the authoritative files listed in [`AUTHORITATIVE_VS_HISTORICAL.md`](AUTHORITATIVE_VS_HISTORICAL.md) below.

## Authoritative derived files
- **Ordinary Balanced Accuracy 95% CIs**: [`../audits/20261110_ba_reverification/results/pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv`](../audits/20261110_ba_reverification/results/pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv) (contains `ordinary_ci_upper = 0.0787` and 4-decimal unrounded-metric differences under `diff_obs_full_precision`: `0.0577`, `0.0670`, `0.1059`, `0.0093`, `0.0482`, `0.0390`).
- **Ordinary Macro-F1 95% CIs**: [`pairwise_macro_f1_bootstrap_seed42.csv`](pairwise_macro_f1_bootstrap_seed42.csv).
- **Class-stratified 95% CIs & full-precision observed diffs**: [`pairwise_class_sensitive_stratified_bootstrap_seed42.csv`](pairwise_class_sensitive_stratified_bootstrap_seed42.csv) (includes synced `ordinary_ci_upper = 0.0787`, `diff_obs_unrounded_4dp`, and 16-digit matrix-derived floating-point `diff_obs_full_precision`).

## Why `confusion_matrix_internlm3.csv` and `confusion_matrix_qwen3.csv` sum to 4,216 (while primary `N = 4,218`)
The four 42x42 confusion matrices contain only **valid class-valued predictions** (`4,218` for ZY-BERT and MacBERT; `4,216` each for InternLM3-8B and Qwen3-8B). Two `empty` (unparsed) outputs per generative model are omitted from the 42x42 grid but counted as incorrect against the full `N = 4,218` evaluation denominator in [`clean4218_seed42.csv`](clean4218_seed42.csv) and `code/verify_public_aggregates.py`. Dividing diagonal sums by `4,216` instead of `4,218` yields valid-output-only accuracy (`69.6157%` for InternLM3-8B and `58.7287%` for Qwen3-8B) rather than the primary full-denominator accuracy (`69.5827%` -> `69.58%` and `58.7008%` -> `58.70%`).
