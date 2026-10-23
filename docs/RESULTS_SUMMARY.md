# Results summary

## Seed-42 primary comparison (clean N=4,218)

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced Acc. | Accuracy 95% CI |
|---|---:|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% | [74.47, 77.05] |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% | [68.23, 70.93] |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% | [61.24, 64.20] |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% | [57.23, 60.19] |

## Three-seed robustness

- ZY-BERT accuracy: **74.92 ± 1.13%**
- ZY-BERT Macro-F1: **66.06 ± 0.66%**
- InternLM3-8B accuracy: **69.42 ± 0.21%**
- InternLM3-8B Macro-F1: **60.89 ± 0.31%**

Mean accuracy gap (ZY-BERT minus InternLM3-8B): approximately **5.50 percentage points**.

## Pairwise accuracy inference

All six seed-42 pairwise accuracy comparisons remain statistically significant after Holm correction. Exact values are in `results/pairwise_significance_seed42.csv`.

## Pairwise Macro-F1 bootstrap (ordinary paired bootstrap; 2,000 resamples; seed 20260516)

| Comparison | Difference (first - second) | 95% CI |
|---|---:|---:|
| ZY-BERT vs InternLM3 | +0.0577 | [0.0427, 0.0737] |
| ZY-BERT vs MacBERT | +0.0970 | [0.0812, 0.1136] |
| ZY-BERT vs Qwen3 | +0.1201 | [0.1042, 0.1357] |
| InternLM3 vs MacBERT | +0.0393 | [0.0226, 0.0557] |
| InternLM3 vs Qwen3 | +0.0624 | [0.0484, 0.0774] |
| MacBERT vs Qwen3 | +0.0231 | [0.0052, 0.0410] |

All six Macro-F1 intervals exclude zero.

## Pairwise Balanced Accuracy bootstrap

| Comparison | Difference (first - second) | 95% CI |
|---|---:|---:|
| ZY-BERT vs InternLM3 | +0.0577 | [0.0361, 0.0786] |
| ZY-BERT vs MacBERT | +0.0669 | [0.0452, 0.0894] |
| ZY-BERT vs Qwen3 | +0.1059 | [0.0847, 0.1276] |
| InternLM3 vs MacBERT | +0.0092 | [-0.0146, 0.0331] |
| InternLM3 vs Qwen3 | +0.0482 | [0.0289, 0.0678] |
| MacBERT vs Qwen3 | +0.0390 | [0.0145, 0.0636] |

Five of six Balanced Accuracy intervals exclude zero. The InternLM3-versus-MacBERT interval includes zero, so this analysis does not support a class-balanced recall advantage for InternLM3 over MacBERT despite InternLM3's higher point estimate.

## Sensitivity analysis

A class-stratified paired-bootstrap analysis preserved the direction of all 12 class-sensitive comparisons. The same qualitative exception remained for InternLM3 versus MacBERT Balanced Accuracy: its interval included zero under both ordinary and class-stratified resampling.

## Interpretation boundary

These results support a system-level advantage for ZY-BERT **within this fixed TCM-SD-derived 42-class setting**. They do not establish that encoder models universally outperform LLMs, and they should not be represented as a complete evaluation on the official normalized 148-class TCM-SD benchmark.


## Deduplication sensitivity (2026-10-22)

The primary results above remain the frozen 4,218-record record-level analysis. A separate aggregate sensitivity table rescored the same predictions after retaining the record with the smallest numeric ID suffix within exact-text groups (n=4,206) and normalized-text groups (n=4,195). The largest reported Accuracy change was approximately 0.085 percentage points. The normalized-text subset applies Unicode NFKC, replaces consecutive digit runs with `#`, then removes punctuation, symbols, control characters and whitespace while preserving `#`; it is a string-normalization stress test, not expert-adjudicated semantic deduplication. See `results/dedup_sensitivity_seed42.csv` and `docs/DATA_QUALITY_SUMMARY.md`. Case-level inputs are private and are not included in this repository.


## Source-split label-selection reconstruction (2026-10-23)

A read-only reconstruction on the official public source splits found 278 distinct raw `syndrome` strings in Train, 282 in the raw union across train/dev/test, and 278 after removing a trailing `证`. The thresholds train>=100, dev>=10, test>=10 select 43 eligible raw strings; canonicalization merges two into the frozen 42-label vocabulary. The cap-before-canonicalization reconstruction gives 19,352 / 4,902 / 4,912. Retained duplicate counts reconcile Dev and Test to 4,411 and 4,452 (453 Dev/Train, 460 Test/Train, and 38 additional Dev/Test removals). The 227-record Train difference remains under targeted review: the revised source-split script compares cap-before-canonicalization and canonicalization-before-cap and checks per-class Train support against the frozen CSV. The original post-processing/deduplication implementation is missing, so no historical operation order is asserted until the per-class comparison is complete. The internal summary's `raw_label_count=278` field is ambiguous about which counting stage it represents.

## Targeted historical checks

MacBERT frozen-prediction metrics were recomputed from the authorized 4,452-row prediction file after 8/8 structural alignment checks: Accuracy 62.778568%, Macro-F1 56.811275%, Weighted-F1 63.944848%, Balanced Accuracy 72.628728% (n=4,218; 2,648 correct). This verifies metrics from frozen predictions, not the missing original fine-tuned checkpoint. The early pilot archive contains the historical TCM-Mini-best Qwen3 adapter and its checksum-matching raw-output artifact. This confirms those early artifacts are preserved, but the original inference command/input hashes are missing and the two Stage-2 epoch adapters needed for a saved-state epoch comparison were not found in the latest server audit, so that comparison remains blocked. The Seed-7 continuation stdout was recovered and hash-verified; it supports a batch-8 continuation that skipped 739 rows and generated 3,479, but does not establish the provenance of the first 739 rows.
