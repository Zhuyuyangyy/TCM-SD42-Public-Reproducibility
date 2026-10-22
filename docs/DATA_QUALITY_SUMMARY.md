# Data quality summary (aggregate, no case-level data)

This document reports aggregate duplicate and overlap counts from the 2026-10-22 private data-quality audit. No clinical text, record IDs, or per-case predictions are included. The raw partitions and pair-level audit file are private and are not included in this public repository.

## Definitions

- **Exact/raw duplicate:** byte-identical \`input_text\`, measured by SHA-256.
- **Normalized duplicate:** lowercase text after removal of fixed template labels, dataset/case identifiers, digits, punctuation and whitespace, then SHA-256. This is the specific normalization implemented by the archived audit script; it is not a general semantic-equivalence test.
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

The clean test is **not internally deduplicated**. Its 12 exact duplicate groups remain in the primary record-level metrics. A sensitivity analysis retains the first record within each exact-text group (N=4,206) and within each normalized-text group (N=4,195). The normalized subset is a string-normalization stress test, not adjudicated semantic or patient-level deduplication. Aggregate results are in \`results/dedup_sensitivity_seed42.csv\`.

## Held-out exclusion evidence and limits

The private audit reports 234 unique held-out exclusions from the 4,452-record pool: 5 raw exact matches and 229 additional near-duplicate matches at the inherited cosine threshold >=0.95. The private pair-level audit file and raw clinical partitions are not redistributed. The exclusion set can be independently re-derived **only when an authorized local evidence tree containing those private inputs is supplied** to \`code/verify_exclusion_set.py\`; this public repository alone cannot rerun the record-level exclusion audit.

The 0.95 cutoff is an inherited operational decision, not a threshold validated against expert-adjudicated duplicate pairs. Text-level equality is not semantic duplication, and no stable patient identifier is available to prove patient-level independence. Record-level bootstrap and McNemar analyses do not account for all dependence that may arise from repeated text or multiple records from the same patient.
