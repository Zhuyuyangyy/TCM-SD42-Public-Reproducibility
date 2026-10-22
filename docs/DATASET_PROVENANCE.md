# Dataset provenance

## Source corpus

TCM-SD was introduced by Ren et al. (CCL 2022) as a public benchmark of 54,152 real-world clinical records covering 148 **normalized** syndrome categories. Public records contain an original `syndrome` field and a `norm_syndrome` field after the source benchmark's normalization pipeline.

## TCM-SD42 relationship to TCM-SD

TCM-SD42 is a **derived 42-class task based on TCM-SD clinical records and original syndrome annotations**. It is not the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy.

The historical 42-class task uses a fixed set of source `syndrome` labels with lightweight string-level canonicalization, primarily removal of the trailing Chinese character `证`. Some source syndrome labels that remain distinct in TCM-SD42 can map to the same official `norm_syndrome` category.

## Historical class-selection rule: evidence status

A retained **internal** `dataset_stats.json` (SHA-256 `5b96b35e77a5a43021658eabe7ede3b7bc149f03ec541373ec4da8f51deda804`; three byte-identical copies were reported in the internal archive) records `raw_label_count=278`, `eligible_label_count=42`, and `selected_label_count=42`. It reports the criterion `train>=100, dev>=10, test>=10, top-50 by total`, with raw split totals of 43,180 / 5,486 / 5,486 and final split totals of 19,125 / 4,411 / 4,452.

The original `preprocess_tcm_sd_v4_topn.py`, complete source-label frequency table, and contemporaneous execution log were not recovered. Thus, 278 is a retained summary-file value, not an independently recomputed count; the exact historical threshold implementation and uniqueness of the 42-class selection remain unverified. The final 42-label vocabulary and its downstream support totals can be checked against the frozen files. The top-50 cap was not reached in the reported summary (42 selected versus a cap of 50), but that arithmetic alone does not independently prove that exactly 42 source labels passed the thresholds.

The later `top50_balanced_cap1000` summary reports 19,125 training, 4,411 development and 4,452 test records. The comparative package subsequently used a 4,186-record training subset and a 420-record balanced development subset, while retaining the 4,452-record source test pool before decontamination.

### Important design limitation

Because the historical eligibility rule used class-support counts from the original **training, development, and test splits**, the task definition was informed by test-label frequency. This did not use model predictions, model errors, or any result from the current four-model comparison, and the 42-label task was fixed long before the present evaluation. Nevertheless, this constitutes a historical **test-informed task-construction choice** and should be considered when interpreting generalizability.

## Frozen comparative partitions

The comparative study used previously established downstream partitions:

- training: 4,186 records,
- development: 420 records,
- pilot test: 420 records,
- same-source full held-out pool: 4,452 records,
- primary decontaminated held-out evaluation: 4,218 records.

The 4,218 primary test set excludes 234 exact/near-duplicate records from the 4,452-record held-out pool under the frozen text-level decontamination procedure. Exact train/test text overlap after cleaning was zero.

## Development-overlap audit

A separate audit identified 54 development instances involved in train-development pairs with similarity >=0.95; 18 were exact duplicates. In a ZY-BERT sensitivity analysis, removing the overlap-affected development instances reduced development macro-F1 from 0.8056 to 0.7742. The clean held-out test set, rather than development performance, is therefore treated as the principal evidence of generalization.

## Remaining provenance limitations

The public archive preserves the fixed label list, downstream split definitions, aggregate evaluation evidence, and the recovered four-layer leakage-audit implementation (`code/audit_leakage.py`), but it does not include the internal `dataset_stats.json`, the original preprocessing source file, a complete source-label frequency table, or a contemporaneous preprocessing execution log. The internal summary-file report is described above; it must not be presented as a surviving public preprocessing log. Patient identifiers are also unavailable in the frozen derived files, so patient-disjoint partitions cannot be established; the study verifies text-level decontamination rather than patient-level independence. See `docs/PROVENANCE_EVIDENCE.md` for the recovery record and the remaining seal gap for the two historical seed-42 baselines.
