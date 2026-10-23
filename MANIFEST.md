# Manifest

This repository contains public, aggregate, non-patient-level reproducibility materials for the TCM-SD42 controlled model comparison. Private clinical records, case-level predictions, model weights, and private operational logs are not included.

## Root files

- .gitignore
- CITATION.cff.template
- DATA_LICENSE_NOTICE.md
- LICENSE
- README.md
- VERSION_20261022.md
- requirements.txt

## Code

- code/audit_leakage.py — recovered four-layer leakage-audit reference implementation; private inputs required
- code/build_four_model_clean4218.py — alignment builder; requires authorized local evidence paths
- code/evaluate.py
- code/infer_encoder.py
- code/infer_llm.py
- code/labels_42.txt
- code/pairwise_stats.py — paired accuracy bootstrap and exact McNemar; choices-based bootstrap index generator
- code/recompute_pairwise_stats.py — aggregate duplicate-sensitivity computation; requires authorized local predictions
- code/verify_exclusion_set.py — exclusion-ID verification; requires authorized private split and pair inputs
- code/verify_four_model_alignment.py — frozen-metric alignment gate; requires authorized local inputs
- code/verify_public_aggregates.py — public aggregate consistency checks only
- code/pairwise_class_sensitive_bootstrap.py — ordinary and class-stratified paired bootstrap
- code/parse_label.py
- code/parser_tests.py
- code/train_encoder.py
- code/train_llm_lora.py

## Configurations

- configs/encoder_zybert.json
- configs/internlm3_lora_module_mapping.json
- configs/internlm3_training_protocol.json
- configs/sft_internlm3.json
- configs/sft_qwen3_frozen_reference.json

## Data documentation only

- data/README.md
- data/schema_example.json — synthetic schema example only; no real clinical record

## Provenance and methods documentation

- docs/DATASET_PROVENANCE.md
- docs/DATA_AVAILABILITY.md
- docs/EVIDENCE_MAP.md
- docs/KNOWN_LIMITATIONS.md
- docs/LEAKAGE_AUDIT_METHOD.md
- docs/METHODS_SUMMARY.md
- docs/PROVENANCE_EVIDENCE.md
- docs/RESULTS_SUMMARY.md
- docs/SOURCE_REFERENCES.md
- docs/STATISTICAL_METHOD.md
- docs/QWEN3_STAGE2_SEMANTICS.md
- docs/SEED7_INFERENCE_PROVENANCE.md
- docs/DATA_QUALITY_SUMMARY.md

## Label space

- label_space/label_mapping_public.json
- label_space/syndrome_label_list.json

## Results

- results/clean4218_seed42.csv
- results/confusion_matrix_internlm3.csv
- results/confusion_matrix_macbert.csv
- results/confusion_matrix_qwen3.csv
- results/confusion_matrix_zybert.csv
- results/dedup_sensitivity_seed42.csv — aggregate results for primary, raw-text deduplicated and normalized-text sensitivity subsets
- results/figures/figure1_overall_performance.png
- results/figures/figure2_seed_robustness.png
- results/internlm3_3seed_metrics.json
- results/pairwise_balanced_accuracy_bootstrap_seed42.csv
- results/pairwise_class_sensitive_bootstrap_seed42.csv
- results/pairwise_class_sensitive_stratified_bootstrap_seed42.csv
- results/pairwise_macro_f1_bootstrap_seed42.csv
- results/pairwise_significance_seed42.csv
- results/three_seed_summary.csv
- results/zybert_3seed_metrics.json

## Run-level provenance

- provenance/README.md
- provenance/seal_summary.json

## Figure sources

- figures_r/reproduce_figures.R

## Manuscript note

- paper/README.md — the full draft is intentionally not included in this public repository.

## Explicit exclusions

The public repository does not contain raw TCM-SD clinical records, per-case prediction files, raw generated outputs, trained model/adapter weights, private compute paths, the private near-duplicate pair table, or full operational logs. The internal dataset_stats.json used to document the reported 278/42 counts is not included.

- `code/recompute_tcm_sd42_label_selection.py` — recomputes raw-label support thresholds from official source splits; emits aggregate counts only
- `code/recompute_macbert_frozen_metrics.py` — recomputes MacBERT clean-test metrics from frozen positional predictions; requires authorized local inputs
- `docs/TARGETED_RECOMPUTATION_GUIDE.md` — commands and evidence boundaries for source-split and MacBERT metric checks
- `docs/TARGETED_CHECKS_20261023.md` — results of the 2026-10-23 real-input targeted audit
- `docs/HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md` — early pilot artifact hashes, evaluator mismatch, source-split count reconciliation, and remaining evidence limits