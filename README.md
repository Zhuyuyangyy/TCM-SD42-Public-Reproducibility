# TCM-SD42: Controlled Model Comparison for TCM Syndrome Differentiation

Public reproducibility materials for the study:

**Domain-Specific Pretraining versus Large Language Models for Traditional Chinese Medicine Syndrome Differentiation: A Controlled Evaluation on TCM-SD42**

## Scope

This repository documents a **previously established, fixed 42-class syndrome differentiation task derived from clinical records in the public TCM-SD corpus**. It is important that **TCM-SD42 is not described as a direct 42-label subset of the official normalized 148-class TCM-SD benchmark taxonomy**. TCM-SD contains original `syndrome` annotations and an official normalized `norm_syndrome` label space; the historical TCM-SD42 task uses a fixed set of original syndrome labels with lightweight canonicalization (primarily removal of the trailing Chinese character `证`).

The comparative experiments reported here keep the TCM-SD42 label space and data partitions fixed across all models.

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

## Important provenance limitation

The historical preprocessing program that originally established the exact TCM-SD42 42-class construction (`prepare_42class.py`, referenced by older training code) is not present in the archived public materials. Therefore this repository does **not** claim a fully reconstructed 148-to-42 selection algorithm. The 42-class task predates the present comparative experiments and was held fixed throughout them.

## Citation

Please cite the original TCM-SD paper when using the source dataset or ZY-BERT. A citation entry for the present study should be added after the final author list and publication/preprint identifier are available.

## License

Original code in this repository is released under the MIT License. TCM-SD data are not included and remain subject to the source dataset license; see `DATA_LICENSE_NOTICE.md`.
