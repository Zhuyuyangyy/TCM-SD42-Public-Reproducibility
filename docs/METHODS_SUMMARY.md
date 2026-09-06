# Methods summary

## Task
Closed-set 42-class syndrome differentiation from clinical presentation text. All models receive the same task input field and target the same fixed canonical label set.

## Historical TCM-SD42 construction
The 42-class task is derived from original TCM-SD `syndrome` annotations, not from the official normalized 148-class `norm_syndrome` taxonomy. A surviving preprocessing log records 278 distinct source syndrome labels and the following eligibility rule:

- source train support >=100,
- source development support >=10,
- source test support >=10.

Exactly 42 source syndrome categories met all three thresholds. The subsequent historical `top50` step therefore retained all 42 eligible categories. This rule predates the current four-model comparison and did not use model predictions, but because source test-label support contributed to the eligibility rule, the task construction is described as test-informed and this is disclosed as a limitation.

The post-deduplication `top50_full` version contained 39,072 training, 4,411 development, and 4,452 test records. A `top50_balanced_cap1000` version capped training support at 1,000 per class (19,125 training records) while leaving development/test counts unchanged. The later frozen comparative task uses 4,186 training records, 420 development records, and the same 4,452-record held-out source pool before final decontamination.

## Leakage and redundancy audit
Cross-split redundancy was audited using exact matching plus a near-duplicate screen based on character n-gram TF-IDF cosine similarity. The high-similarity threshold was >=0.95. A union of exact and near-duplicate exclusions removed 234 held-out records, producing the 4,218-record primary test set; no exact or >=0.95 near-duplicate case remained between the clean test and training/development partitions.

A separate train-development audit identified 54 development instances involved in >=0.95-similarity pairs, including 18 exact duplicates. In a ZY-BERT sensitivity analysis, removing overlap-affected development instances reduced development Macro-F1 from 0.8056 to 0.7742.

## Primary evaluation set
The main paper reports the decontaminated held-out set (N=4,218). The original same-source held-out pool contains 4,452 records. The clean test distribution is strongly imbalanced, so Accuracy is interpreted together with Macro-F1 and Balanced Accuracy.

## Metrics
- exact top-1 accuracy (`syn_acc@1`)
- Macro-F1
- Weighted-F1
- Balanced accuracy
- format validity and empty-prediction rate for generated outputs
- paired bootstrap 95% CI for accuracy differences (2,000 resamples; seed 20260516)
- exact two-sided McNemar test
- Holm correction across six pairwise comparisons

## Checkpoint selection
- MacBERT: development Macro-F1 early stopping (historical frozen run)
- ZY-BERT: development Macro-F1
- InternLM3-8B: development Macro-F1 in the final comparative protocol
- Qwen3-8B: historical frozen v18 checkpoint selected by development loss; this mismatch is disclosed and the model was not retroactively retuned on held-out data

## Inference
Generative-model outputs are parsed with one frozen closed-set parser (`code/parse_label.py`). Greedy generation is used for the current LLM evaluation protocol (`do_sample=False`, `temperature=0`, `max_new_tokens=96`).

## Statistical scope
Paired accuracy inference is case-level. Because stable patient identifiers are unavailable, the analysis cannot model possible within-patient correlation if multiple records originated from the same patient.

## Three-seed robustness
ZY-BERT and InternLM3-8B were replicated with seeds 42, 2026, and 7. The held-out set was not used to select checkpoints.
