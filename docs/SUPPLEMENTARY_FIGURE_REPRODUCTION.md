# Reproducing Supplementary Figures S0-S4

The public aggregate repository regenerates Supplementary Figure S0 and the four 42 x 42 heatmaps without raw clinical records, case-level predictions, or model checkpoints.

## Requirements

Python 3.9+ and Matplotlib:

    python -m pip install -r requirements-figures.txt

## Generate

From the repository root:

    python figures_py/make_supp_figures.py

By default, PNG and SVG outputs are written to figures_py/supp_figures/. To choose another directory or a lower preview resolution:

    python figures_py/make_supp_figures.py --output-dir /tmp/tcm-sd42-supplement --dpi 150

## Source data and checks

- code/labels_42.txt: frozen 42-label order.
- results/confusion_matrix_*.csv: four archived 42 x 42 matrices.
- figures_py/source_data/fig8_errors.csv: top-10 directions and model-specific cell counts.
- figures_py/source_data/classwise_metrics.csv: gold-label support used to verify omitted outputs.

Before rendering, the script verifies each confusion-matrix Git blob SHA-1, frozen row/column label order, matrix dimensions and totals, diagonal correct counts, row-support accounting, and all 40 model-by-direction cells in the top-10 table. It also checks the published top-10 totals and percentages.

Expected matrix totals are 4,218 for ZY-BERT and MacBERT, and 4,216 for InternLM3 and Qwen3. The two empty outputs per generative model are outside the 42 x 42 matrices but remain errors in the full N=4,218 primary evaluation.

## Figure definitions

- **S0:** panel A shows diagonal correct classifications and off-diagonal misclassifications among valid class-valued predictions. The two empty outputs per generative model are explicitly noted but lie outside the 42 x 42 matrices. Panel B shows the top 10 off-diagonal directions and their share of each model's valid-label errors. Pooled counts are model-record errors, not unique clinical cases.
- **S1-S4:** row-normalized heatmaps in the frozen label order. Each row is normalized by that model's valid class-valued outputs for the corresponding gold class. The two empty outputs are excluded from the generative matrices; row percentages must not be interpreted as full-denominator recall without knowing the gold classes of the omitted outputs.

The script is an aggregate consistency and rendering tool. It does not reproduce per-case predictions, training, clinical validation, or the original historical preprocessing run.
