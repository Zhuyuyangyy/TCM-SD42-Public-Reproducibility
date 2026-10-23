# Evidence map and reproducibility boundaries

**Purpose.** This is a claim-to-artifact index for the TCM-SD42 *public research archive*. It distinguishes checks that anyone can perform on the public aggregate files from analyses that require the original authorized clinical data, predictions, or model checkpoints. It is not a certificate of independent end-to-end replication.

**Public snapshot used for this map:** the repository's published seed-42 summary, confusion matrices, statistical tables, frozen 42-label list, code, and sanitized seals. Numbers in these files are historical reported results, not newly trained or fabricated results.

## Start with a read-only public check

From the repository root:

```bash
python code/verify_public_aggregates.py
```

This Python standard-library script verifies that the public confusion matrices, published metrics, label order, three-seed summaries, and McNemar/Holm computations are internally consistent. It does **not** reconstruct patient records, per-case alignment, training, bootstrapping, or checkpoint identity. A successful public check must not be described as reproduction of the original experiments.

## Claim → public artifact → verification limit

| Claim or quantity | Public source | What an outside reader can check | What remains unverified from public files |
| --- | --- | --- | --- |
| Frozen original-label 42-class task | [`code/labels_42.txt`](../code/labels_42.txt), [`label_space/syndrome_label_list.json`](../label_space/syndrome_label_list.json), [`DATASET_PROVENANCE.md`](DATASET_PROVENANCE.md) | Compare the 42 labels and their order; inspect the documented 100/10/10 historical support rule | Recover the original missing `preprocess_tcm_sd_v4_topn.py` and independently rerun the historical eligibility rule on licensed source records |
| Seed-42 Accuracy, Macro-F1, Weighted-F1, Balanced Accuracy (N=4,218) | [`results/clean4218_seed42.csv`](../results/clean4218_seed42.csv) and the four [`confusion_matrix_*.csv`](../results/) | Recompute all four metric types with the published class marginals and the omitted-output adjustment explained below | Verify individual example IDs, labels, predictions, original model executions, and the cleaning set itself |
| Three-seed descriptive robustness for two systems | [`results/three_seed_summary.csv`](../results/three_seed_summary.csv), [`zybert_3seed_metrics.json`](../results/zybert_3seed_metrics.json), [`internlm3_3seed_metrics.json`](../results/internlm3_3seed_metrics.json) | Recompute arithmetic means and **sample** standard deviations from the three published seed summaries | Independently rerun training and inference, or verify seed-specific raw predictions and checkpoints |
| Six exact two-sided McNemar tests and Holm correction for **accuracy** | [`results/pairwise_significance_seed42.csv`](../results/pairwise_significance_seed42.csv) | Recompute exact p-values, Holm-adjusted values, and rounded accuracy deltas **from the published discordant counts** | Independently regenerate the discordant-pair counts without aligned per-case predictions |
| Paired-bootstrap confidence intervals for Accuracy, Macro-F1 and Balanced Accuracy | [`results/`](../results/), [`STATISTICAL_METHOD.md`](STATISTICAL_METHOD.md), [`code/pairwise_class_sensitive_bootstrap.py`](../code/pairwise_class_sensitive_bootstrap.py) | Inspect procedures, settings, and archived interval tables; the Macro-F1/BA intervals are descriptive 95% intervals | Recompute the published intervals or case-level resamples from the public repository alone; no general multiplicity adjustment is claimed for these intervals |
| Text-level decontamination: 4,452 → 4,218 | [`code/audit_leakage.py`](../code/audit_leakage.py), [`code/verify_exclusion_set.py`](../code/verify_exclusion_set.py), [`LEAKAGE_AUDIT_METHOD.md`](LEAKAGE_AUDIT_METHOD.md) | Inspect the method and the reported aggregate count of 234 exclusions | The public repository alone cannot reproduce the excluded-ID set; authorized private split files, the near-duplicate pair table and the frozen exclusion list are required. Patient-level independence cannot be proven (stable patient IDs are unavailable) |
| Official InternLM3 checkpoint selection | [`code/train_llm_lora.py`](../code/train_llm_lora.py), [`configs/internlm3_training_protocol.json`](../configs/internlm3_training_protocol.json), [`provenance/seal_summary.json`](../provenance/seal_summary.json) | Confirm the **public training script** saves its best checkpoint according to Stage-2 dev **loss**; public seals report selected epoch 2 and development Macro-F1 values | Independently verify the **separate, author-reported** dev Macro-F1 final-selection step or final loaded adapter hashes: selection script, per-epoch predictions, and InternLM3 adapter hashes are not publicly released |
| InternLM3 executed layer-freezing behavior | [`configs/internlm3_training_protocol.json`](../configs/internlm3_training_protocol.json), [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) | Inspect the locked design ranges and the separate execution clarification; the audit reports both stages updated LoRA layers 31–47 | Runtime parameter-group logs and all historical checkpoints are not public; the conclusion relies on private code/weight audit evidence |
| Qwen3 Stage-2 optimizer and saved adapter | [`docs/QWEN3_STAGE2_SEMANTICS.md`](QWEN3_STAGE2_SEMANTICS.md) | Review reported parameter counts and distinguish optimizer scope from the adapter-only artifact | The early archive contains a checksum-matching TCM-Mini-best adapter copy, and a separate server audit verified all five base weight shards, tokenizer.json and config.json against upstream. The two epoch-specific adapters needed for saved-state comparison remain unavailable in the active run tree. The optimizer group included the Norm parameters, but per-tensor numerical deltas are not retained and the Norm state was omitted from adapter-only saving |
| Clean-set duplicate sensitivity | [`results/dedup_sensitivity_seed42.csv`](../results/dedup_sensitivity_seed42.csv), [`code/recompute_pairwise_stats.py`](../code/recompute_pairwise_stats.py), [`docs/DATA_QUALITY_SUMMARY.md`](DATA_QUALITY_SUMMARY.md) | Inspect aggregate counts and the deterministic minimum-numeric-ID retention method | The private aligned input and predictions are not distributed; sensitivity script requires authorized local inputs |
| Seed-7 mixed decoding provenance | [`docs/SEED7_INFERENCE_PROVENANCE.md`](SEED7_INFERENCE_PROVENANCE.md), [`provenance/seal_summary.json`](../provenance/seal_summary.json) | Inspect the private-audit-reported hashes and limits | Raw/parsed outputs and stdout log are not public; the continuation stdout hash was verified in the latest private audit, but the first 739 rows and complete cross-segment checkpoint/tokenizer identity remain unresolved |
| Historical source-split counts and frozen supports | [`DATASET_PROVENANCE.md`](DATASET_PROVENANCE.md), [`HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md`](HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md) | Check the retained summary hash, raw-label scope ambiguity, and Dev/Test arithmetic reconciliation | Original preprocessing source, complete raw label-frequency table and pair-level duplicate file are missing; 227 Train records remain unexplained |
| Historical Qwen3 pilot artifact and legacy evaluator | [`QWEN3_STAGE2_SEMANTICS.md`](QWEN3_STAGE2_SEMANTICS.md), [`HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md`](HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md) | Verify adapter/raw-output hashes and distinguish alias-equivalence scoring from exact-label scoring | Original inference command/input hashes are missing; artifact hashes alone do not fully prove output-to-checkpoint linkage |
| Generalization and causal attribution | [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) | Inspect limitations on class imbalance, patient independence and comparisons among four distinct systems | Establish clinical deployment safety, a universal encoder-vs-LLM result, or a factorial causal effect of domain pretraining |

