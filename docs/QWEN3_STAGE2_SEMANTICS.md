# Qwen3-8B Stage-2 semantics: optimizer scope versus saved checkpoint

This note separates three distinct claims: parameters included in an optimizer group, parameters that actually received and applied updates, and parameters included in the evaluated artifact. The historical adapter directory is not included in this public repository; the figures below come from a private artifact audit and are stated with their evidence limits.

## Artifact fingerprints reported by the private audit

| Artifact | SHA-256 |
|---|---|
| Historical training script (\`phase3_train.py\`) | \`69ba59aeacbcbfb557321b12ce22cef5397df8a564de28fa42ddd0287be7af39\` |
| Base configuration (\`config.py\`) | \`91316f207afe585a9aadcfc14a0b3c3eb277808bd5c4532e16339bfe89112b1c\` |
| Run-group configuration | \`90bf35d44005dc439f2e83079e45b5dd483f4af6ee88796a1900e0e2421e997a\` |
| Saved adapter configuration | \`9dabad1934555230314e20d87f8fefb22af324a7e005a5a740952ecd5c591ddb\` |

The retained adapter configuration records PEFT 0.19.1. The historical log supports bitsandbytes 0.49.2 and Transformers 5.x; the exact Transformers minor version and PyTorch version remain unverified. PEFT 0.15.2 belongs to the separate later InternLM3 environment and must not be substituted for the Qwen3 environment.

## Code-path interpretation

The archived code path calls \`prepare_model_for_kbit_training\`, then attaches LoRA adapters to seven projection targets across 36 layers. The Stage-2 helper sets \`requires_grad=True\` only for floating-point parameters in layers 12–31. The 4-bit backbone weights are stored as non-floating-point packed parameters and are skipped by that guard.

A prior server inventory reported an adapter file and SHA-256 `a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf`, and reported five base-model shards. However, the 2026-10-23 targeted audit could not locate the selected adapter or either epoch adapter and found the `TCM-Mini-best` symlink dangling. The two inventory reports conflict; until the adapter bytes are recovered and hashed in the same environment as the current audit, adapter recovery is not treated as verified and saved-state epoch comparison remains blocked. The original inference command and per-record input hashes were not retained.

The private audit calculates the following parameter counts:

| Scope | Parameter count | Interpretation |
|---|---:|---|
| LoRA adapters across 36 layers | 43,646,976 | Stage-1 optimizer scope reported by the audit |
| Stage-2 optimizer parameter group | 43,815,936 | LoRA plus 168,960 floating-point normalization parameters |
| Stage-2 normalization parameters in AdamW group | 168,960 | Historical code and log show the fp32 Norm parameters were made trainable and included in the Stage-2 optimizer; exact per-tensor before/after deltas were not retained |
| Parameters in the evaluated adapter artifact | 43,646,976 (LoRA only) | Adapter-only save; separate normalization updates are not present in this artifact |

The 168,960 normalization count comprises 8,448 parameters per layer across 20 layers (12–31): input and post-attention layer norms (4,096 each), plus Q/K normalization parameters (128 each).

## Reporting boundary

The historical code and training log establish that the Stage-2 optimizer group included the additional floating-point normalization parameters and that Stage-2 training steps ran. The retained archive does not contain before/after Norm tensors or optimizer state needed to report the exact numerical delta of every Norm tensor. Because the saved artifact is adapter-only, those Norm weights were not serialized into the evaluated checkpoint. This creates a material distinction: the development loss used to select the epoch was evaluated on the in-memory Stage-2 model with Norm parameters in the optimizer, while held-out inference uses the base model's original Norm weights plus the saved LoRA adapter. The selection-time state and evaluated artifact are therefore not identical; this must be disclosed rather than described as a fully matched checkpoint-selection/inference path.

The latest targeted audit did not find the adapter or epoch-level checkpoints in its available filesystem; an earlier inventory reported a matching adapter hash, but that claim could not be reverified in the current environment. This note is a transparent account of the private audit, not an independently executable reproduction from the public repository. The historical inference command and per-record input hashes remain missing.
