# Historical evidence reconciliation (2026-10-23)

This note reconciles the early Pilot-SFT archive with the current four-system comparison. It does not change frozen predictions or primary metrics. The early v14 Pilot-SFT manuscript and the current four-system paper are different analysis versions; their aggregate metrics must not be mixed.

## Confirmed early artifacts

The uploaded early archive contains the historical Qwen3 TCM-Mini-best adapter (174,655,536 bytes; SHA-256 `a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf`), matching its retained checksum. The safetensors header has 504 F32 tensors, 43,646,976 parameters, and no Norm tensor keys. The archive also contains the 4,452-row raw-output file (6,760,239 bytes; SHA-256 `9a02eca7394a599ead9db00c80bb16803c63dedf203bae9d4f8c644523c07042`), matching the historical server inventory. The original inference command and per-record input hashes are missing, so the complete output-to-checkpoint link remains incomplete.

## Legacy evaluator boundary

The early pilot evaluator maps `气虚血瘀` to `气滞血瘀` and uses alias-equivalence for top-1 correctness. Its F1 metrics instead compare raw gold labels with alias-normalized predictions. Therefore the old 60.60% top-1 and its F1 values do not share one exact-label definition and are not reused in the current four-system comparison. Re-parsing the archived raw outputs with the current public exact-label parser gives 2,670/4,452 correct (59.973%) and two empty predictions. This is an offline re-evaluation, not a new inference run.

## Source-split count reconciliation

The retained `dataset_stats.json` reports original split sizes 43,180/5,486/5,486 and frozen counts 19,125/4,411/4,452. The 2026-10-23 source-split audit reports 278 raw syndrome strings in Train, 282 across the three raw splits, and 278 after suffix normalization. The thresholds select 43 eligible raw strings; normalizing `正虚瘀结证` to `正虚瘀结` yields the frozen 42-label vocabulary. The field `raw_label_count=278` is scope-ambiguous.

The source reconstruction yields 39,072 eligible raw Train records, 19,352 after the 1,000-per-class cap, and 4,902/4,912 Dev/Test. Retained duplicate counts reconcile Dev and Test: 4,902−453−38=4,411 and 4,912−460=4,452. The capped Train count remains 227 above the frozen 19,125. The original preprocessing script, complete raw label-frequency table, and pair-level near-duplicate file were not recovered; the 227-record difference remains unresolved.

## Qwen3 Norm and Seed 7

Stage 2 included 43,646,976 LoRA parameters plus 168,960 fp32 Norm parameters in the optimizer group, but the adapter-only artifact contains LoRA parameters only. Thus the validation state used for epoch selection differs from the saved/evaluated state; exact per-tensor Norm deltas are unavailable.

The Seed-7 continuation stdout was recovered and SHA-256-verified as `17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f`. It records batch size 8, 739 rows skipped, and 3,479 generated. The first 739 rows and cross-segment checkpoint/tokenizer identity remain unverified.

## Reporting boundary

The 42-label set is independently matched and Dev/Test totals are arithmetically reconciled. The full source-to-frozen pipeline and 227-record Train difference are not fully reproducible. Do not mix the early pilot evaluator's aggregate metrics with the current exact-label comparison, and do not claim end-to-end Seed-7 or Qwen3 checkpoint provenance beyond the evidence above.
