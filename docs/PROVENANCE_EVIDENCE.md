# Recovered provenance evidence

This note records the provenance artifacts recovered from the private experiment archives on 2026-09-27. The public repository contains only code, aggregate results, hashes, and run-level metadata. It does not contain clinical records, case-level predictions, checkpoints, or private server paths.

## Recovered source and statistics

| Artifact | Status | Public treatment |
|---|---|---|
| Historical four-layer leakage audit implementation | Found; SHA256 `aba08ba0c18a922227412086f05dba7f3706512dd564fff1e59cb06044bdef5b` | Published as `code/audit_leakage.py` |
| Historical 42-class preprocessing script `preprocess_tcm_sd_v4_topn.py` | Recovered in a private local evidence archive; SHA256 `0c7e35388b0b3d74a09cd55e51c0fd3331756155ca482a077bfaf97fd7410f11` | Not redistributed because the copy contains fixed private runtime paths and expects licensed source data at those paths; its code supports suffix canonicalization before support counting/capping |
| v23 class-sensitive statistics addendum | Found; ZIP SHA256 `50709127ea6b053b9b7ef152e007d37cc0cadcda6e214bcf47b99e923596cc3e` | Reproducible scripts and small aggregate result tables are published |
| Structured run seals | Found for ZY-BERT and InternLM3 seeds 42, 2026, and 7 | Sanitized run-level summary in `provenance/seal_summary.json` |
| MacBERT/Qwen3 seed-42 seals | No standalone `SEAL.json` found | Frozen prediction hashes and protocol references are retained; this gap is explicit |

The recovered preprocess_tcm_sd_v4_topn.py copy is an actual archived source file, not a reconstructed rewrite; its SHA-256 is 0c7e35388b0b3d74a09cd55e51c0fd3331756155ca482a077bfaf97fd7410f11. It is not included in the public repository because it contains fixed private runtime paths and expects licensed source data at those paths. The contemporaneous 2026-05-07 execution stdout, complete historical source-label frequency table, and intermediate downstream training-cleaning output remain unavailable. The retained dataset_stats.json reports 278 labels and 42 eligible/selected labels under train>=100, dev>=10, test>=10, top-50. A later source-split reconstruction found 278 raw strings in Train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization; the thresholds yield 43 eligible raw strings that canonicalize to the frozen 42-label vocabulary. The summary field raw_label_count=278 remains ambiguous about counting stage. The raw-label cap-before-canonicalization reconstruction yields 19,352/4,902/4,912; retained duplicate counters reconcile Dev/Test to 4,411 and 4,452, and the 227-record post-cap difference is explained by canonical-first counting rather than an unexplained downstream loss. The exact historical execution order remains unproven because the contemporaneous stdout and complete source-label frequency table are unavailable. The task is disclosed as test-informed because source test-label support contributed to the reported rule.

## Run-level seal coverage

`provenance/seal_summary.json` records, without private paths:

- model and seed;
- seal timestamp where available;
- selected epoch and development macro-F1 where available;
- clean-test data hash and sample count;
- prediction-file hashes;
- checkpoint-file hashes, without checkpoint contents.

The primary clean held-out scope is 4,218 records. The 4,452-record files are retained only as the historical full-pool prediction artifacts from which the clean scope was selected; they are not interchangeable in the manuscript's primary analysis.

## Author-side InternLM3 dev420 replay (2026-10-23)

The private author-side replay report states that the official final adapters for seeds 42, 7 and 2026 reproduced the archived epoch-2 outputs on the frozen 420-record development set byte-for-byte, including IDs/order, generated tokens, raw outputs, parser predictions and raw/parsed SHA-256. This directly links the retained final adapters to the archived dev outputs for that set. It does not cover the 4,218-record clean test inference, does not restore the lost independent seed-2026 intermediate checkpoint, and cannot be repeated by an outside reader from this public repository because the weights and per-case outputs are not distributed. The archived loss-setting versus later Macro-F1 selection-account discrepancy remains documented.

## Statistical addendum

## Integrity checks

The recovered v23 run reported these gates:

- four-model metric alignment: maximum absolute difference `0.00e+00` against the frozen table;
- six accuracy confidence-interval checks: `6/6` passed;
- fast metric implementation against scikit-learn: `50/50` resamples passed at `1e-12` tolerance;
- ordinary versus class-stratified direction agreement: `12/12` comparisons.

These checks support the published aggregate results. They do not establish patient-level independence because the source records do not provide a stable patient identifier.
