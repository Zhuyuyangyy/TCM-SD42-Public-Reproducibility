# Recovered provenance evidence

This note records the provenance artifacts recovered from the private experiment archives on 2026-09-27. The public repository contains only code, aggregate results, hashes, and run-level metadata. It does not contain clinical records, case-level predictions, checkpoints, or private server paths.

## Recovered source and statistics

| Artifact | Status | Public treatment |
|---|---|---|
| Historical four-layer leakage audit implementation | Found; SHA256 `aba08ba0c18a922227412086f05dba7f3706512dd564fff1e59cb06044bdef5b` | Published as `code/audit_leakage.py` |
| Historical 42-class preprocessing script `preprocess_tcm_sd_v4_topn.py` | Not found after the archived search | The support rule is documented; the missing source is disclosed as a limitation |
| v23 class-sensitive statistics addendum | Found; ZIP SHA256 `50709127ea6b053b9b7ef152e007d37cc0cadcda6e214bcf47b99e923596cc3e` | Reproducible scripts and small aggregate result tables are published |
| Structured run seals | Found for ZY-BERT and InternLM3 seeds 42, 2026, and 7 | Sanitized run-level summary in `provenance/seal_summary.json` |
| MacBERT/Qwen3 seed-42 seals | No standalone `SEAL.json` found | Frozen prediction hashes and protocol references are retained; this gap is explicit |

The original preprocessing script is not reconstructed or represented as original source. A retained internal `dataset_stats.json` (SHA-256 `5b96b35e77a5a43021658eabe7ede3b7bc149f03ec541373ec4da8f51deda804`) reports 278 raw labels and 42 eligible/selected labels under the train>=100, dev>=10, test>=10, top-50 criterion. The original historical source-label frequency table and contemporaneous execution log were not recovered. A later independent reconstruction on current official source splits found 278 raw strings in train, 282 in the raw three-split union, and 278 after trailing-证 canonicalization. The thresholds yield 43 eligible raw strings, which canonicalize to the frozen 42-label vocabulary. The summary's raw_label_count=278 is ambiguous about counting stage. The raw-label cap-before-canonicalization reconstruction yields 19,352/4,902/4,912. Retained duplicate counts reconcile Dev and Test exactly to 4,411 and 4,452 (453 Dev/Train, 460 Test/Train, and 38 additional Dev/Test removals). The capped Train difference of 227 remains unresolved pending an explicit per-class comparison of cap-before-canonicalization versus canonicalization-before-cap; the original historical post-processing/deduplication code is missing. The task is disclosed as test-informed because source test-label support contributed to the reported rule.

## Run-level seal coverage

`provenance/seal_summary.json` records, without private paths:

- model and seed;
- seal timestamp where available;
- selected epoch and development macro-F1 where available;
- clean-test data hash and sample count;
- prediction-file hashes;
- checkpoint-file hashes, without checkpoint contents.

The primary clean held-out scope is 4,218 records. The 4,452-record files are retained only as the historical full-pool prediction artifacts from which the clean scope was selected; they are not interchangeable in the manuscript's primary analysis.

## Statistical addendum

The v23 addendum used one aligned, non-patient-level four-model input and produced ordinary and class-stratified paired bootstrap results. The public release includes:

- `code/pairwise_class_sensitive_bootstrap.py`;
- `code/verify_four_model_alignment.py`;
- `code/build_four_model_clean4218.py`;
- ordinary Macro-F1 and balanced-accuracy tables;
- the class-stratified sensitivity table.

The aligned case-level input is intentionally omitted from this public repository. To run the scripts, provide an authorized local evidence tree and pass explicit paths; the scripts do not assume the historical `/root` layout.

## Integrity checks

The recovered v23 run reported these gates:

- four-model metric alignment: maximum absolute difference `0.00e+00` against the frozen table;
- six accuracy confidence-interval checks: `6/6` passed;
- fast metric implementation against scikit-learn: `50/50` resamples passed at `1e-12` tolerance;
- ordinary versus class-stratified direction agreement: `12/12` comparisons.

These checks support the published aggregate results. They do not establish patient-level independence because the source records do not provide a stable patient identifier.
