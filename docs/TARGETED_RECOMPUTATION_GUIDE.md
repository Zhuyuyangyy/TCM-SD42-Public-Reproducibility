# Targeted server-side recomputation guide (2026-10-23)

The 2026-10-23 real-input audit has already run the MacBERT metric check and the source-split label reconstruction on the authorized server. The results and remaining limits are recorded in `docs/TARGETED_CHECKS_20261023.md`. The commands below document how to repeat those checks on authorized inputs; they do not imply that private inputs are included in this public repository. The scripts emit aggregate metrics/counts and file hashes only and do not print clinical text or record IDs.

## A. Recompute the historical 42-label eligibility rule

Obtain the official TCM-SD source train/dev/test splits from the upstream release. Use the original raw \`syndrome\` field, not \`norm_syndrome\`, unless inspection of the source schema proves that a different field was used in the historical pipeline.

\`\`\`bash
python code/recompute_tcm_sd42_label_selection.py \\
  --train /path/to/source_train.json \\
  --dev /path/to/source_dev.json \\
  --test /path/to/source_test.json \\
  --label-field syndrome \\
  --frozen-labels code/labels_42.txt \\
  --out-dir /path/to/private_audit_output
\`\`\`

Expected source split sizes are 43,180 / 5,486 / 5,486. The 2026-10-23 source-split audit found 278 unique raw labels in train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization; 43 raw strings pass the thresholds and canonicalize to the frozen 42 labels. The raw-form-first reconstruction yields 38,955 eligible Train records before cap, 19,352 after separate raw-form caps, and 4,888/4,904 eligible Dev/Test. A separate canonical-first reconstruction on the authorized source splits yields 39,072 Train before cap, 19,125 after cap, and 4,902/4,912 Dev/Test; retained duplicate counters reconcile final totals to 19,125/4,411/4,452. The 227 post-cap difference is +247 from separate caps on the two zheng-xu-yu-jie raw forms minus 20 qi-yin-liang-xu records failing raw-form Dev/Test thresholds. The pre-cap difference is -117 (-97 qi-zhi-xue-yu records failing raw-form Train/Test thresholds, minus 20 qi-yin-liang-xu). The public script now implements canonical-first as the default and exposes `--selection-level raw_form` for the raw-form merge-then-cap comparison. It emits all three variants and per-label scope differences. The 2026-10-25 CI run passed the synthetic tests; the official-source totals are supported by the authorized clean-clone report, while the historical May 2026 operation order remains unproven. It writes separate raw-label and canonical-label support CSVs plus aggregate JSON with input SHA-256 hashes. The expected outputs are label_selection_raw_support.csv, label_selection_canonical_support.csv, and label_selection_recompute.json. If the field names or source split counts differ, stop and resolve the schema before interpreting the result. A successful result validates the rule on the downloaded source files; it does not prove that the same script was executed in May 2026.

## A2. Test the two possible training-cap orders

The 2026-10-25 source-split reconstruction distinguishes the raw-form-first alternatives from canonical-first selection. The current public script implements canonical-first by default and adds `--selection-level {canonical,raw_form}` to compare canonical-first with raw-form-first selection. The reconstructed canonical-first totals are 39,072 before cap, 19,125 after cap, and 4,902/4,912 Dev/Test; raw-form-first yields 38,955 before cap, 19,352 or 19,105 after cap, and 4,888/4,904 Dev/Test. The canonical-first patch should report all three variants:
- cap each eligible raw label, then merge canonical labels;
- merge eligible raw labels into canonical labels, then cap each canonical label.

Run it with the frozen support CSV as an additional input:

```bash
python code/recompute_tcm_sd42_label_selection.py \
  --train /path/to/source_train.json \
  --dev /path/to/source_dev.json \
  --test /path/to/source_test.json \
  --label-field syndrome \
  --frozen-labels code/labels_42.txt \
  --frozen-support-csv /path/to/label_distribution.csv \
  --out-dir /path/to/private_audit_output
