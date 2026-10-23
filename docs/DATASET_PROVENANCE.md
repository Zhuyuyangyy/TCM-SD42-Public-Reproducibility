# Dataset provenance

## Source corpus

TCM-SD was introduced by Ren et al. (CCL 2022) as a public benchmark of 54,152 real-world clinical records covering 148 **normalized** syndrome categories. Public records contain an original `syndrome` field and a `norm_syndrome` field after the source benchmark's normalization pipeline.

## TCM-SD42 relationship to TCM-SD

TCM-SD42 is a **derived 42-class task based on TCM-SD clinical records and original syndrome annotations**. It is not the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy.

The historical 42-class task uses a fixed set of source `syndrome` labels with lightweight string-level canonicalization, primarily removal of the trailing Chinese character `证`. Some source syndrome labels that remain distinct in TCM-SD42 can map to the same official `norm_syndrome` category.

## Historical class-selection rule: evidence status

A retained internal `dataset_stats.json` (SHA-256 `5b96b35e77a5a43021658eabe7ede3b7bc149f03ec541373ec4da8f51deda804`; three byte-identical copies were reported) records `raw_label_count=278`, `eligible_label_count=42`, and `selected_label_count=42`. Its `raw_label_count` field is ambiguous against independent source-split reconstruction: the training split contains 278 distinct raw `syndrome` strings, the union of raw strings across train/dev/test contains 282, and the union after removing one trailing `证` contains 278. Therefore the field cannot be assigned a unique counting definition from the retained JSON alone.

Using the current official public source splits (43,180 / 5,486 / 5,486 records), the reported thresholds `train>=100, dev>=10, test>=10` select 43 eligible raw strings. Removing one trailing `证` from the selected eligible strings merges `正虚瘀结证` and `正虚瘀结`, yielding the same 42-label canonical vocabulary as the frozen task. The top-50 cap is not binding in this reconstruction (43 eligible raw strings < 50). This independently reproduces the canonical label set under the reported rule; it does not prove that the exact same code ran in May 2026.

Before the training cap, the selected-label source counts total 39,072 training records, 4,902 development records and 4,912 test records. Applying a 1,000-per-canonical-label training cap yields 19,352 training records. These values do not reproduce the internal summary's downstream counts of 19,125 / 4,411 / 4,452. The missing historical preprocessing/deduplication script and full pair-level artifacts prevent reconstruction of the additional differences (227 / 491 / 460 records). The frozen downstream support table itself sums to 19,125 / 4,411 / 4,452, with per-class minima 111 / 10 / 13; those counts are verified for the frozen derived artifacts, not independently reproduced from the official source splits.

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
