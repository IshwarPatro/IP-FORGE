# Dataset v3: targeted expansion

The first local adapter missed all three v2 development defects. This revision
adds tested session-token isolation and asynchronous loading/error state cases.
It doubles the training set from five to ten records; this is still very small.
No new training run is started automatically.

Builder: `scripts/prepare_flutter_v3.py`. Original v1/v2 artifacts remain intact.
Training includes cache, counter notifications, session logout, and load state.
Two key-invalidation cases are separated for development evaluation.

Important limitation: key invalidation is structurally similar to session logout
and account-cache clearing. Although source hashes/family names differ, these
cases are NOT a sufficiently independent generalization benchmark. Reserve a
future independently sourced test set before claiming model accuracy. Do not
move v2 cases into training after inspecting their evaluation outputs.

Each clean case must pass Flutter tests; each seeded bug must produce an actual
assertion failure. Labels are authored, not independently reviewed. Existing
clean implementations provide the repair targets; this is still fixture-level
validation, not browser or production-app validation.

Next: expand beyond these small fixtures, review duplicate/structural overlap,
include reproducible failure evidence and tested patches in training records,
and run baseline evaluation before deciding on a longer training run.

Validation completed: all 12 Flutter cases matched their expected outcomes.
All records pass the actual local Qwen tokenizer and masking checks at 512
maximum tokens (longest 292). Evidence and per-case logs are preserved in
`data/flutter_pilot_v3`; `token-check.json` records lengths. No model training
was run for this revision.
