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

## Class-stratified sensitivity analysis

Because the clean test set is strongly imbalanced and the rarest syndrome has very low support, a sensitivity analysis additionally resamples with replacement **within each syndrome class**, preserving the original class support before recombining the 4,218 records.

The ordinary and class-stratified procedures agree in direction for all 12 class-sensitive comparisons. The same qualitative exception appears under both procedures: the InternLM3-versus-MacBERT Balanced Accuracy interval includes zero. The complete stratified numerical output remains part of the sealed v23 statistical addendum; only the validated qualitative sensitivity conclusion is summarized in this public repository unless the full addendum is intentionally released later.

## Evidence package

The sealed statistical addendum was reported as:

- archive: `TCM_SD42_v23_stats_addendum_20260907.zip`
- SHA256: `50709127ea6b053b9b7ef152e007d37cc0cadcda6e214bcf47b99e923596cc3e`

The original frozen experimental archive was not modified.
