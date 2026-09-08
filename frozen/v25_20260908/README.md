# TCM-SD42 experiment freeze — v25 (2026-09-08)

This directory records the **frozen experimental state** used by the v25 manuscript revision. It is a snapshot of the public reproducibility repository plus a machine-readable summary of the frozen numerical results and protocol.

## Freeze identity

- Freeze branch: `freeze/v25-20260908`
- Source `main` commit used as the snapshot base: `a9993382f0ab072d85bfc773ebbeba030444d921`
- Freeze date: 2026-09-08
- Manuscript file: `TCM_SD42_SCI_Manuscript_v25_scientific_skill_optimized.docx`
- Manuscript SHA-256: `5c7eab5961f7987464b50ac94273dd80d198d28973bed45e4bdc42d67c4cabb8`

The exact Git commit at the head of this freeze branch is the canonical identifier for this frozen state. Subsequent experimental revisions should use a new version/branch rather than overwriting these values.

## Frozen task definition

The study evaluates a **TCM-SD-derived 42-class raw-label syndrome-differentiation task**. It is not the official normalized 148-class TCM-SD benchmark. The supplementary taxonomy audit found 38 identity-preserved mappings and four merge/rename mappings; two raw-label pairs collapse under normalization, so the 42 frozen labels correspond to **40 distinct normalized categories** in the audited public mapping resource.

Historical class eligibility was defined before the present four-model comparison using source-support thresholds of >=100 training, >=10 development, and >=10 source-test records. Because source-test label counts contributed to historical class eligibility, the taxonomy construction is explicitly treated as **test-informed at the label-support level**.

## Frozen data counts

- Training: 4,186 records
- Development: 420 records
- Source held-out pool before decontamination: 4,452 records
- Primary clean held-out test: 4,218 records
- Held-out records excluded by the frozen exact/near-duplicate union: 234 unique records

## Frozen leakage-audit protocol

Exact held-out exclusions are based on SHA-256 equality of raw `input_text` against training, development, or pilot records. Near-duplicate screening standardizes text by removing case identifiers, digits, punctuation/whitespace, and fixed template prefixes, then fits one TF-IDF vectorizer over all compared splits with:

- `analyzer="char_wb"`
- `ngram_range=(2,4)`
- `min_df=2`
- `sublinear_tf=True`
- `norm="l2"`
- `max_features=200000`
- primary cosine-similarity exclusion threshold: `>=0.95`

The reconstructed held-out exclusion union contains 234 unique records and matches the 4,452 -> 4,218 record-ID difference exactly. A separate train-development audit identified 54 development instances in >=0.95-similarity pairs, including 18 exact duplicates; the ZY-BERT sensitivity analysis reduced development Macro-F1 from 0.8056 to 0.7742 after removing overlap-affected development instances.

## Frozen seed-42 results (clean N=4,218)

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced accuracy | Accuracy 95% CI |
|---|---:|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% | 74.47-77.05 |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% | 68.23-70.93 |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% | 61.24-64.20 |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% | 57.23-60.19 |

## Frozen three-seed robustness

Seeds: 42, 2026, 7.

- ZY-BERT accuracy: 75.77%, 75.34%, 73.64% -> **74.92 +/- 1.13%**
- ZY-BERT Macro-F1: **66.06 +/- 0.66%**
- ZY-BERT Weighted-F1: **77.17 +/- 1.10%**
- ZY-BERT Balanced accuracy: **78.81 +/- 1.06%**
- InternLM3-8B accuracy: 69.58%, 69.49%, 69.18% -> **69.42 +/- 0.21%**
- InternLM3-8B Macro-F1: **60.89 +/- 0.31%**
- InternLM3-8B Weighted-F1: **72.16 +/- 0.11%**
- InternLM3-8B Balanced accuracy: **73.81 +/- 0.40%**
- Three-seed mean accuracy gap (ZY-BERT minus InternLM3-8B): **5.50 percentage points**

## Frozen statistical inference

Paired analyses use the same 4,218 seed-42 cases. Accuracy inference uses 2,000 paired bootstrap resamples with seed 20260516, exact two-sided McNemar tests, and Holm correction across six pairwise accuracy comparisons. Macro-F1 and balanced-accuracy differences use paired bootstrap 95% confidence intervals, with a class-stratified paired-bootstrap sensitivity analysis.

All six seed-42 pairwise accuracy comparisons remain significant after Holm correction. All six Macro-F1 paired-bootstrap intervals exclude zero. Five of six balanced-accuracy intervals exclude zero; **InternLM3-8B vs MacBERT balanced accuracy is the exception** (+0.92 percentage points, 95% CI -1.46 to 3.31).

## Interpretation boundary

These frozen results support a **system-level comparison within this fixed 42-class task**. They do not isolate architecture, parameter scale, pretraining corpus, or domain pretraining as single causal factors; they do not establish that encoder models universally outperform LLMs; and they must not be described as a direct evaluation on the official normalized 148-class TCM-SD benchmark.

## Public-data boundary

This freeze does not add raw clinical records, per-case predictions, trained weights, or private compute logs. Existing data-license and availability notices in the repository continue to apply.
