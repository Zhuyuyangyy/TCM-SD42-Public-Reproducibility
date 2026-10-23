# Targeted audit results — 2026-10-23

This document summarizes the latest read-only server audit. No model was retrained, no frozen prediction/checkpoint/SEAL was modified, and no held-out result was used for checkpoint selection.

## A. MacBERT frozen-prediction metric reconstruction — PASS

The archived 4,452-row MacBERT prediction file passed 8/8 structural checks covering row count, unique/indexed rows, full-test gold sequence, clean-test ID/gold alignment, and exclusion-set identity. Metrics recomputed on the frozen clean set (n=4,218) were:

| Metric | Recomputed | Published |
|---|---:|---:|
| Accuracy | 62.778568% | 62.78% |
| Macro-F1 | 56.811275% | 56.81% |
| Weighted-F1 | 63.944848% | 63.94% |
| Balanced Accuracy | 72.628728% | 72.63% |

Correct predictions: 2,648 / 4,218. This validates metrics from the frozen prediction file; the historical MacBERT fine-tuned checkpoint and epoch-level training history remain missing, so the original training run is not re-instantiable from its original weights.

## B. Source-split label reconstruction — PARTIAL

Using the official public TCM-SD source splits (43,180 train / 5,486 development / 5,486 test):

| Counting stage | Distinct labels |
|---|---:|
| Raw syndrome strings in train split | 278 |
| Union of raw strings across all three splits | 282 |
| Union after removing one trailing 证 | 278 |
| Raw strings meeting train>=100, dev>=10, test>=10 | 43 |
| Canonical labels after trailing-证 removal among eligible strings | 42 |

The two eligible raw strings 正虚瘀结证 and 正虚瘀结 canonicalize to one frozen label. The final canonical label set exactly matches the frozen 42-label vocabulary. The top-50 cap is not binding in this reconstruction because 43 raw strings pass the thresholds.

The retained internal dataset_stats.json reports raw_label_count=278, eligible_label_count=42, and selected_label_count=42, but does not specify the stage used for raw_label_count; 278 can refer to train-only raw strings or the canonicalized three-split union, while the raw three-split union is 282.

Selected-label support reconstructed from the public source splits is 39,072 training records before cap, 19,352 training records after a 1,000-per-canonical-label cap, 4,902 development records and 4,912 test records. These do not match the frozen downstream support totals 19,125 / 4,411 / 4,452. The historical post-processing/deduplication script and full original frequency table are unavailable; differences of 227 / 491 / 460 remain unexplained. Therefore, the canonical 42-label vocabulary and threshold rule are independently reconstructable on current public source files, but the exact historical execution and downstream support transformation are not fully reproduced.

## C. Qwen3 saved-state epoch comparison — BLOCKED

The historical code and training log indicate that the Stage-2 AdamW group included 43,646,976 LoRA parameters plus 168,960 fp32 Norm parameters in layers 12–31. Adapter-only saving omitted the Norm parameters, so development-loss selection used an in-memory state not identical to the saved/evaluated base-plus-LoRA state.

A prior server inventory reported an adapter SHA-256 of a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf, but the latest targeted audit could not locate the selected adapter or either epoch adapter and found the TCM-Mini-best symlink dangling. The reports conflict. Until the file bytes and checksum are verified together in the same environment, adapter recovery and saved-state epoch comparison remain unresolved. The original inference command and per-record input hashes are also unavailable.

## D. Seed-7 continuation stdout — FOUND / VERIFIED

The continuation stdout was recovered and its SHA-256 verified as:

17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f

It records batch size 8, skipping 739 existing rows and generating 3,479 rows. This verifies the continuation segment and its reported counts. It does not independently establish the provenance of the first 739 predictions, provide per-record segment markers, or verify a complete cross-segment checkpoint/tokenizer hash chain. The held-out effect of any batch-size difference remains unknown.

## Overall conclusion

- MacBERT aggregate metrics: PASS from frozen predictions.
- Label-selection reconstruction: PARTIAL; 42 canonical labels reproduced, but the summary's 278 field is ambiguous and downstream counts do not reproduce.
- Qwen3 saved-state epoch comparison: BLOCKED due conflicting adapter availability records and missing epoch adapters.
- Seed-7 continuation log: FOUND / VERIFIED; first-segment provenance remains incomplete.

No primary metric, historical prediction, checkpoint or SEAL was changed. This report distinguishes reconstruction on current public source splits from proof of the exact historical execution.
