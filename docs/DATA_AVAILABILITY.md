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

A surviving historical preprocessing log recovers the operational class-eligibility rule used to establish the 42-label task (minimum support of 100/10/10 records in the original train/development/test splits, respectively). The original preprocessing source file itself is not included in the public package, and TCM-SD42 is not reconstructable by selecting 42 labels directly from the official normalized 148-class taxonomy because it is based on original `syndrome` annotations rather than the normalized `norm_syndrome` label space.
