# Supplementary-material and public-matrix audit (2026-11-09)

This note records a read-only cross-check of the public aggregate files against the supplementary overview in the author-side file `TCM-SD42_Supplement_FinalReview_20261026_v6.docx`. No clinical records, case-level predictions, or model weights were accessed or added.

## Supplementary Figure S1-S4 companion overview

The four public 42 x 42 confusion matrices and `figures_py/source_data/fig8_errors.csv` were cross-checked cell by cell for all ten displayed error directions (40 model-by-direction cells). The diagonal counts and valid-label off-diagonal totals are:

| Model | Matrix entries | Correct (diagonal) | Valid-label off-diagonal errors | Top-10 errors | Top-10 share of off-diagonal errors |
|---|---:|---:|---:|---:|---:|
| ZY-BERT | 4,218 | 3,196 | 1,022 | 324 | 31.7% |
| InternLM3-8B | 4,216 | 2,935 | 1,281 | 409 | 31.9% |
| MacBERT | 4,218 | 2,648 | 1,570 | **640** | **40.8%** |
| Qwen3-8B | 4,216 | 2,476 | 1,740 | **667** | **38.3%** |

The Supplement v6 companion overview displayed 630 for MacBERT and 677 for Qwen3. Those two values do not match the sum of the ten public error-direction cells or the corresponding confusion-matrix cells. The corrected aggregate counts are 640 and 667. The valid-label off-diagonal denominators remain 1,570 and 1,740, respectively; the two empty outputs for each generative model are outside the 42 x 42 matrix and are still counted as errors in the full N=4,218 evaluation metrics.

Re-run the public check from the repository root:

```bash
python code/verify_supplementary_matrix_summary.py
```

The script checks label order, matrix totals, diagonal counts, and every one of the 40 top-10 matrix cells. It does not reproduce the withheld case-level predictions.

## Label crosswalk source

The 42-row label crosswalk in Supplement v6 was compared against the public upstream preprocessing map `TCM/data_preprocess/syndrome.txt` at commit `82031dc6fa7e951f04be0c5214cf140cb008404b` in [GengJiahao121/ZY-BERT-jiahao.geng](https://github.com/GengJiahao121/ZY-BERT-jiahao.geng/blob/82031dc6fa7e951f04be0c5214cf140cb008404b/TCM/data_preprocess/syndrome.txt). Matching the 42 frozen labels plus the terminal `证` suffix yields 38 KEEP and 4 MERGE rows. This is a label-space crosswalk only; it is not the construction rule for the historical TCM-SD42 task.

## Parameter-scale wording

The recorded InternLM3 parameter count (4,981,002,240) and nominal model scale (8B) are distinct reporting bases. Relative to ZY-BERT (325,565,482 parameters), they imply approximately 1:15.3 and 1:24.6, respectively. The existing manuscript wording of approximately one-fifteenth to one-twenty-fifth therefore describes two different denominators; it should not be collapsed into a single parameter count. This audit leaves the recorded value and nominal scale unchanged.

## Scope and limitations

- The confusion matrices contain 4,218 valid-label predictions for the encoder systems and 4,216 for each generative system. The two empty outputs per generative model are not represented as a 43rd matrix column.
- The top-10 percentages above use valid-label off-diagonal errors as their denominator, not all errors including empty outputs.
- This is an aggregate consistency check, not a new inference run, clinical validation, or independent reproduction of training.
