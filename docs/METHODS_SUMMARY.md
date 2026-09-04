# Methods summary

## Task
Closed-set 42-class syndrome differentiation from clinical presentation text. All models receive the same task input field and target the same fixed canonical label set.

## Primary evaluation set
The main paper reports the decontaminated held-out set (N=4,218). The original same-source held-out pool contains 4,452 records and is treated as a sensitivity set.

## Metrics
- exact top-1 accuracy (`syn_acc@1`)
- Macro-F1
- Weighted-F1
- Balanced accuracy
- format validity and empty-prediction rate for generated outputs
- paired bootstrap 95% CI for accuracy differences (2,000 resamples; seed 20260516)
- exact two-sided McNemar test
- Holm correction across six pairwise comparisons

## Checkpoint selection
- MacBERT: development Macro-F1 early stopping (historical frozen run)
- ZY-BERT: development Macro-F1
- InternLM3-8B: development Macro-F1 in the final comparative protocol
- Qwen3-8B: historical frozen v18 checkpoint selected by development loss; this mismatch is disclosed and the model was not retroactively retuned on held-out data

## Inference
Generative-model outputs are parsed with one frozen closed-set parser (`code/parse_label.py`). Greedy generation is used for the current LLM evaluation protocol (`do_sample=False`, `temperature=0`, `max_new_tokens=96`).

## Three-seed robustness
ZY-BERT and InternLM3-8B were replicated with seeds 42, 2026, and 7. The held-out set was not used to select checkpoints.
