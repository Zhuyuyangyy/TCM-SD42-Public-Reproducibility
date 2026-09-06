# Dataset provenance

## Source corpus

TCM-SD was introduced by Ren et al. (CCL 2022) as a public benchmark of 54,152 real-world clinical records covering 148 **normalized** syndrome categories. Public records contain an original `syndrome` field and a `norm_syndrome` field after the source benchmark's normalization pipeline.

## TCM-SD42 relationship to TCM-SD

TCM-SD42 is a **derived 42-class task based on TCM-SD clinical records and original syndrome annotations**. It is not the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy.

The historical 42-class task uses a fixed set of source `syndrome` labels with lightweight string-level canonicalization, primarily removal of the trailing Chinese character `证`. Some source syndrome labels that remain distinct in TCM-SD42 can map to the same official `norm_syndrome` category.

## Recovered historical class-selection rule

A surviving preprocessing log dated 2026-05-07 records the operational rule used in the historical Top-N preprocessing stage. The source split contained 278 distinct original syndrome labels. A syndrome category was eligible if it had at least:

- 100 records in the source training split,
- 10 records in the source development split, and
- 10 records in the source test split.

Exactly **42 original syndrome categories** satisfied all three minimum-support criteria. The subsequent `top50` step therefore retained all 42 eligible categories rather than 50. The same log records the following post-deduplication counts for the 42-class `top50_full` version:

- training: 39,072 records,
- development: 4,411 records,
- test: 4,452 records.

For the `top50_balanced_cap1000` version, only the training split was capped at 1,000 records per class, yielding 19,125 training records while development and test remained 4,411 and 4,452.

This construction predates the present four-model comparison. The surviving log recovers the operational support thresholds, although the original preprocessing source file is not included in the current public package.

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

The current archive preserves the fixed label list, downstream split definitions, aggregate evaluation evidence, and the historical preprocessing log, but not the original preprocessing source file that implemented the support-threshold rule. Patient identifiers are also unavailable in the frozen derived files, so patient-disjoint partitions cannot be established; the study verifies text-level decontamination rather than patient-level independence.
