# Known limitations

1. **Derived task, not the official 148-class benchmark.** TCM-SD42 uses a historical 42-class task taxonomy based on original syndrome annotations; it is not identical to the official normalized 148-class TCM-SD label space.
2. **Historical construction script unavailable.** The original `prepare_42class.py` is referenced by archived code but is not present in the surviving public package; the exact original class-selection procedure is therefore incompletely documented.
3. **Patient-level independence cannot be established.** The frozen derived files do not contain a reliable patient identifier suitable for proving patient-disjoint splits. The study establishes text-level decontamination, not guaranteed patient-level independence.
4. **Class imbalance.** The primary 4,218-case test set is strongly imbalanced; Macro-F1 and Balanced Accuracy should be interpreted alongside overall Accuracy.
5. **Checkpoint-selection mismatch for historical Qwen3.** The frozen Qwen3 checkpoint was selected by development loss, whereas later comparative models use development Macro-F1. This is disclosed rather than retroactively changed.
6. **No reliable public per-class F1 table from the v20 aggregate file.** An internal per-class CSV was found to be column-inconsistent and is intentionally excluded from this public release. Confusion matrices and aggregate metrics are retained.
7. **No claim of clinical deployment.** The task is a benchmark classification study and does not establish diagnostic safety or clinical effectiveness.
