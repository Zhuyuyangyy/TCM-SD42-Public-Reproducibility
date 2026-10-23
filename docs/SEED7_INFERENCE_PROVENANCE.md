# Seed-7 inference provenance (InternLM3-8B)

The 2026-10-23 targeted audit recovered the continuation stdout and verified its SHA-256 as `17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f`. The log supports a batch-size-8 continuation that skipped 739 existing rows and generated 3,479 rows. The provenance of the first 739 rows still depends on separate run/SEAL records. The raw clinical inputs, prediction JSONL files and SEAL are not redistributed in this public repository. The continuation stdout was recovered in the private audit tree.

## Checks reported by the private verification

| Check | Reported result |
|---|---|
| Raw / parsed / clean rows | 4,218 / 4,218 / 4,218 |
| Unique IDs in each file | 4,218 / 4,218 |
| ID sets and row order | No mismatches |
| Gold labels against clean data | No mismatches |
| Parsed predictions versus frozen parser on raw output | 0 / 4,218 mismatches |
| Empty predictions | 2 / 4,218 (0.0474%) |
| Recomputed accuracy | 0.691797 (2,918 correct) |

The report records these SHA-256 values:

- Raw output: \`96866c0462e5af30b796702684b6151a694a61d4f40b331c55007f54a2f661bf\`
- Parsed output: \`c6c66c2c48836dfed5aa5dc41f8789765c5d945fec1d554e959198d8ab92bdfb\`
- Clean evaluation input: \`dc5d66dda2295921916a2edaa52f2537206b8d1784fe10cb8ba3e9c80f2935de\`
- Frozen parser: \`f2adb96b1291bd2787f9c15b88611c6b14972f4540527d7a114274f5a4f607d9\`
- Seed-7 SEAL: \`24f273034952fb8a63714208cb92e552d38e2808e035be77820a6fd74704b11a\`
- Continuation stdout log reported by the audit: \`17eaf1e94b249e6bedd0645840553342c4687c2b890dafebbae31bf9a0dea36f\`

These fingerprints were transcribed from the earlier private verification report; the raw/parsed files and stdout log are not available in this public repository for byte-level checking. A later reconciliation on a separate server could not locate `/tmp/seed7_resume_b8.log` or confirm its SHA-256. Therefore, the reported log hash and the 739/3,479 segment split remain UNVERIFIED in the currently available archive, even though the raw/parsed/clean artifact hashes were reported to match the SEAL.

## Mixed decoding segments

The private verification report says the continuation log recorded batch size 8, 739 already-completed records, 3,479 remaining records, and a continuation start at zero-based index 739 (record identifier withheld). The reported counts sum to 4,218, and the boundary ID reportedly matches the raw output at that position.

The interpretation is limited to the reported segment boundary. Individual rows have no per-record segment marker, so a particular prediction cannot be attributed to a specific run from the public files. The public repository does not contain the original stdout log or the per-case output files. A prior 32-record comparison reportedly found token-identical output across batch sizes, while a separate development check found differences in 15/420 records; the effect on the held-out test predictions is unknown.

## Reproducibility boundary

The reported ID, gold, parser and hash checks support integrity and alignment of the sealed output artifact. They establish the logged batch-8 continuation, but do not independently establish the generation provenance of the first 739 rows, provide per-record segment markers, or verify a complete checkpoint/tokenizer hash chain across segments. They also do not quantify how mixed decoding batch sizes affected test predictions. The public release therefore reports this as private-audit evidence and does not claim end-to-end reproduction.