## Why the LLM 42×42 confusion matrices have 4,216 entries

The **primary evaluation denominator is 4,218 cases for all four systems**. The 42×42 confusion matrices contain only predictions that fall within the fixed 42-label space. The evaluation script's `empty` value is not among those labels, so two such predictions are absent from the InternLM3 matrix and two from the Qwen3 matrix.

| Model | 42×42 matrix count | Published empty-prediction count implied by N | Correct predictions | Accuracy denominator |
| --- | ---: | ---: | ---: | ---: |
| ZY-BERT | 4,218 | 0 | 3,196 | 4,218 |
| MacBERT | 4,218 | 0 | 2,648 | 4,218 |
| InternLM3-8B | 4,216 | 2 | 2,935 | 4,218 |
| Qwen3-8B | 4,216 | 2 | 2,476 | 4,218 |

**Calculation boundary:** To reconstruct the reported Macro-F1, Weighted-F1 and Balanced Accuracy from the published 42×42 matrices, use the full 4,218-case gold-class support vector (identical in both complete encoder matrices). For each LLM, the difference between that support vector and its 42×42 row totals gives the per-class number of omitted predictions. These omissions are counted as false negatives for their gold labels, **not dropped from the denominator or reclassified as one of the 42 valid labels**. This public marginal reconstruction reproduces the rounded published metrics; it does **not** identify the omitted individual cases or replace the withheld case-level output records.

