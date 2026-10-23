# Manuscript and Supplement minimal patch list (2026-10-23)

This is an editing guide, not a claim that the DOCX files have already been updated. Apply only to the current four-system manuscript/Supplement, not the early v14 Pilot-SFT manuscript. Do not alter Tables 2–4, frozen predictions, or existing significance values.

## Main text: Methods 2.2 (data source and task construction)

Suggested concise wording:

> The frozen 42-label vocabulary was reconstructed from the original TCM-SD syndrome field using the retained support rule (train >=100, development >=10, test >=10) and a top-50 cap. A read-only reconstruction of the official source splits identified 278 distinct raw strings in Train, 282 in the raw three-split union, and 278 after removal of one trailing 证. The support thresholds selected 43 eligible raw strings; canonicalization of 正虚瘀结证 to 正虚瘀结 yielded the frozen 42-label vocabulary. The historical dataset_stats.json reports raw_label_count=278, but the field does not identify which counting stage it represents. The original preprocessing implementation and complete source-label frequency table were not recovered.

## Main text: Methods 2.2 or a short data-processing note

Suggested wording:

> The frozen downstream support table contains 19,125 training, 4,411 development, and 4,452 held-out records. A reconstruction from the official source splits yields 19,352 training records after a 1,000-per-raw-label cap, 4,902 development records, and 4,912 test records. Retained duplicate counts reconcile the development and test totals (453 development records overlapping Train, 460 test records overlapping Train, and 38 additional development records overlapping Test). The 227-record difference between the capped reconstructed Train set and the frozen Train set remains unresolved because the original post-processing script and pair-level duplicate artifacts are unavailable. Therefore, the frozen support counts are verified against the derived artifacts, but the full source-to-frozen transformation is not claimed to be independently reproduced.

Do not shorten this to “all split counts were independently reproduced.” Do not attribute the remaining 227 records to cleaning unless the cap-order script and per-class frozen-support comparison support it.

## Main text: Methods 2.4.3 (Qwen3) / Limitations

Suggested wording:

> The historical Stage-2 code/log indicates an optimizer group containing 43,646,976 LoRA parameters and 168,960 fp32 normalization parameters. The recovered early Pilot-SFT adapter artifact contains the LoRA tensors only; the normalization tensors are not serialized. Accordingly, the development-loss selection state and the saved adapter-only inference state are not identical. The recovered adapter and raw-output artifact belong to the early Pilot-SFT archive; the original inference command and per-record input hashes were not retained, so this artifact alone does not prove which exact checkpoint generated the current four-system Qwen3 prediction file. The current frozen Qwen3 metrics are retained without modification, and this provenance boundary is disclosed.

Only assert that the recovered early adapter was the exact evaluated four-system checkpoint if a matching current-run checkpoint hash or equivalent direct record is found.

## Main text: Methods 2.4.4 / Supplement (Seed 7)

Suggested wording:

> The recovered Seed-7 continuation stdout (SHA-256 17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f) records a batch-size-8 continuation that skipped 739 existing rows and generated the remaining 3,479 rows. The origin of the first 739 predictions and a complete checkpoint/tokenizer identity chain across the segments could not be independently verified; the effect of any batch-size difference on the frozen predictions remains unknown.

Do not state that all 4,218 records have verified per-record batch provenance.

## Supplementary Table S7

Retain the 18-row duplicate-sensitivity table for S0 (n=4,218), S1 exact-text deduplication (n=4,206), and S2 normalized-text stress test (n=4,195). Define S2 normalization as Unicode NFKC, each consecutive digit run replaced by #, then punctuation, symbols, control characters and whitespace removed while preserving #. In each duplicate group retain the record with the smallest numeric ID suffix. Describe S2 as a string-normalization stress test, not adjudicated semantic or patient-level deduplication.

## Limitations paragraph

Include the following boundaries, without implying the primary frozen metrics have been recalculated:
- original preprocessing/deduplication script and pair-level duplicate artifact are missing;
- 227 Train records remain unexplained;
- historical task construction used source test-label support and is test-informed;
- Qwen3 selection-time model state differed from the saved adapter-only state, and the current four-system output-to-checkpoint link is not fully closed;
- Seed-7 continuation is verified, but the first 739 rows and cross-segment checkpoint/tokenizer identity remain unverified;
- MacBERT metrics are reproducible from frozen predictions, but its original fine-tuned checkpoint and training history are missing.

## Version and scope guard

This patch applies to the current four-system comparison only. The early v14 Pilot-SFT paper's alias-equivalence top-1 metric and legacy F1 calculation must not be copied into the current manuscript. No new labels, model runs, or held-out-driven checkpoint choices are introduced by these edits.
