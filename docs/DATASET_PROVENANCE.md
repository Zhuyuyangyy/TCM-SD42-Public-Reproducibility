# Dataset provenance

## Source corpus

TCM-SD was introduced by Ren et al. (CCL 2022) as a public benchmark of 54,152 real-world clinical records covering 148 **normalized** syndrome categories. Public records contain an original `syndrome` field and a `norm_syndrome` field after the source benchmark's normalization pipeline.

## TCM-SD42 relationship to TCM-SD

TCM-SD42 is a **derived 42-class task based on TCM-SD clinical records and original syndrome annotations**. The task existed before the comparative experiments in the current study. The fixed label space is stored in `label_space/syndrome_label_list.json`.

The canonical label used by the historical 42-class task is generally the original syndrome string with lightweight string normalization, primarily removal of the trailing `证`. This task taxonomy is therefore **not identical to, and should not be presented as a direct subset of, the official normalized 148-class `norm_syndrome` taxonomy**. Some original syndrome names that remain distinct in TCM-SD42 can map to the same normalized TCM-SD label.

## Frozen comparative partitions

The comparative study used previously established partitions:

- training: 4,186 records
- development: 420 records
- pilot test: 420 records
- same-source full held-out pool: 4,452 records
- primary decontaminated held-out evaluation: 4,218 records

The 4,218 primary test set excludes 234 exact/near-duplicate test records under the frozen text-level decontamination rules used by the study. Exact train/test text overlap after cleaning was zero.

## Historical construction limitation

Older project artifacts refer to a preprocessing script named `prepare_42class.py` and to a historical processed-data directory containing the terms `top50`, `balanced`, and `cap1000`. The original `prepare_42class.py` is not available in the archived release. Consequently, the exact operational rule by which the historical 42-label task was first established cannot be reconstructed from the surviving public materials and is not fabricated here.

This is a provenance/documentation limitation. It does not change the fact that all models in the present comparison were evaluated on the same frozen label space and splits.
