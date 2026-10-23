# TCM-SD42: Controlled Model Comparison for TCM Syndrome Differentiation

> **Research archive / Medical NLP / Reproducibility**  
> A controlled, system-level comparison of specialized encoders and general-purpose language models for traditional Chinese medicine syndrome differentiation.

### At a glance

| Study dimension | What is actually evaluated |
| --- | --- |
| Task | Fixed historical **42-class task derived from TCM-SD** |
| Models | ZY-BERT, MacBERT, Qwen3-8B and InternLM3-8B-Instruct |
| Clean held-out split | **4,218 records**, seed 42 |
| Strongest reported baseline in this comparison | **ZY-BERT: 75.77% accuracy / 66.51% macro-F1** |
| Evidence | Evaluation scripts, aggregate results, statistical tests, provenance and known limitations |

**Start with the evidence:** [Results summary](docs/RESULTS_SUMMARY.md) · [Methods](docs/METHODS_SUMMARY.md) · [Statistical tests](docs/STATISTICAL_METHOD.md) · [Dataset provenance](docs/DATASET_PROVENANCE.md) · [Known limitations](docs/KNOWN_LIMITATIONS.md) · [Data availability](docs/DATA_AVAILABILITY.md).

> [!IMPORTANT]
> This is **not** the official normalized 148-class TCM-SD benchmark. The fixed historical task has a disclosed test-informed eligibility rule. The public release intentionally does not include raw clinical records, per-case predictions or trained weights. Interpret the numbers and reproducibility scope in that context.

---

Public reproducibility materials for the study:

**Domain-Specific Encoders versus General-Purpose Large Language Models for Traditional Chinese Medicine Syndrome Differentiation: A Controlled System-Level Evaluation on a TCM-SD-Derived 42-Class Task**

## Read the evidence first

The results below are **historical reported results** on a fixed TCM-SD-derived 42-class task, not a new run or a clinical validation. Start with the [claim-to-evidence map](docs/EVIDENCE_MAP.md), which clearly separates what can be verified from public aggregates from what still requires the original authorized records and checkpoints.

![Four-model seed-42 results](results/figures/figure1_overall_performance.png)

*Existing repository figure, reproduced from published aggregate results; not evidence of a new training run.*

**Reproducibility level:** **Public aggregate consistency check available**; full model training, case-level paired analysis, checkpoint identity, and split reconstruction are **not independently reproducible from this public repository alone**.

Run the read-only check on the published matrices, fixed label vocabulary, per-seed summaries, and the six McNemar/Holm calculations:

```bash
python code/verify_public_aggregates.py
```

This script uses only Python's standard library. A **PASS** means the disclosed aggregate tables agree internally; it does **not** verify case-level predictions, raw clinical records, resampling confidence intervals, checkpoints, or patient independence. See [the evidence map](docs/EVIDENCE_MAP.md) for the complete scope.

![ZY-BERT and InternLM3 three-seed robustness](results/figures/figure2_seed_robustness.png)

*Existing repository figure; three seeds per displayed system. Do not interpret this as a four-model three-seed comparison.*

**Important reporting detail:** Each LLM's published 42×42 confusion matrix contains **4,216 valid-label outputs**, not all **4,218** test cases. The two omitted outputs per model were recorded as non-parsed (`empty`) and count as incorrect against the full denominator. The [evidence map](docs/EVIDENCE_MAP.md#why-the-llm-4242-confusion-matrices-have-4216-entries) shows how to correctly reconstruct Macro-F1 and Balanced Accuracy without silently discarding cases.

