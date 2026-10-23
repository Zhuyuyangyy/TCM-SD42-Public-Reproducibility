# Seed-7 inference provenance (InternLM3-8B)

The 2026-10-23 targeted server audit reports that the continuation stdout was recovered and its SHA-256 verified as:

\`17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f\`

The log records a batch-size-8 continuation that skipped 739 existing rows and generated 3,479 rows. The counts sum to 4,218. A separate reconciliation on another server could not locate the referenced path; that path discrepancy remains part of the provenance history, but the latest audit reports the log bytes as FOUND/VERIFIED.

The continuation log supports the batch-size-8 segment. It does **not** establish the origin of the first 739 predictions, provide per-record segment markers, or verify a complete checkpoint/tokenizer hash chain across the two segments. The effect of any batch-size difference on the held-out predictions remains unknown.

The same targeted audit reports these frozen artifact checks:
- Raw / parsed / clean rows: 4,218 / 4,218 / 4,218.
- Unique IDs in each file: 4,218; ID sets, row order and gold-label alignment had no mismatches.
- Frozen parser outputs versus raw-output reparsing: 0 / 4,218 mismatches.
- Empty predictions: 2 / 4,218 (0.0474%).
- Recomputed accuracy: 2,918 / 4,218 = 69.1797%.

The report lists these artifact hashes:
- Raw output: \`96866c0462e5af30b796702684b6151a694a61d4f40b331c55007f54a2f661bf\`
- Parsed output: \`c6c66c2c48836dfed5aa5dc41f8789765c5d945fec1d554e959198d8ab92bdfb\`
- Clean evaluation input: \`dc5d66dda2295921916a2edaa52f2537206b8d1784fe10cb8ba3e9c80f2935de\`
- Frozen parser: \`f2adb96b1291bd2787f9c15b88611c6b14972f4540527d7a114274f5a4f607d9\`
- Continuation stdout: \`17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f\`

These hashes and checks are reported by the private server audit; the raw/parsed case-level files and stdout log are not redistributed in this public repository. The public archive can document the reported checks but cannot independently repeat them without authorized private inputs. This evidence establishes the logged continuation, not the complete provenance of every prediction or end-to-end reproducibility.
