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

An internal `dataset_stats.json` reports 278 raw labels and 42 eligible/selected labels under the historical train>=100, dev>=10, test>=10, top-50 rule (SHA-256 recorded in `docs/DATASET_PROVENANCE.md`). A copy of `preprocess_tcm_sd_v4_topn.py` has since been recovered in the private local evidence archive, but it is not redistributed here because it contains fixed private runtime paths and expects licensed source data at those paths. The original stdout, complete historical source-label frequency table, and intermediate downstream training-cleaning output remain unavailable. A read-only source-split reconstruction distinguishes 278 raw strings in Train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization; 43 eligible raw strings normalize to the frozen 42 labels. Thus the label set can be reconstructed, but the summary field raw_label_count=278 is scope-ambiguous, the 227-record post-cap difference is explained by the canonical-first reconstruction, while the exact historical execution order remains unproven because the contemporaneous stdout and complete source-label frequency table are unavailable, and the exact historical threshold/cap execution cannot be proven from this public repository. TCM-SD42 is not reconstructable by selecting 42 labels directly from the official normalized 148-class taxonomy because it is based on original `syndrome` annotations rather than the normalized `norm_syndrome` label space.
