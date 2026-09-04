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

The historical exact TCM-SD42 construction script is unavailable; therefore this repository cannot promise exact reconstruction of the original 42-class split from the official 148-class release alone.
