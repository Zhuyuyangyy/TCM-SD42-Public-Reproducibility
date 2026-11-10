# Figure reproduction (Python)

Rebuilds the eight main figures of the TCM-SD42 manuscript as vector SVG plus
600-dpi PNG, directly from the aggregate inputs in `source_data/`.

Run:

```bash
python reproduce_figures.py
```

Outputs in this directory: `Figure1.svg` … `Figure8.svg`, matching `.html`
render pages, and `Figure1.png` … `Figure8.png`. The script finishes by running
`verify_provenance.py`, which recomputes Accuracy, Macro-F1, Weighted-F1 and
Balanced Accuracy from the four archived 42×42 confusion matrices and checks
that the numbers printed in the SVGs match.

## Requirements

- Python 3.9+ (standard library only for SVG generation)
- Pillow, only for the PNG step
- Microsoft Edge or Google Chrome, only for the PNG step (headless screenshot);
  set `EDGE`/`PATH` or install the browser in a default location

If no browser is found, the script still produces all SVG/HTML files and
prints a notice.

## Inputs (`source_data/`)

| File | Role |
| --- | --- |
| `model_summary.csv` | public aggregate model summary (four rows): valid-label extraction rate (historical column name `format_validity`) and recorded parameter counts; no per-record predictions |
| `confusion_matrix_{zybert,internlm3,macbert,qwen3}.csv` | archived 42×42 matrices; source of all point metrics |
| `fig5_metrics.csv`, `fig5_pairs.csv` | seed-42 metrics and paired differences (six comparisons) |
| `fig6_seeds.csv` | three-seed summaries for ZY-BERT and InternLM3 |
| `fig6_dedup.csv`, `fig6_bootstrap.csv` | deduplication sensitivity and ordinary vs class-stratified bootstrap |
| `fig8_errors.csv` | top-10 off-diagonal error directions |
| `classwise_metrics.csv` | 42-class support and per-class Recall/F1 |
| `labels_42.json`, `label_meta.json` | frozen label order and display labels |

These files are aggregate outputs; they contain no raw clinical text and no
patient identifiers. Rows marked `digitized` inside `fig5_pairs.csv`,
`fig6_bootstrap.csv` and the S1 column of `fig6_dedup.csv` are read from the
archived figure sources rather than recomputed from per-record predictions; see
`../results/` and the repository README for the underlying artifacts.

Terminology: `format_validity` in `model_summary.csv` is retained as the
historical column name. It records the fraction of outputs from which the frozen
parser extracted a valid label (parser success rate), not strict compliance with
the two-field output format; the manuscript reports the same quantity as the
valid-label extraction rate.

## Layout rules used by the scripts

- Model colours are fixed: ZY-BERT `#0072B2`, InternLM3-8B `#D55E00`,
  MacBERT `#009E73`, Qwen3-8B `#CC79A7`.
- Main metric axes run from 0 to 100; no truncated bar axes.
- Panels carry a black letter only; panel titles live in the caption.
- Figure 4 uses the two-route plate and a shared evaluation rail; it is built by
  `fig4_v3.py`, and `build_all.py` deliberately does not rebuild it.

## Supplementary figures (S0-S4)

`python make_supp_figures.py` rebuilds the five supplementary figures from the
archived matrices in `../results/` and the top-10 table in `source_data/`:

- `supp_figures/FigureS0.png` — diagonal vs off-diagonal counts and the share of
  errors concentrated in the top-10 confusion directions;
- `supp_figures/FigureS1.png` … `FigureS4.png` — row-normalized 42×42 heatmaps.

The plotted values are identical to the typeset supplement; the styling is a
clean re-implementation and is not claimed to be pixel-identical.


The S0-S4 generator validates the four confusion-matrix Git blob SHA-1 values, frozen row/column label order, matrix totals, diagonal counts, class-support accounting, and all 40 top-10 cells before rendering. It writes PNG and SVG outputs to the selected output directory; the checked-in PNGs are the current public rendering snapshot.
