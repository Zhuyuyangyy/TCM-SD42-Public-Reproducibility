# Qwen3-8B Stage-2 semantics: optimizer scope versus saved checkpoint

This note distinguishes optimizer-group membership, the in-memory model state used for development-loss selection, and the adapter artifact used for held-out inference.

## Recovered early pilot artifact

The uploaded early pilot archive contains the historical TCM-Mini-best adapter:
- Size: 174,655,536 bytes.
- SHA-256: a80b261a36d79b7085f4b577f0eed291b570103e4a32edc13ca5e7a6dcde7daf, matching the retained model_checksums.txt entry.
- Safetensors header: 504 F32 tensors, 43,646,976 parameters, and no tensor keys containing norm.
- Adapter configuration: PEFT 0.19.1, modules_to_save=null, seven LoRA target modules, base path recorded as Qwen3-8B.

The early archive also contains a 4,452-row raw-output artifact (SHA-256 9a02eca7394a599ead9db00c80bb16803c63dedf203bae9d4f8c644523c07042) matching the historical server inventory. These matching hashes establish that the early pilot adapter and raw outputs are preserved. They do not fully prove the original output-to-checkpoint invocation because the inference command and per-record input hashes were not retained. The two Stage-2 epoch adapters needed for a saved-state epoch comparison were not found in the latest server audit.

## Base-model upstream verification (2026-10-23)

A separate server-side audit verified all five Qwen3-8B weight shards and `tokenizer.json` against official Hugging Face LFS entries at commit prefix `b968826d…`; `config.json` was byte-identical to the upstream file.

| Artifact | Reported SHA-256 prefix | Verification |
|---|---|---|
| `model-00001-of-00005.safetensors` | `31d6a825…cbf5f` | Matches upstream HF LFS |
| `model-00002-of-00005.safetensors` | `5991236c…18282` | Matches upstream HF LFS |
| `model-00003-of-00005.safetensors` | `c5185c47…896836` | Matches upstream HF LFS |
| `model-00004-of-00005.safetensors` | `b5ee7de7…caa917a` | Matches upstream HF LFS |
| `model-00005-of-00005.safetensors` | `20c2d636…b542ff` | Matches upstream HF LFS |
| `tokenizer.json` | `aeb13307…2dae4` | Matches upstream HF LFS |
| `config.json` | `f7c4eadf…47c30` | Byte-identical; diff empty |

Full digests are preserved in the server-side audit report (SHA-256 `337abf91ad9493b496069f381df8a5da5a2912a48dcf326b8aee76fef5f5a0de`). The verified base files and the archived checksum-matching adapter make a new local inference check possible. The two epoch-specific adapters needed for saved-state epoch comparison remain missing from the active run tree, and the original inference command/input hashes are still unavailable; do not claim full historical output-to-checkpoint reproduction.

## Historical optimizer and saved-state scope

The archived code path attaches LoRA adapters to seven projection targets across 36 layers. The Stage-2 helper sets requires_grad=True for floating-point parameters in layers 12–31. The 4-bit backbone weights are packed non-floating-point tensors and are skipped by that guard.

| Scope | Parameter count | Evidence interpretation |
|---|---:|---|
| LoRA adapters | 43,646,976 | Count in the recovered adapter artifact |
| Stage-2 optimizer group | 43,815,936 | LoRA plus 168,960 fp32 normalization parameters |
| fp32 Norm parameters in optimizer group | 168,960 | Historical code and log show these parameters were included in Stage 2 |
| Norm parameters serialized in adapter-only artifact | 0 | Safetensors header has no Norm keys |

The 168,960 normalization count is 8,448 parameters per layer across layers 12–31: input and post-attention layer norms (4,096 each), plus Q/K normalization parameters (128 each).

## Reporting boundary

The development loss used to select Stage-2 epoch 1 (0.0198; epoch 2 loss 0.0219) was measured on the in-memory training model with the Norm parameters in the optimizer group. The adapter-only checkpoint omits those Norm parameters, so held-out inference uses the base model's original Norm weights plus saved LoRA. This selection-state/evaluated-artifact mismatch is a real implementation limitation and must be disclosed. Exact per-tensor Norm deltas and optimizer state were not retained, so this note does not claim a per-tensor numerical-delta reconstruction.

The early Pilot-SFT v14 evaluator also used alias-equivalence for top-1 correctness (including the alias 气虚血瘀 → 气滞血瘀), while its F1 metrics used alias-normalized predictions against raw gold labels. Those historical pilot aggregate metrics are not reused in the current four-system comparison, which uses the common exact-label parser. See docs/HISTORICAL_EVIDENCE_RECONCILIATION_20261023.md.

The adapter and raw-output artifacts are not redistributed in this public repository. No held-out test result was used to retune or select a checkpoint in this follow-up review.
