# Results summary

## Seed-42 primary comparison (clean N=4,218)

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced Acc. | Accuracy 95% CI |
|---|---:|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% | [74.47, 77.05] |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% | [68.23, 70.93] |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% | [61.24, 64.20] |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% | [57.23, 60.19] |

## Three-seed robustness

- ZY-BERT accuracy: **74.92 ± 1.13%**
- ZY-BERT Macro-F1: **66.06 ± 0.66%**
- InternLM3-8B accuracy: **69.42 ± 0.21%**
- InternLM3-8B Macro-F1: **60.89 ± 0.31%**

Mean accuracy gap (ZY-BERT minus InternLM3-8B): approximately **5.50 percentage points**.

## Pairwise significance
All six seed-42 pairwise accuracy comparisons remain statistically significant after Holm correction. Exact values are in `results/pairwise_significance_seed42.csv`.

## Interpretation boundary
These results support a domain-specific pretraining advantage **within this fixed TCM-SD-derived 42-class setting**. They do not establish that encoder models universally outperform LLMs, and they should not be represented as a complete evaluation on the official normalized 148-class TCM-SD benchmark.
