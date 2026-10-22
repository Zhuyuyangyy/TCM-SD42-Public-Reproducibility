# Data availability

Raw TCM-SD clinical records are **not redistributed in this repository**. The source TCM-SD dataset is publicly released by the original authors; obtain it from the official TCM-SD / ZY-BERT resources and comply with the source license.

This repository releases:
- the fixed 42-label task vocabulary
- aggregate model metrics
- three-seed summaries
- aggregate confusion matrices
- figures
- parser/evaluator and reference training/inference scripts
- model/protocol configuration snapshots
- provenance and limitation documentation

This repository intentionally does not release:
- raw clinical case JSON files
- per-case predictions or raw generated outputs
- model weights or LoRA adapters
- private compute paths and operational logs

An internal `dataset_stats.json` reports 278 raw labels and 42 eligible/selected labels under the historical train>=100, dev>=10, test>=10, top-50 rule (SHA-256 recorded in `docs/DATASET_PROVENANCE.md`). The original preprocessing script, complete source-label frequency table and contemporaneous execution log were not recovered; the 278 count and historical threshold execution therefore cannot be independently reconstructed from this public repository. TCM-SD42 is not reconstructable by selecting 42 labels directly from the official normalized 148-class taxonomy because it is based on original `syndrome` annotations rather than the normalized `norm_syndrome` label space.