```

Inspect `reconstruction_variants`, `cap_scope_difference`, `pre_cap_scope_difference`, and `frozen_support_csv_comparison` in the patched script's JSON. The canonical-first result reproduces the retained frozen support, while the raw-form-first alternatives explain the historical 227 post-cap / 117 pre-cap arithmetic differences. This supports the reconstructed counting mechanism but does **not** prove that this exact operation order ran in May 2026, because the contemporaneous stdout and complete source-label frequency table are unavailable. The canonical-first mode is now in the public branch and its synthetic CI tests pass. The authorized-source recomputation reports the expected counts; retain the caveat that this does not prove the exact historical May 2026 execution order.

## B. Recompute MacBERT metrics from the frozen 4,452-row prediction file

This requires authorized local copies of:
- the frozen full test split (4,452 rows),
- the clean test split (4,218 rows),
- the 234-ID exclusion list,
- \`macbert_heldout4452.jsonl\`, and
- the frozen 42-label list.

\`\`\`bash
python code/recompute_macbert_frozen_metrics.py \\
  --full-test /path/to/full_test_4452.json \\
  --clean-test /path/to/heldout_clean_4218.json \\
  --excluded-ids /path/to/excluded_heldout_ids.csv \\
  --predictions /path/to/macbert_heldout4452.jsonl \\
  --labels code/labels_42.txt \\
  --out /path/to/private_audit_output/macbert_metrics.json
\`\`\`

The script checks unique IDs, the 1-based prediction index, the full-test gold sequence, clean-test gold/order alignment, and the exclusion-set identity before calculating Accuracy, Macro-F1, Weighted-F1 and Balanced Accuracy. If the prediction file uses different field names, pass the matching \`--prediction-index-field\`, \`--prediction-gold-field\`, \`--prediction-field\`, or \`--excluded-id-field\` explicitly. Do not change the parser or label normalization to make the output match the expected numbers.

A successful metric match verifies the frozen prediction file against the clean split. It does not recover the MacBERT checkpoint, training history, or prove the historical input text identity.

## C. Qwen3 Stage-2 evidence boundary

The 2026-10-23 server audit verified all five Qwen3-8B base weight shards and `tokenizer.json` against upstream Hugging Face LFS at commit prefix `b968826d…`; `config.json` was byte-identical. The early archive contains a checksum-matching `TCM-Mini-best` adapter copy (SHA-256 `a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf`). However, the two epoch-specific adapters needed for a saved-state epoch comparison were not found in the active run tree, so that comparison remains BLOCKED. The Stage-2 AdamW group included 168,960 fp32 Norm parameters, but adapter-only saving omitted them; validation loss was computed on the in-memory state with Norm parameters in the optimizer, whereas held-out inference uses base Norm weights plus LoRA. This state mismatch must be disclosed. A new inference check is possible with the verified base and archived adapter copy, but the original inference command and per-record input hashes remain unavailable; do not claim an exact historical prediction-to-checkpoint chain.

## D. Seed 7

The continuation stdout was recovered in the 2026-10-23 targeted audit and its SHA-256 verified as `17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f`. It records batch size 8, skipping 739 existing rows and generating 3,479 rows. A prior reconciliation on another server could not locate the referenced path, so that path discrepancy remains documented. The log supports the continuation segment, but not the provenance of the first 739 predictions or the complete cross-segment checkpoint/tokenizer hash chain; the held-out effect of any batch-size difference remains unknown.


## E. Corrected 5-gram Jaccard diagnostic

The completed log reports Train-to-Dev/Test candidate hits of 615/625 at threshold >=0.80, 516/550 at >=0.85, and 370/387 at >=0.90. Earlier interim counts 502/518 and 424/447 were taken from an incomplete log tail and are superseded. These diagnostic hit counts are not the historical production deletion counts. Corrected diagnostic report SHA-256: `7014c4021f1a38b1eb72db23f0e56e50c44d0a0eb44f836c7b0c688c42646536`.
