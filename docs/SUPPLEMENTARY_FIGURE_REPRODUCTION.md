# Reproducing Supplementary Figures S0-S4

The public aggregate repository can regenerate the Supplementary Figure S0 overview and the four 42 x 42 heatmaps without raw clinical records, per-case predictions, or model checkpoints.

## Requirements

Python 3.9+ and the package in requirements-figures.txt:

    python -m pip install -r requirements-figures.txt

## Generate

From the repository root:

    python figures_py/reproduce_supplementary.py

By default, outputs are written to figures_py/generated_supplementary/. To choose another directory or a lower preview resolution:

    python figures_py/reproduce_supplementary.py --output-dir /tmp/tcm-sd42-supplement --dpi 150

The script writes PNG and SVG versions of Figure S0 and Figures S1-S4.

## Source data and checks

- figures_py/source_data/syndrome_label_list.json: frozen 42-label order.
- figures_py/source_data/confusion_matrix_*.csv: four archived 42 x 42 matrices.
- figures_py/source_data/fig8_errors.csv: top-10 directions and model-specific cell counts.
- figures_py/source_data/classwise_metrics.csv: gold-label support used to verify omitted outputs.

Before rendering, the script checks the 42-label order, matrix dimensions, matrix totals, diagonal correct counts, row-support accounting, and all 40 model-by-direction cells in the top-10 table. It also checks the published top-10 totals and percentages.

Expected matrix totals are 4,218 for ZY-BERT and MacBERT, and 4,216 for InternLM3 and Qwen3. The two empty outputs per generative model are outside the 42 x 42 matrices but remain errors in the full N=4,218 primary evaluation.

## Figure definitions

- **S0:** panel A shows correct classifications, valid-label errors, and empty outputs against the fixed 4,218-record denominator. Panel B shows the ten most frequent pooled off-diagonal directions, stacked by model. Pooled counts are model-record errors, not unique clinical cases.
- **S1-S4:** row-normalized heatmaps in the frozen label order. Each row is normalized by that model's valid class-valued outputs for the corresponding gold class. The two empty outputs are excluded from the generative matrices; row percentages must not be interpreted as full-denominator recall without knowing the gold classes of the omitted outputs.

The script is an aggregate consistency and rendering tool. It does not reproduce per-case predictions, training, clinical validation, or the original historical preprocessing run.
