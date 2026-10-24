# Data quality summary (aggregate, no case-level data)

This document reports aggregate duplicate and overlap counts from the 2026-10-22 private data-quality audit. No clinical text, record IDs, or per-case predictions are included. The raw partitions and pair-level audit file are private and are not included in this public repository.

## Definitions

- **Exact/raw duplicate:** byte-identical \`input_text\`, measured by SHA-256.
- **Normalized duplicate:** Unicode NFKC normalization, consecutive digit runs deleted (not replaced with a sentinel), then punctuation, symbols, control characters and whitespace removed, followed by SHA-256. This string-normalization rule matches the retained aggregate counts; it is not a semantic-equivalence or patient-level test.
- **Groups / involved / redundant:** number of duplicate groups / records inside those groups / involved minus groups.
- **Conflict:** a group containing different \`syndrome_canonical\` labels.

## Within-partition duplicates

| Partition | N | Exact groups / involved / redundant | Exact conflicts | Normalized groups / involved / redundant | Normalized conflicts |
|---|---:|---|---:|---|---:|
| Training | 4,186 | 51 / 119 / 68 | 1 group / 3 records | 70 / 190 / 120 | 2 groups / 6 records |
| Development | 420 | 2 / 4 / 2 | 0 | 3 / 6 / 3 | 0 |
| Pilot test | 420 | 0 | 0 | 0 | 0 |
| Pilot clean | 383 | 0 | 0 | 0 | 0 |
| Full held-out pool | 4,452 | 15 / 30 / 15 | 0 | 31 / 64 / 33 | 2 groups / 4 records |
| **Primary clean set** | **4,218** | **12 / 24 / 12** | **0** | **22 / 45 / 23** | **1 group / 2 records** |

The raw-text unique-input counts are 4,118 in training and 4,206 in the clean set; normalized unique-input counts are 4,066 and 4,195, respectively.

## Cross-partition overlap

| Comparison | Exact/raw overlap | Normalized overlap |
|---|---:|---:|
| Clean test vs training | 0 | 0 |
| Clean test vs development | 0 | 0 |
| Clean test vs pilot (420 and 383 records) | 0 | 0 |
| Development vs training | 18 records / 17 unique text hashes | 27 |
| Pilot test vs training | 14 | 20 |

The clean test is **not internally deduplicated**. Its 12 exact duplicate groups remain in the primary record-level metrics. A sensitivity analysis retains the record with the smallest numeric ID suffix within each exact-text group (N=4,206) and within each normalized-text group (N=4,195). The normalized subset is a string-normalization stress test, not adjudicated semantic or patient-level deduplication. Aggregate results are in \`results/dedup_sensitivity_seed42.csv\`.

## Held-out exclusion evidence and limits

The frozen exclusion set contains 234 held-out record IDs from the 4,452-record source pool. At record-level accounting, six excluded IDs have exact raw-text matches; these correspond to five distinct raw-text hashes because one text appears in two records. The remaining 228 excluded IDs are the near-duplicate-only remainder in the historical record-level accounting. Earlier wording (“5 raw exact + 229 near”) mixed unique-text and record-level units and should not be interpreted as a consistent record-level decomposition. The 234-record total is independently confirmed by the ID difference between the 4,452-record source pool and the 4,218-record clean set.

The original pair-level `near_duplicate_pairs.csv` and raw clinical partitions are not redistributed. An alternative reimplementation that did not exactly reuse the archived preprocessing order overlapped with 226/234 archived IDs, with eight archived IDs not reproduced and three additional candidates. All 11 differences were close to the inherited 0.95 cosine threshold. Because the alternative implementation changed text-normalization details/order, these differences are a sensitivity warning rather than a definitive failure of the archived implementation. The public repository alone cannot independently reconstruct every historical exclusion decision; the exact pair-level evidence remains unavailable.

The 0.95 cutoff is an inherited operational decision, not a threshold validated against expert-adjudicated duplicate pairs. Text-level equality is not semantic duplication, and no stable patient identifier is available to prove patient-level independence. Record-level bootstrap and McNemar analyses do not account for all dependence that may arise from repeated text or multiple records from the same patient.

## 5-gram Jaccard diagnostic for source-split count reconciliation (not the historical production filter)

The completed 2026-10-23 log reports these Train-to-Dev/Test candidate-hit counts:

| Threshold | Dev hits | Test hits |
|---|---:|---:|
| >=0.80 | 615 | 625 |
| >=0.85 | 516 | 550 |
| >=0.90 | 370 | 387 |

Earlier interim values 502/518 and 424/447 came from an incomplete log tail and are superseded. These candidate-hit counts are not the historical production deletion counts. Corrected diagnostic report SHA-256: `7014c4021f1a38b1eb72db23f0e56e50c44d0a0eb44f836c7b0c688c42646536`. The historical summary counters remain 453 Dev/Train, 460 Test/Train, and 38 additional Dev/Test removals; the original pair-level file and exact historical matching key remain unavailable.
