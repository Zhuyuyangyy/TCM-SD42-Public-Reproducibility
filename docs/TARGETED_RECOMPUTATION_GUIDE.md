# Targeted server-side recomputation guide (2026-10-23)

These scripts are intended to run on an authorized machine that has the official public source splits or the private frozen prediction inputs. They emit aggregate metrics/counts and file hashes only; they do not print clinical text or record IDs. The source datasets and per-case prediction files are deliberately not included in this repository.

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

Expected reported source split sizes are 43,180 / 5,486 / 5,486. The internal summary file reports 278 raw labels, 42 eligible/selected labels, and post-processing counts 19,125 / 4,411 / 4,452. The script reports the actual recomputation rather than forcing those expected values. It writes a per-label support CSV and aggregate JSON including input SHA-256 hashes. If the field names or source split counts differ, stop and resolve the schema before interpreting the result. A successful result validates the rule on the downloaded source files; it does not prove that the same script was executed in May 2026.

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

The latest private server audit reports the recovered adapter SHA-256 and five base-model shards. It also establishes that 168,960 fp32 Norm parameters were included in the Stage-2 AdamW group but omitted from the adapter-only saved artifact. The validation loss was computed on the in-memory model state with those Norm parameters enabled, whereas held-out inference used the base model's original Norm weights plus LoRA. This state mismatch must be disclosed. If both stage-2 epoch adapters are available, a development-only comparison of the saved adapter artifacts can assess whether selecting the checkpoint on the actual saved inference state would change the epoch choice; do not use held-out test results to retune.

## D. Seed 7

The 739/3,479 split is not asserted as verified because the cited continuation stdout could not be located in the subsequent archive reconciliation. Keep it UNVERIFIED unless a byte-identical log copy is recovered and its SHA-256 verified. The existing prediction/SEAL integrity checks do not prove the segment boundary or quantify any test-set batch-size effect.
