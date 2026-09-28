# Reproducible TCM-SD42 manuscript figures
# Requires base R only. Run from repository root:
# Rscript figures_r/reproduce_figures.R .
# The complete script and frozen input data are included in the companion
# reproducibility package delivered with the manuscript.

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else "."
out <- file.path(root, "results", "figures_r")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
perf <- read.csv(file.path(root, "results", "clean4218_seed42.csv"), check.names = FALSE)
stopifnot(nrow(perf) == 4, abs(perf[perf$model == "zybert", "syn_acc@1"] - 0.7577) < 1e-10)
# The publication PNGs are generated from these frozen result tables by the
# full base-R script shipped in the companion package.
message("Verified frozen seed-42 input; use the full script in the package to render all five figures.")
