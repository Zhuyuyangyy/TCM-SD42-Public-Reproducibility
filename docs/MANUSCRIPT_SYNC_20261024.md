# Manuscript-facing public evidence synchronization (2026-10-24)

This note synchronizes the public reproducibility documentation with the author-side review of the 2026-10-22 manuscript and Supplement, incorporating later audit evidence through 2026-10-24. The manuscript and Supplement themselves are not distributed in this repository. No raw clinical records, per-case predictions, model weights, private run logs, or private pair-level duplicate records are added.

## Primary results

The frozen seed-42 comparison remains unchanged (N = 4,218). Public aggregate files continue to report:

| Model | Accuracy | Macro-F1 | Weighted-F1 | Balanced accuracy |
|---|---:|---:|---:|---:|
| ZY-BERT | 75.77% | 66.51% | 78.00% | 79.32% |
| InternLM3-8B | 69.58% | 60.74% | 72.20% | 73.55% |
| MacBERT | 62.78% | 56.81% | 63.94% | 72.63% |
| Qwen3-8B | 58.70% | 54.50% | 61.82% | 68.73% |

The InternLM3-versus-MacBERT balanced-accuracy point difference is +0.93 percentage points (unrounded difference approximately +0.9258); its archived 95% interval includes zero. No frozen prediction or primary metric was replaced.

## Historical 42-class construction

A copy of preprocess_tcm_sd_v4_topn.py was recovered in the private local evidence archive and inspected. Its code canonicalizes the terminal 证 suffix before class-support counting and training-cap application. Its SHA-256 in the private evidence package is 0c7e35388b0b3d74a09cd55e51c0fd3331756155ca482a077bfaf97fd7410f11.

The script is not redistributed here: the recovered copy contains fixed private runtime paths and expects licensed source data at those paths. Its presence strengthens evidence for the preprocessing logic, but does not prove that the exact historical end-to-end run produced every frozen downstream artifact. The contemporaneous 2026-05-07 stdout, complete historical source-label frequency table, and intermediate training-cleaning output remain unavailable. The source-split reconstruction finds 278 raw strings in Train, 282 in the three-split raw union, and 278 after suffix canonicalization; 43 eligible raw strings canonicalize to the frozen 42-label vocabulary. The 227-record difference between cap-before-canonicalization Train (19,352) and the retained frozen Train count (19,125) remains unresolved.

## Held-out exclusions and count units

The frozen clean set contains 4,218 record IDs; the source held-out pool contains 4,452 record IDs, so the ID difference is 234 records. At record-level accounting, six excluded record IDs have exact raw-text matches, representing five distinct raw-text hashes because one text appears in two records; the remaining 228 excluded IDs are the near-duplicate-only remainder in the historical record-level accounting. Earlier public wording (“5 raw exact + 229 near”) mixed unique-text and record-level units and should not be read as a consistent record-level decomposition.

The original near_duplicate_pairs.csv is not available in the public repository. An alternative reimplementation that did not exactly reuse the archived preprocessing order overlapped with 226/234 archived IDs, with eight archived IDs not reproduced and three additional candidates; all differences were near the 0.95 threshold. Because that implementation differed in text normalization/order, these results are a sensitivity warning, not a definitive replay of the exact archived implementation. The threshold was not validated against expert-adjudicated duplicate pairs. The public repository alone cannot independently reconstruct the complete historical exclusion decision for each record.

The normalized within-partition duplicate counts in docs/DATA_QUALITY_SUMMARY.md match an implementation that deletes consecutive digit runs, then removes punctuation, symbols, control characters and whitespace after Unicode NFKC normalization. The prior wording that digit runs were replaced by a # sentinel was inaccurate and has been corrected.

## InternLM3 development replay

The private author-side replay report for 2026-10-23 states that the official final adapters for seeds 42, 7, and 2026 reproduce their archived epoch-2 outputs on the 420-record development set byte-for-byte: IDs/order, generated tokens, raw outputs, parser predictions, and raw/parsed file hashes all match. This is direct replay evidence for dev_420, not a second inference run on the 4,218-record clean test set. See docs/DEV420_REPLAY_EVIDENCE_20261023.md.

The archived training configuration still specifies Stage-2 development loss, while the later official-selection account identifies development Macro-F1. Both reported criteria select epoch 2 in all three seeds, and the development replay matches the archived epoch-2 outputs. The public repository does not contain the private selection logs, adapters or per-case outputs needed for an outside reader to independently repeat that verification.

## Seed-7 and historical-checkpoint boundaries

The hash-verified continuation stdout supports a batch-size-8 continuation that skipped 739 existing rows and generated 3,479 rows. The completed full-run stdout and original argv were not preserved; therefore the SEAL field alone is not treated as independent proof of runtime batch size for all 4,218 records. Batch-size-1 and batch-size-8 outputs are not assumed equivalent. The lost independent seed-2026 intermediate checkpoint had no retained SHA-256 fingerprint and is not recreated by the final-adapter replay. MacBERT's trained checkpoint/history and the exact Qwen3 prediction-to-adapter inference chain also remain incomplete.

## Public release boundary

This update changes documentation only. It does not change the frozen 4,218-record prediction files, confusion matrices, primary metrics, SEAL artifacts, or historical checkpoint files. The public repository continues to exclude raw clinical records, case-level predictions, trained weights, private operational logs, and the pair-level near-duplicate file. Author/mentor confirmation of manuscript declarations and final manuscript/Supplement consistency remains outside the scope of this repository update.
