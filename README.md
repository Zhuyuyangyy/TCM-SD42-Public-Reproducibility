# TCM-SD42: Controlled Model Comparison for TCM Syndrome Differentiation

Public reproducibility materials for the study:

**Domain-Specific Pretraining versus Large Language Models for Traditional Chinese Medicine Syndrome Differentiation: A Controlled Evaluation on a TCM-SD-Derived 42-Class Task**

## Scope

This repository documents a **previously established, fixed 42-class syndrome differentiation task derived from clinical records in the public TCM-SD corpus**. TCM-SD42 is **not** the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy. TCM-SD contains original `syndrome` annotations and an official normalized `norm_syndrome` label space; the historical TCM-SD42 task uses a fixed set of original syndrome labels with lightweight canonicalization, primarily removal of the trailing Chinese character `证`.

A surviving preprocessing log dated 2026-05-07 records the historical eligibility rule: source syndrome categories were retained when they had at least **100 training records, 10 development records, and 10 test records** in the original TCM-SD splits. Exactly **42** original syndrome categories met all three thresholds. This construction predates the present four-model comparison and did not use model predictions or model performance. Because test-label support contributed to the historical eligibility rule, this is disclosed as a test-informed task-construction limitation.

The comparative experiments reported here keep the resulting TCM-SD42 label space and data partitions fixed across all models.

## Models

- MacBERT (`hfl/chinese-macbert-base`) — discriminative encoder
- ZY-BERT — TCM domain-specific encoder introduced with TCM-SD
- Qwen3-8B — generative LLM, frozen historical QLoRA-SFT protocol
- InternLM3-8B-Instruct — generative LLM, QLoRA-SFT under the locked comparative protocol

## Main clean held-out results (N = 4,218, seed 42)

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced Accuracy |
|---|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% |

Three-seed summaries for ZY-BERT and InternLM3-8B are under `results/three_seed_summary.csv`. Pairwise accuracy comparisons use paired bootstrap confidence intervals, exact McNemar tests, and six-comparison Holm correction.

## Repository contents

```text
code/          parser, evaluator, training/inference reference scripts, pairwise statistics
configs/       model/protocol snapshots
label_space/   fixed 42-label taxonomy
results/       aggregate metrics, seed summaries, confusion matrices, figures
docs/          provenance, methods, results, limitations, availability statements
data/          schema only; no clinical records
paper/         manuscript-publication note; full draft intentionally not included
```

## Why raw records and predictions are not here

This release intentionally excludes raw clinical records, per-case predictions, trained model weights, private compute paths, and operational logs. The source TCM-SD dataset can be obtained from its official release. See `DATA_LICENSE_NOTICE.md` and `docs/DATA_AVAILABILITY.md`.

## Quick checks

```bash
pip install -r requirements.txt
python code/parser_tests.py
```

To recompute metrics from standardized prediction files (`id`, `gold`, `pred`), use `code/evaluate.py`. For pairwise accuracy comparisons, use `code/pairwise_stats.py`.

## Provenance notes

The historical support-threshold rule is recoverable from surviving preprocessing logs, but the original preprocessing source file is not included in the public package. The exact 42-label task predates the current comparative experiments and was held fixed throughout them. See `docs/DATASET_PROVENANCE.md` and `docs/KNOWN_LIMITATIONS.md` for the full audit trail and limitations.

## Citation

Please cite the original TCM-SD paper when using the source dataset or ZY-BERT. A citation entry for the present study should be added after the final author list and publication/preprint identifier are available.

## License

Original code in this repository is released under the MIT License. TCM-SD data are not included and remain subject to the source dataset license; see `DATA_LICENSE_NOTICE.md`.
