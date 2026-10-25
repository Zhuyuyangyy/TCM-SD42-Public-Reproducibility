# Methods summary

## Task
Closed-set 42-class syndrome differentiation from clinical presentation text. All models receive the same task input field and target the same fixed canonical label set.

## Historical TCM-SD42 construction

TCM-SD42 is based on original TCM-SD `syndrome` annotations, not the official normalized 148-class `norm_syndrome` taxonomy. The retained internal `dataset_stats.json` reports 278 raw labels, 42 eligible labels and 42 selected labels under `train>=100, dev>=10, test>=10, top-50 by total`. A source-split recomputation completed on 2026-10-23 found 278 distinct raw strings in the training split, 282 distinct raw strings across the three splits, and 278 labels after removing a terminal `证`. The stated support thresholds identify 43 eligible raw strings that map to the frozen 42-label vocabulary after canonicalization.

The raw-form-first reconstruction yields 38,955 training records before cap and 19,352 after separately capping eligible raw forms. Canonical-first reconstruction yields 39,072 before cap, 19,125 after cap, and 4,902/4,912 development/test. The retained summary reports final counts of 19,125 / 4,411 / 4,452. Its duplicate counters reconcile Dev/Test as 4,902−453−38=4,411 and 4,912−460=4,452. The 227 post-cap difference is explained by +247 from separate raw-form caps for zheng-xu-yu-jie minus 20 records from a qi-yin-liang-xu raw form failing its own Dev/Test thresholds. The pre-cap difference is −117 (−97 qi-zhi-xue-yu failing its own Train/Test thresholds, plus −20 qi-yin-liang-xu). The original 2026-05-07 stdout and complete source-label frequency table remain unavailable, so this count reconstruction does not prove the exact historical end-to-end execution order.

The task remains test-informed because source test-label support contributed to the historical eligibility criterion. This did not use model predictions or results from the current four-model comparison, but it limits claims of a fully pre-registered or source-independent label-space construction.

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

The frozen exclusion set contains 234 held-out record IDs, equal to the ID difference between the 4,452-record source pool and the 4,218-record clean set. At record-level accounting, six excluded record IDs have exact raw-text matches; these correspond to five distinct raw-text hashes because one text appears in two records. The remaining 228 excluded IDs are the near-duplicate-only remainder in the historical record-level accounting. Earlier public wording (“5 raw exact + 229 near”) mixed unique-text and record-level units and should not be interpreted as a record-level decomposition. The original near_duplicate_pairs.csv and raw clinical partitions are not included in this repository.

An alternative reimplementation that did not exactly reuse the archived text-preprocessing order overlapped with 226/234 archived IDs, with eight archived IDs not reproduced and three additional candidates; the differences were near the 0.95 threshold. Because that implementation differed from the archived preprocessing order, this is a sensitivity warning rather than a definitive replay of the historical implementation. The public repository alone cannot independently reproduce every exclusion decision.

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
- InternLM3-8B: the archived configuration specifies Stage-2 development loss, while the later official-selection record identifies development Macro-F1. A private author-side replay reproduced the archived epoch-2 outputs byte-for-byte on dev420 for all three seeds, and both reported criteria select epoch 2; the documentary difference remains visible, and the private weights/outputs are not public
- Qwen3-8B: the early pilot archive contains the historical TCM-Mini-best adapter and its raw 4,452-row output artifact, with SHA-256 values matching retained checksum/inventory records (see `docs/HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md`). This confirms the early pilot artifacts exist, but the original inference command and per-record input hashes are missing, so exact output-to-checkpoint linkage remains incomplete. The two Stage-2 epoch adapters needed for a saved-state epoch comparison were not found in the latest server audit. The Stage-2 optimizer included 168,960 fp32 Norm parameters, but adapter-only saving omitted them; development-loss selection and the saved/evaluated state therefore differ. No held-out retuning was performed.

## Author-side dev420 replay (2026-10-23)

The private author-side report states that the official final adapters for seeds 42, 7, and 2026 were replayed on the frozen 420-record development set. IDs/order, generated tokens, raw outputs, parsed predictions, and raw/parsed SHA-256 values matched the archived epoch-2 artifacts byte-for-byte for all three seeds. This is direct replay evidence for dev420 only. It is not a second inference run on the 4,218-record clean test set, does not restore the lost independent seed-2026 intermediate checkpoint, and cannot be independently repeated from the public repository because weights and case-level outputs are not distributed.

## Seed-7 inference provenance

A hash-verified continuation stdout supports a batch-size-8 segment that skipped 739 existing rows and generated 3,479. The completed full-run stdout and original argv were not preserved, so the SEAL field alone is not treated as proof of runtime batch size for every clean-test record. Batch-size-1 and batch-size-8 outputs are not assumed equivalent; the origin of the first 739 rows and the complete cross-segment checkpoint/tokenizer chain remain unresolved.

## Inference

## Statistical scope
Paired inference is case-level. Because stable patient identifiers are unavailable, the analysis cannot model possible within-patient correlation if multiple records originated from the same patient.

## Three-seed robustness
ZY-BERT and InternLM3-8B were replicated with seeds 42, 2026, and 7. The held-out set was not used to select checkpoints.