**Checkpoint disclosure:** The public InternLM3 *training-time* script saves by Stage-2 dev loss; an author-reported private archive audit describes a separate *official inference* selection by dev Macro-F1 that chose the same epoch-2 adapters for all three seeds. The full separate selection and checkpoint hashes are **not yet available publicly**, so the public archive cannot independently validate that step. See [checkpoint provenance](docs/EVIDENCE_MAP.md#checkpoint-protocol-do-not-conflate-two-stages).

**Qwen3 checkpoint-state disclosure:** the early pilot archive contains the historical TCM-Mini-best adapter (SHA-256 `a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf`, matching its retained checksum) and the 4,452-row raw-output artifact (SHA-256 `9a02eca7394a599ead9db00c80bb16803c63dedf203bae9d4f8c644523c07042`, matching the historical inventory). This establishes the existence and integrity of the early pilot artifacts, but the original inference command and per-record input hashes are absent, so the exact output-to-checkpoint link remains incomplete. The two Stage-2 epoch adapters needed for saved-state epoch comparison were not found in the latest server audit. The Stage-2 optimizer included 168,960 fp32 Norm parameters that the adapter-only save routine does not serialize. The development loss used for epoch selection was computed on the in-memory state with those Norm parameters enabled, whereas held-out inference uses base Norm weights plus LoRA. This selection-time/evaluated-artifact mismatch is documented in [Qwen3 Stage-2 semantics](docs/QWEN3_STAGE2_SEMANTICS.md); it does not change the frozen reported metrics, but it limits claims of a fully matched selection/inference state.

## Scope

This repository documents a **previously established, fixed 42-class syndrome differentiation task derived from clinical records in the public TCM-SD corpus**. TCM-SD42 is **not** the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy. TCM-SD contains original `syndrome` annotations and an official normalized `norm_syndrome` label space; the historical TCM-SD42 task uses a fixed set of original syndrome labels with lightweight canonicalization, primarily removal of the trailing Chinese character `证`.

A retained internal `dataset_stats.json` reports `raw_label_count=278` and 42 eligible/selected labels, but the counting stage of the 278 field is ambiguous: independent reconstruction finds 278 raw strings in train, 282 in the raw three-split union, and 278 after trailing-`证` canonicalization. On the current official source splits, the stated thresholds select 43 raw strings; removing one trailing `证` merges two into the frozen 42-label vocabulary. This reconstructs the label set under the reported rule but does not prove the exact historical execution. The retained duplicate counts reconcile Dev and Test to 4,411 and 4,452 (453 Dev/Train removals, 460 Test/Train removals, and 38 additional Dev/Test removals). The 1,000-per-class capped source Train count is 19,352, while the frozen Train artifact has 19,125; this 227-record gap remains unexplained because the historical preprocessing script and pair-level artifacts were not recovered. Because source test-label support contributed to the reported rule, task construction is disclosed as test-informed.

The comparative experiments reported here keep the resulting TCM-SD42 label space and data partitions fixed across all models.

## Models

- MacBERT (`hfl/chinese-macbert-base`) — discriminative encoder
- ZY-BERT — TCM domain-specific encoder introduced with TCM-SD
- Qwen3-8B — generative LLM, frozen historical QLoRA-SFT protocol
- InternLM3-8B-Instruct — generative LLM, QLoRA-SFT under a locked design protocol with a disclosed layer-freezing execution deviation (see the protocol JSON and known limitations)

## Main clean held-out results (N = 4,218, seed 42)

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced Accuracy |
|---|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% |

Three-seed summaries for ZY-BERT and InternLM3-8B are under `results/three_seed_summary.csv`. Pairwise accuracy comparisons use paired bootstrap confidence intervals, exact McNemar tests, and six-comparison Holm correction.

The v23 statistical addendum additionally reports paired-bootstrap 95% confidence intervals for **Macro-F1** and **Balanced Accuracy** differences. All six Macro-F1 intervals exclude zero. Five of six Balanced Accuracy intervals exclude zero; the InternLM3-versus-MacBERT difference is +0.92 percentage points with 95% CI [-1.46, 3.31]. A class-stratified paired-bootstrap sensitivity analysis preserves the direction of all 12 class-sensitive comparisons and the same qualitative exception. See the ordinary and stratified tables under `results/`, the portable scripts under `code/`, and `docs/STATISTICAL_METHOD.md`.

## Repository contents

```text
code/          parser, evaluator, leakage audit, training/inference reference scripts, pairwise statistics and audit gates
configs/       model/protocol snapshots
label_space/   fixed 42-label taxonomy
results/       aggregate metrics, seed summaries, confusion matrices, bootstrap summaries, figures
docs/          provenance, methods, statistical methods, results, limitations, availability statements
provenance/    sanitized run-level seals and artifact provenance summaries
data/          schema only; no clinical records
paper/         manuscript-publication note; full draft intentionally not included
```

## Why raw records and predictions are not here

This release intentionally excludes raw clinical records, per-case predictions, trained model weights, private compute paths, and operational logs. The source TCM-SD dataset can be obtained from its official release. See `DATA_LICENSE_NOTICE.md` and `docs/DATA_AVAILABILITY.md`.

## Targeted historical checks

Two additional scripts are provided for authorized local use: `code/recompute_tcm_sd42_label_selection.py` recomputes the historical support-threshold rule from the official raw source splits, and `code/recompute_macbert_frozen_metrics.py` recomputes MacBERT metrics from its frozen 4,452-row prediction file after checking alignment to the clean 4,218 records. Neither the raw source splits nor the per-case prediction file is distributed here. Instructions and limits are in [docs/TARGETED_RECOMPUTATION_GUIDE.md](docs/TARGETED_RECOMPUTATION_GUIDE.md). The 2026-10-23 server audit reports MacBERT metric recomputation PASS (8/8 structural checks; 62.778568/56.811275/63.944848/72.628728% on n=4,218). The source-split reconstruction reports a 42-label canonical set match but does not reproduce downstream support totals (PARTIAL). The scripts in this public branch are intended to preserve those checks; verify their SHA-256 against the server audit before claiming the exact same script produced the reported run.

## Quick checks

```bash
pip install -r requirements.txt
python code/parser_tests.py
python code/verify_public_aggregates.py
```

The public aggregate verification script checks the frozen label order, confusion-matrix counts, reported aggregate metrics, three-seed summaries, and the published McNemar/Holm table. A PASS establishes internal consistency of public aggregate files; it does not reproduce model training, case-level predictions, private exclusion inputs, or checkpoints.

To recompute metrics from standardized prediction files (`id`, `gold`, `pred`), use `code/evaluate.py`. For the published pairwise summaries, see the files under `results/` and the methodology under `docs/STATISTICAL_METHOD.md`.

## Recovered provenance evidence

The historical four-layer leakage-audit implementation was recovered and is published as `code/audit_leakage.py`. The v23 class-sensitive statistics addendum was also recovered; its ordinary and class-stratified aggregate tables and portable verification scripts are included here. The run-level seal coverage and the remaining evidence gap are summarized in `docs/PROVENANCE_EVIDENCE.md` and `provenance/seal_summary.json`.

The original `preprocess_tcm_sd_v4_topn.py` source, complete source-label frequency table and contemporaneous execution log were not recovered. The support-threshold rule is documented only as a secondary description reported by an internal `dataset_stats.json` and project notes; it is not presented as a surviving log or as independently verified execution evidence.

## Provenance notes

The exact 42-label task predates the current comparative experiments and was held fixed throughout them. See `docs/DATASET_PROVENANCE.md`, `docs/PROVENANCE_EVIDENCE.md`, and `docs/KNOWN_LIMITATIONS.md` for the full audit trail and limitations.

## 2026-10-22 evidence-alignment update

The public archive now distinguishes historical design from verified execution. See [Qwen3 Stage-2 semantics](docs/QWEN3_STAGE2_SEMANTICS.md), [Seed-7 inference provenance](docs/SEED7_INFERENCE_PROVENANCE.md), [data-quality summary](docs/DATA_QUALITY_SUMMARY.md), and the [claim-to-evidence map](docs/EVIDENCE_MAP.md). The public repository does not contain the private clinical inputs, per-case predictions, near-duplicate pair file or model weights needed to rerun every historical audit locally. The 4,218-case aggregate checks can be run with `python code/verify_public_aggregates.py`; a PASS validates public aggregate consistency, not end-to-end training reproduction.

## Citation

Please cite the original TCM-SD paper when using the source dataset or ZY-BERT. A citation entry for the present study should be added after the final author list and publication/preprint identifier are available.

## License

Original code in this repository is released under the MIT License. TCM-SD data are not included and remain subject to the source dataset license; see `DATA_LICENSE_NOTICE.md`.


**Historical pilot-evaluator boundary:** the early Pilot-SFT v14 evaluation used alias-equivalence for top-1 correctness (including an alias mapping between two distinct frozen labels) while its F1 metrics used alias-normalized predictions against raw gold labels. Those pilot aggregate metrics are not reused in the present four-system comparison. The early archive's raw-output file was independently re-parsed with the current exact-label parser as a provenance check; this was not a new inference run. Details are in [the historical evidence reconciliation](docs/HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md).
