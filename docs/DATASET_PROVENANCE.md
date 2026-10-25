# Dataset provenance

## Source corpus

TCM-SD was introduced by Ren et al. (CCL 2022) as a public benchmark of 54,152 real-world clinical records covering 148 **normalized** syndrome categories. Public records contain an original `syndrome` field and a `norm_syndrome` field after the source benchmark's normalization pipeline.

## TCM-SD42 relationship to TCM-SD

TCM-SD42 is a **derived 42-class task based on TCM-SD clinical records and original syndrome annotations**. It is not the official normalized 148-class TCM-SD benchmark and should not be described as a direct 42-label subset of that normalized taxonomy.

The historical 42-class task uses a fixed set of source `syndrome` labels with lightweight string-level canonicalization, primarily removal of the trailing Chinese character `证`. Some source syndrome labels that remain distinct in TCM-SD42 can map to the same official `norm_syndrome` category.

## Historical class-selection rule: evidence status

The retained internal `dataset_stats.json` (three byte-identical copies; SHA-256 `5b96b35e77a5a43021658eabe7ede3b7bc149f03ec541373ec4da8f51deda804`) reports `raw_label_count=278`, `eligible_label_count=42`, and `selected_label_count=42`, with thresholds `train>=100, dev>=10, test>=10` and a top-50-by-total stage.

A 2026-10-23 recomputation against the retrieved public source splits clarifies the label-count scope: the raw training split contains 278 distinct original `syndrome` strings; the union across train/dev/test contains 282 distinct raw strings; after removing a terminal `证`, the normalized union contains 278 labels. Applying the support thresholds to raw strings identifies 43 eligible strings, which map to the frozen 42-label vocabulary after suffix canonicalization. Therefore, 278 is not an unambiguous all-split raw-label count, and the internal summary does not specify this scope clearly. The recomputation reproduces the frozen 42-label set under the stated canonicalization, but it does not prove that the exact historical preprocessing sequence was identical.

The raw-form-first reconstruction yields 38,955 selected training records before cap and 19,352 after applying the cap separately to eligible raw labels. The canonical-first reconstruction instead yields 39,072 training records before cap, 19,125 after cap, and 4,902 development / 4,912 test records. The retained summary reports final totals of 19,125 / 4,411 / 4,452. Its recorded counters (`dev_removed_train_dup=453`, `test_removed_train_dup=460`, `dev_removed_test_dup=38`) arithmetically explain the final development and test totals: 4,902−453−38=4,411 and 4,912−460=4,452. The 227-record post-cap difference is explained by the canonical-first reconstruction: +247 from separately capping the two raw forms of zheng-xu-yu-jie, minus 20 records from a raw qi-yin-liang-xu form that fails its own Dev/Test thresholds. The separate pre-cap difference is -117 (-97 from a qi-zhi-xue-yu raw form failing its own Train/Test thresholds, minus 20 qi-yin-liang-xu). The contemporaneous stdout and complete source-label frequency table remain unavailable, so this arithmetic reconstruction does not prove the exact historical run order.

A copy of `preprocess_tcm_sd_v4_topn.py` was recovered in the private local evidence archive and inspected, but it is not redistributed in this public repository because it contains fixed private runtime paths and expects licensed source data at those paths. The contemporaneous 2026-05-07 stdout and complete source-label frequency table as used by the historical run remain unavailable. Thus the current source-split reconstruction supports the frozen label set and explains the count-scope differences, but does not establish the exact historical implementation order.

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
