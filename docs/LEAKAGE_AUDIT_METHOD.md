# Leakage audit method

`code/audit_leakage.py` is the recovered historical four-layer audit implementation. It is provided as reference code; the public repository does not include the clinical-record inputs required to execute it.

## Layers

1. **Exact duplicates.** Compare raw `input_text`, normalized input text, and normalized clinical content using SHA-256 hashes across train, development, pilot, and held-out splits.
2. **Near duplicates.** Remove case identifiers, digits, punctuation/whitespace, and fixed template prefixes. Fit one character-level TF-IDF representation (`char_wb`, 2–4 grams, `min_df=2`, sublinear TF, L2 normalization, maximum 200,000 features), then screen the predefined cross-split pairs by cosine similarity. The primary exclusion threshold is `>=0.95`.
3. **Patient-level overlap.** Inspect available identifier fields. The frozen records expose case IDs but no stable patient identifier, so patient-level disjointness cannot be proven.
4. **Label leakage.** Measure direct gold-label appearance, any frozen-label appearance, and diagnostic phrase indicators in input, description, and detection fields. Report examples separately from aggregate counts.

The primary clean held-out set is the union of exact and `>=0.95` near-duplicate exclusions from the 4,452-record source pool, leaving 4,218 records. The historical audit does not use model predictions to define the exclusion set.

## Re-running with authorized data

The historical script expects the archived evidence layout under a local working tree. Do not copy clinical records into this repository. If an authorized private evidence tree is available, place it outside the repository and adjust the script's input paths locally. Keep generated reports outside version control unless they contain only aggregate, non-patient-level results.


## Evidence and reproducibility boundary (2026-10-22)

The private audit reports that the historical pair-level output contained 5,570 cross-partition pairs and that replaying the archived implementation reproduced the pair keys, similarity values to four decimal places, band counts and 234-record exclusion set. The pair-level CSV and clinical partitions are **not included in this public repository**. Therefore, the public code is executable reference code, but a reader cannot independently recreate the historical exclusion set from this repository alone. Re-running the exclusion check requires an authorized private evidence tree; use `code/verify_exclusion_set.py` to compare the derived excluded-ID set, and do not publish clinical text or record-level outputs.
