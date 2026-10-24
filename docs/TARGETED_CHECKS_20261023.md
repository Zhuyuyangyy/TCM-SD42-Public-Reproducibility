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

Selected-label support reconstructed from the public source splits is 39,072 eligible raw Train records before cap, 19,352 after capping each raw label at 1,000, 4,902 development records and 4,912 test records. Retained duplicate counts reconcile Dev and Test arithmetically: 4,902 - 453 Dev/Train duplicates - 38 additional Dev/Test duplicates = 4,411; 4,912 - 460 Test/Train duplicates = 4,452. The capped Train count remains 227 above the frozen 19,125. The updated public script compares cap-before-canonicalization with canonicalization-before-cap and can compare per-class Train support against the frozen support CSV. A synthetic test confirms the script can detect a 227-record difference caused by cap order, but this is not proof that this was the historical cause. The historical post-processing/deduplication script and full original frequency table remain unavailable. Therefore, the canonical 42-label vocabulary is independently reconstructed and Dev/Test totals are arithmetically reconciled, but the 227-record Train gap and exact historical operation order remain unresolved.

### Corrected 5-gram Jaccard diagnostic

The completed log summary—not the earlier incomplete tail—reports the following Train-to-Dev/Test candidate-hit counts:

| Threshold | Dev hits | Test hits |
|---|---:|---:|
| >=0.80 | 615 | 625 |
| >=0.85 | 516 | 550 |
| >=0.90 | 370 | 387 |

Earlier interim values 502/518 and 424/447 are superseded. These are diagnostic counts for a 5-gram Jaccard candidate rule, not the historical production filter and not the recorded duplicate-removal counts. The corrected report SHA-256 is `7014c4021f1a38b1eb72db23f0e56e50c44d0a0eb44f836c7b0c688c42646536`.


## C. Qwen3 saved-state epoch comparison — BLOCKED

The historical code and training log indicate that the Stage-2 AdamW group included 43,646,976 LoRA parameters plus 168,960 fp32 Norm parameters in layers 12–31. Adapter-only saving omitted the Norm parameters, so development-loss selection used an in-memory state not identical to the saved/evaluated base-plus-LoRA state.

The Qwen3 base-model verification job additionally compared all five weight shards, `tokenizer.json`, and `config.json` with the official Hugging Face upstream at commit prefix `b968826d…`. All five shards and the tokenizer matched upstream LFS; config.json was byte-identical. Reported SHA-256 prefixes: shard 1 `31d6a825…cbf5f`, shard 2 `5991236c…18282`, shard 3 `c5185c47…896836`, shard 4 `b5ee7de7…caa917a`, shard 5 `20c2d636…b542ff`, tokenizer `aeb13307…2dae4`, config `f7c4eadf…47c30`. Full digests are preserved in the server-side audit report whose SHA-256 is `337abf91ad9493b496069f381df8a5da5a2912a48dcf326b8aee76fef5f5a0de`.

The uploaded early Pilot-SFT archive contains the historical TCM-Mini-best adapter (174,655,536 bytes; SHA-256 a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf, matching its retained checksum) and a 4,452-row raw-output artifact whose SHA-256 matches the historical server inventory. This confirms those early pilot artifacts are preserved. It does not prove that this adapter generated the current four-system Qwen3 prediction file because the original inference command and per-record input hashes are missing. The two Stage-2 epoch adapters needed for a saved-state epoch comparison were not found in the latest server audit, so that comparison remains blocked. This does not mean the base model is missing: all seven base/tokenizer/config artifacts above are verified, and an archived adapter copy exists; the remaining gap is the missing epoch-specific adapters and the original prediction-to-checkpoint/input chain.

## D. Seed-7 continuation stdout — FOUND / VERIFIED

The continuation stdout was recovered in the 2026-10-23 targeted audit and its SHA-256 was verified as `17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f`. It records batch size 8, skipping 739 existing rows and generating 3,479 rows. A prior reconciliation on a different server could not locate the referenced path, so that path discrepancy remains a provenance note; the current audit reports the log bytes as FOUND/VERIFIED. The log does not independently establish the provenance of the first 739 predictions, provide per-record segment markers, or verify a complete cross-segment checkpoint/tokenizer hash chain. The held-out effect of any batch-size difference remains unknown.

## Overall conclusion

- MacBERT aggregate metrics: PASS from frozen predictions.
- Label-selection reconstruction: PARTIAL; 42 canonical labels reproduced, but the summary's 278 field is ambiguous and downstream counts do not reproduce.
- Qwen3 saved-state epoch comparison: BLOCKED due conflicting adapter availability records and missing epoch adapters.
- Seed-7 continuation log: FOUND / VERIFIED; first-segment provenance remains incomplete.

No primary metric, historical prediction, checkpoint or SEAL was changed. This report distinguishes reconstruction on current public source splits from proof of the exact historical execution.
