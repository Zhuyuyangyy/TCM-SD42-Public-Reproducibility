# Methods summary

## Task
Closed-set 42-class syndrome differentiation from clinical presentation text. All models receive the same task input field and target the same fixed canonical label set.

## Historical TCM-SD42 construction

The 42-class task is derived from original TCM-SD `syndrome` annotations, not from the official normalized 148-class `norm_syndrome` taxonomy. A retained internal `dataset_stats.json` reports 278 raw source labels, 42 eligible labels and 42 selected labels under the criterion train>=100, development>=10, test>=10, with a top-50 cap. The summary reports raw split totals of 43,180 / 5,486 / 5,486 and post-processing totals of 19,125 / 4,411 / 4,452.

The original preprocessing script, complete source-label frequency table and contemporaneous execution log were not recovered. Independent reconstruction on the official source splits finds 278 raw strings in train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization. The reported thresholds select 43 eligible raw strings; canonicalizing the two eligible forms 正虚瘀结证 and 正虚瘀结 yields the frozen 42-label vocabulary. The internal summary's raw_label_count=278 field does not specify which of these counting stages it represents. The reconstruction yields 39,072 selected-label training records before cap, 19,352 after the 1,000-per-label cap, 4,902 development and 4,912 test; it does not reproduce the retained downstream support totals of 19,125/4,411/4,452. The missing historical preprocessing/deduplication code prevents explaining the differences of 227/491/460 records. Since source test-label support contributed to the reported rule, the historical task definition is disclosed as test-informed.

The later comparative task used the frozen derived partitions of 4,186 training records, 420 development records and the 4,452-record held-out source pool before final decontamination; these downstream partitions are not directly reproduced by the public source-split threshold reconstruction. The 420-record development subset is a downstream balanced subset, not the 4,411-record post-processing development split reported in the internal summary.

## Leakage and redundancy audit
The archived implementation was re-audited at code level in the v23.1 revision using authorized private inputs; the public repository contains the implementation but not the records required to replay the historical result by itself. Exact held-out exclusions were defined by SHA-256 equality of the raw `input_text` against train, development, or pilot records.

For near-duplicate screening, `input_text` was standardized by removing case identifiers matching `tcm_sd_(train|test)_\\d+`, all digits, punctuation/whitespace, and fixed template prefixes. A single `TfidfVectorizer` was fit across standardized train, development, pilot, and held-out texts with:

- `analyzer="char_wb"`
- `ngram_range=(2,4)`
- `min_df=2`
- `sublinear_tf=True`
- `norm="l2"`
- `max_features=200000`
- sklearn defaults `max_df=1.0`, `lowercase=True`, `strip_accents=None`

Cosine similarity was computed across train-held-out, development-held-out, pilot-held-out, train-development, train-pilot, and development-pilot split pairs. The primary near-duplicate threshold was >=0.95. A held-out record was excluded if it had either a raw exact `input_text` match or a >=0.95 TF-IDF cosine match to any train, development, or pilot record.

The 2026-10-22 private audit reports an independent reconstruction from authorized frozen audit files: 5 unique raw-exact held-out IDs and 234 unique >=0.95 near-duplicate held-out IDs; 229 of the latter were not already in the raw-exact set. Their union contained 234 unique records, matching the ID difference between the 4,452-record source pool and the 4,218-record clean held-out set. The private source partitions and pair-level file are not included in this public repository.

A separate train-development audit identified 54 development instances involved in >=0.95-similarity pairs, including 18 exact duplicates. In a ZY-BERT sensitivity analysis, removing overlap-affected development instances reduced development Macro-F1 from 0.8056 to 0.7742.

See `docs/LEAKAGE_AUDIT_METHOD.md` for the implementation-level audit.

## Primary evaluation set
The main paper reports the decontaminated held-out set (N=4,218). The original same-source held-out pool contains 4,452 records. The clean test distribution is strongly imbalanced, so Accuracy is interpreted together with Macro-F1 and Balanced Accuracy.

## Metrics
- exact top-1 accuracy (`syn_acc@1`)
- Macro-F1
- Weighted-F1
- Balanced accuracy
- format validity and empty-prediction rate for generated outputs
- paired bootstrap 95% CI for accuracy, Macro-F1, and Balanced Accuracy differences (2,000 resamples; seed 20260516)
- exact two-sided McNemar test for paired accuracy
- Holm correction across six pairwise accuracy comparisons
- class-stratified paired-bootstrap sensitivity analysis for class-sensitive metrics

## Checkpoint selection
- MacBERT: development Macro-F1 early stopping (historical frozen run)
- ZY-BERT: development Macro-F1
- InternLM3-8B: the latest author-reported reconciliation identifies development Macro-F1 as the official selection criterion; the public training script and protocol retain a development-loss intermediate checkpoint setting, and public seals alone do not independently prove the final ranking rule
- Qwen3-8B: historical frozen v18 adapter selected by development loss. A later server audit recovered the adapter (SHA-256 recorded in `docs/QWEN3_STAGE2_SEMANTICS.md`) and found that the Stage-2 optimizer included 168,960 fp32 Norm parameters, but adapter-only saving omitted them. The development loss was evaluated on the in-memory state with those Norm parameters enabled, whereas the evaluated artifact is base model plus LoRA without those Norm updates; this selection-state/evaluated-artifact mismatch is disclosed. The original inference command and per-record input hashes remain unavailable; no held-out retuning was performed.

## Inference
Generative-model outputs are parsed with one frozen closed-set parser (`code/parse_label.py`). Greedy generation is used for the current LLM evaluation protocol (`do_sample=False`, `temperature=0`, `max_new_tokens=96`).

## Statistical scope
Paired inference is case-level. Because stable patient identifiers are unavailable, the analysis cannot model possible within-patient correlation if multiple records originated from the same patient.

## Three-seed robustness
ZY-BERT and InternLM3-8B were replicated with seeds 42, 2026, and 7. The held-out set was not used to select checkpoints.
