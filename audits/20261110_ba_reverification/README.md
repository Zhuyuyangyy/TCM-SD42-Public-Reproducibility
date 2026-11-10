# TCM-SD42 ordinary paired-bootstrap Balanced Accuracy re-verification

Date: 2026-11-10  
Status: completed on authorized local data; PR #4 remains open and unmerged.

## Result

The corrected gold-present Balanced Accuracy implementation was checked against the authorized aligned seed-42 predictions (N=4,218). The ordinary paired bootstrap used 2,000 resamples, seed 20260516, with zero-based percentile indices [50] and [1949].

- G1: 16/16 model-metric comparisons passed.
- G2: 6/6 historical Accuracy-CI anchors reproduced.
- G3: 8,000/8,000 corrected-fast-path vs scikit-learn comparisons passed; maximum absolute difference 0.
- G4: 6/6 historical union-path BA intervals reproduced.
- Only one CI endpoint changed: ZY-BERT vs InternLM3 upper bound 0.0786 → 0.0787 (7.86 → 7.87 pp).
- No zero-exclusion verdict changed: five intervals exclude zero; InternLM3 vs MacBERT remains the single interval containing zero.
- Full-test-set BA point estimates, Macro-F1 intervals, and class-stratified BA intervals are unchanged.

## Corrected ordinary paired-bootstrap results

| Comparison | Difference (pp) | Corrected 95% CI (pp) | Excludes zero |
|---|---:|---:|---|
| ZY-BERT vs InternLM3 | +5.77 | [3.61, 7.87] | Yes |
| ZY-BERT vs MacBERT | +6.69 | [4.52, 8.94] | Yes |
| ZY-BERT vs Qwen3 | +10.59 | [8.47, 12.76] | Yes |
| InternLM3 vs MacBERT | +0.92 | [-1.46, 3.31] | No |
| InternLM3 vs Qwen3 | +4.82 | [2.89, 6.78] | Yes |
| MacBERT vs Qwen3 | +3.90 | [1.45, 6.36] | Yes |

## Privacy and reproducibility boundary

The aligned six-field case-level prediction file is intentionally not included in this public repository. Its SHA-256 fingerprint is recorded in the full audit report, but the input itself must remain in an authorized controlled environment. This directory publishes aggregate results only.

The corrected implementation is in `code/pairwise_class_sensitive_bootstrap.py` on this PR branch. The full AutoDL execution package, detailed report, and sanitized logs are retained by the authors. To independently rerun, use an authorized local aligned JSONL with the PR #4 implementation; do not upload case-level predictions or clinical text.

The historical aggregate CSV on `main` is not overwritten. PR #4 remains unmerged, so these corrected results are review-branch evidence, not yet the published main-branch result.