The public marginal calculation identifies one omitted prediction under each of these gold classes: InternLM3 — `湿热瘀阻`, `风寒袭肺`; Qwen3 — `湿热蕴结`, `风寒袭肺`. These are **mathematical deductions from public class marginals**, not newly located individual patient records.

When plotting these matrices, label any image as "42×42 valid-label confusion matrix (4,216/4,218 for each generative model)"; do not silently caption the LLM matrices as if all 4,218 predictions were represented.

## Checkpoint protocol: do not conflate two stages

The **published** `train_llm_lora.py` and historical `internlm3_training_protocol.json` specify Stage-2 development **loss** for saving the training-time `best_checkpoint`. The study's official InternLM3 evaluation is **author-reported, based on a private 2026-10-21 archive audit**, to have selected a separate `best_checkpoint_macro_f1` by dev Macro-F1 across the two Stage-2 epochs. That audit reports epoch 2 for seeds 42/7/2026, and identical adapter content under both criteria. We do not present these private results as independently confirmed by publicly released code or weights.

**Pending public verification:** The repository does not currently contain the separate selection program, per-epoch dev predictions, final adapter hashes, or full inference command-line provenance needed to independently trace the official checkpoint. The public seal summary lists the epoch and dev Macro-F1 but not InternLM3 checkpoint-file hashes. The historical dev-loss configuration should be retained; any future public explanation of the final-stage Macro-F1 selection must identify the later selection step and the provenance of that claim, rather than silently rewriting the old config.

The private-audit report also identifies record limitations: the seed-42 selection stdout log is empty; the seed-2026 independent original epoch-2 directory was lost and reconstructed from surviving copies; and some inference command provenance is incomplete. The seed-7 continuation stdout was recovered and hash-verified in the latest targeted audit; it records batch size 8, 739 skipped rows and 3,479 generated rows. The origin of the first 739 rows and cross-segment checkpoint/tokenizer identity remain unverified. Publicly verifiable status remains limited because the relevant raw outputs, logs and checkpoint weights are not redistributed.

## What is not in this release

- No raw clinical records, individual model outputs or paired case-level comparison files.
- No model weights, adapters, full original training logs or the historical preprocessing script.
- No patient identifiers; case-level resampling cannot account for unknown within-patient correlations.
- No demonstration of clinical efficacy or controlled inference-efficiency benchmarking.
- No claim that this derived task is a direct subset of the source benchmark's normalized 148-class taxonomy.

For source dataset license and acquisition context, see [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) and [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md). This public archive's integrity checks and documentation are not a substitute for scrutiny of the original private evidence when authorized.


Targeted server-side recomputation instructions are available in [TARGETED_RECOMPUTATION_GUIDE.md](TARGETED_RECOMPUTATION_GUIDE.md). The scripts in that guide have been syntax/synthetic-fixture tested but have not been run against the original source splits or the private MacBERT prediction file in this environment.
