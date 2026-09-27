# Manifest

This repository contains public, aggregate, non-patient-level reproducibility materials for the TCM-SD42 controlled model comparison.

## Root files

- `.gitignore`
- `CITATION.cff.template`
- `DATA_LICENSE_NOTICE.md`
- `LICENSE`
- `README.md`
- `requirements.txt`

## Code

- `code/audit_leakage.py` — recovered four-layer leakage-audit implementation
- `code/build_four_model_clean4218.py` — portable alignment builder; requires authorized local evidence paths
- `code/evaluate.py`
- `code/infer_encoder.py`
- `code/infer_llm.py`
- `code/labels_42.txt`
- `code/pairwise_stats.py`
- `code/pairwise_class_sensitive_bootstrap.py` — ordinary and class-stratified paired bootstrap
- `code/parse_label.py`
- `code/parser_tests.py`
- `code/verify_four_model_alignment.py` — frozen-metric alignment gate
- `code/train_encoder.py`
- `code/train_llm_lora.py`

## Configurations

- `configs/encoder_zybert.json`
- `configs/internlm3_lora_module_mapping.json`
- `configs/internlm3_training_protocol.json`
- `configs/sft_internlm3.json`
- `configs/sft_qwen3_frozen_reference.json`

## Data documentation only

- `data/README.md`
- `data/schema_example.json` — synthetic schema example only; no real clinical record

## Provenance and methods documentation

- `docs/DATASET_PROVENANCE.md`
- `docs/DATA_AVAILABILITY.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/METHODS_SUMMARY.md`
- `docs/PROVENANCE_EVIDENCE.md`
- `docs/RESULTS_SUMMARY.md`
- `docs/SOURCE_REFERENCES.md`

## Label space

- `label_space/label_mapping_public.json`
- `label_space/syndrome_label_list.json`

## Results

- `results/clean4218_seed42.csv`
- `results/confusion_matrix_internlm3.csv`
- `results/confusion_matrix_macbert.csv`
- `results/confusion_matrix_qwen3.csv`
- `results/confusion_matrix_zybert.csv`
- `results/figures/figure1_overall_performance.png`
- `results/figures/figure2_seed_robustness.png`
- `results/internlm3_3seed_metrics.json`
- `results/pairwise_balanced_accuracy_bootstrap_seed42.csv`
- `results/pairwise_class_sensitive_bootstrap_seed42.csv`
- `results/pairwise_class_sensitive_stratified_bootstrap_seed42.csv`
- `results/pairwise_macro_f1_bootstrap_seed42.csv`
- `results/pairwise_significance_seed42.csv`
- `results/three_seed_summary.csv`
- `results/zybert_3seed_metrics.json`

## Run-level provenance

- `provenance/README.md`
- `provenance/seal_summary.json`

## Manuscript note

- `paper/README.md` — the full manuscript is intentionally not included pending journal/preprint-policy decisions.

## Explicit exclusions

The public repository does not contain raw TCM-SD clinical records, per-case prediction files, raw generated outputs, model or adapter weights, private compute paths, operational logs, or the internally identified column-inconsistent per-class F1 CSV.
