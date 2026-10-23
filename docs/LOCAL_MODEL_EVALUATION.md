# Local model development evaluation — 20 October 2026

Compared the pinned MLX 4-bit Qwen 7B base against the fresh ten-step local
adapter in `data/local_mlx/training-20261020-141312/adapter`.
Both used the same concise verdict/evidence/fix prompt and deterministic decoding.
Five examples were used for training; six separate development cases were evaluated.

| Result | Base | Local adapter |
| --- | ---: | ---: |
| Defects detected | 0 / 3 | 0 / 3 |
| Defects missed | 3 / 3 | 3 / 3 |
| Clean cases accepted | 3 / 3 | 3 / 3 |
| False alarms on clean cases | 0 / 3 | 0 / 3 |

Both returned NO_DEFECT for every case. Missing navigation content, stale search
responses, and stale offline cache refresh were all missed. The explanations
also incorrectly assert that the broken implementations satisfy the requirements.
This pilot shows no improvement in defect detection on this small suite.

These six cases informed prompt development; results are not an independent
benchmark or a production accuracy estimate. Quantized MLX results should not
be equated with the earlier AMD BF16 outputs. No broad capability claim follows.

## Artifacts

- Reusable evaluator: `scripts/evaluate_local_mlx.py`
- Full responses, timings and verdict counts: `data/local_mlx/training-20261020-141312/evaluation.json`
- Training metadata and logs remain in the same run directory.

## Decision

Do not integrate this adapter as an authoritative MCP reviewer or increase epochs
on the same five records. Build a substantially broader training set with explicit
requirements, faulty expressions, counterexamples, and tested repairs. Add a new
unseen test set before making another model-quality decision. Continue deterministic
Flutter checks independently; those already reproduce the seeded defects.
