# S2 definition check (2026-10-25)

The authorized-data comparison of the 4,452-record held-out pool and frozen 4,218-row four-model prediction CSV produced:

| Mode | Full pool: N / groups / involved / redundant | Clean subset: N / groups / involved / redundant | Six archived pairwise cells |
|---|---|---|---|
| Digit deletion | 4,419 / 31 / 64 / 33 | 4,195 / 22 / 45 / 23 | All match |
| Digit-to-# sentinel | 4,425 / 26 / 53 / 27 | 4,197 / 20 / 41 / 21 | All match, but count anchors fail |

The prediction CSV agreed with the retained frozen per-run predictions 0/4,218 cases for each model, and the S0 paired cells matched the archived values. The retained-ID sets differ between the two S2 modes. Only digit deletion matches both count anchors and the archived pairwise cells. This supports the published S2 aggregate values but does not establish which historical script copy generated them.

Of the 23 S2 removals, 12 are raw exact-text redundancies and 11 are additional normalization-only removals. Nine groups exist only after deleting digits, and numeric content differs in all nine; the only discordant-label group is among these digit-dependent groups. S2 is an aggressive post hoc normalization stress test / upper bound among the tested definitions, not true deduplication or patient-level independence. Maximum absolute accuracy change: 0.0849 pp (0.085 rounded; conservatively <=0.09 pp).

No clinical text or individual record IDs are included in this note.
