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

Expected source split sizes are 43,180 / 5,486 / 5,486. The 2026-10-23 source-split audit found 278 unique raw labels in train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization; 43 raw strings pass the thresholds and canonicalize to the frozen 42 labels. The source reconstruction yields 39,072 eligible raw Train records, 19,352 when the cap is applied to each raw label, and 4,902 / 4,912 eligible Dev/Test records. Retained duplicate counts reconcile Dev/Test to 4,411 / 4,452 (453 Dev/Train, 460 Test/Train, and 38 additional Dev/Test removals). The 227-record Train difference may depend on whether eligible raw labels are canonicalized before the per-class cap; compare both explicit operation orders before marking it resolved. The script reports the actual recomputation rather than forcing the historical values. It writes separate raw-label and canonical-label support CSVs plus aggregate JSON with input SHA-256 hashes. The expected outputs are label_selection_raw_support.csv, label_selection_canonical_support.csv, and label_selection_recompute.json. If the field names or source split counts differ, stop and resolve the schema before interpreting the result. A successful result validates the rule on the downloaded source files; it does not prove that the same script was executed in May 2026.

## A2. Test the two possible training-cap orders

The 2026-10-23 source-split audit found 19,352 training records when the 1,000-per-class cap is applied to each eligible raw label before suffix canonicalization. The retained frozen Train artifact has 19,125 records, a difference of 227. The revised label-selection script now reports both:
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

Inspect `cap_order_comparison` and `frozen_support_csv_comparison` in the JSON. If canonicalization-before-cap yields 19,125 and the per-class Train support matches the frozen CSV, this would explain the 227-count difference for the reconstructed rule. It would **not** prove that this was the exact historical operation order unless the original script/log is recovered. Do not change the historical claim based on total-count coincidence alone.

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

A prior server inventory reported an adapter SHA-256 and five base-model shards, but the latest targeted audit could not locate the selected adapter or either epoch adapter and found the `TCM-Mini-best` link dangling. Treat adapter recovery as unresolved until the file is present and its hash is rechecked in the same environment. The audit reports that 168,960 fp32 Norm parameters were included in the Stage-2 AdamW group but omitted from the adapter-only saved artifact. The validation loss was computed on the in-memory model state with those Norm parameters enabled, whereas held-out inference used the base model's original Norm weights plus LoRA. This state mismatch must be disclosed. If both stage-2 epoch adapters are available, a development-only comparison of the saved adapter artifacts can assess whether selecting the checkpoint on the actual saved inference state would change the epoch choice; do not use held-out test results to retune.

## D. Seed 7

The 739/3,479 split is not asserted as verified because the cited continuation stdout could not be located in the subsequent archive reconciliation. Keep it UNVERIFIED unless a byte-identical log copy is recovered and its SHA-256 verified. The existing prediction/SEAL integrity checks do not prove the segment boundary or quantify any test-set batch-size effect.
