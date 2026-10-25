# InternLM3 dev420 replay evidence (author-side verification, 2026-10-23)

## Result reported by the private author-side audit

The official final adapters for seeds 42, 7, and 2026 were replayed on the frozen 420-record development set with the v18 parser/evaluator and recorded inference environment. For each seed, the replay matched the archived Stage-2 epoch-2 output byte-for-byte for record IDs and row order (420/420), generated token sequences, raw generated output, parsed syndrome prediction, and raw/parsed output SHA-256 values.

The recomputed syn@1 and Macro-F1 agreed with the archived epoch-2 records and checkpoint_selection.json. The author-side report states that the final adapter, stage2-epoch-2, and best_checkpoint directories were file-hash identical within the retained run trees.

This is stronger than aggregate-metric agreement: it is direct replay evidence linking each retained final adapter to the archived epoch-2 development outputs.

## What this does and does not establish

- **Established by the private audit:** the three final adapters reproduce the archived epoch-2 outputs on dev_420 byte-for-byte under the recorded replay setup.
- **Not independently reproducible from this public repository:** the adapters, per-case raw outputs, parser outputs, and full run logs are not distributed here. This is an author-side verification report, not a claim that an outside reader can repeat the replay from this repository alone.
- **Not a clean-test rerun:** this check covers dev_420 only. It does not constitute a second inference run on the frozen 4,218-record clean held-out set.
- **Checkpoint-selection wording remains qualified:** the archived training configuration specifies Stage-2 development loss, while the later official-selection record identifies development Macro-F1. The replay verifies output correspondence and reports that both criteria select epoch 2 for all three seeds; it does not erase the documentary difference between the historical configuration and the later selection account.
- **Seed-2026 intermediate checkpoint remains unrecoverable:** the replay used the retained official final adapter. It does not recreate or authenticate the lost independent intermediate checkpoint, for which no historical SHA-256 fingerprint was retained.
- **Seed-7 clean-test batch-size remains unresolved:** the development replay must not be used to infer the runtime batch size of the historical 4,218-record test inference or to claim batch-size-1 and batch-size-8 equivalence.

No frozen test prediction, SEAL, primary metric, or checkpoint was changed as part of this replay. Interpret this note alongside docs/EVIDENCE_MAP.md, docs/KNOWN_LIMITATIONS.md, and docs/SEED7_INFERENCE_PROVENANCE.md.
