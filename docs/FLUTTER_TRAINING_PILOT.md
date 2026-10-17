# Flutter training pilot: first validated seed cases

This is dataset preparation, not a trained model. The AMD 7B synthetic checks
passed at 128 and 512 tokens, batch size one. Their results are saved in `docs/`.

## What is being built

`scripts/prepare_flutter_pilot.py` copies the bundled Flutter fixture into isolated
temporary directories and tests clean and deliberately broken versions. It exports
JSONL only when every clean version passes and every broken version produces a
Flutter test assertion failure. Compilation or dependency failures do not qualify.
Each record contains the source hash, test path, origin, and a review conversation.
Per-case logs and the Flutter SDK version are saved with the manifest.

| Family | Cases | Split |
| --- | --- | --- |
| Cache | Clean, expired-at-boundary bug, logout-clears-other-accounts bug | Train |
| Native state | Clean counter, missing listener notification | Train |
| Navigation | Clean details flow, missing details content | Evaluation |

Clean/broken relatives stay together in the same split. This reduces direct
source leakage. Two navigation cases do not constitute a representative benchmark.
The labels are manually authored here and supported by narrow tests, not by an
independent expert review. No third-party dataset or private app was uploaded.

## Rebuild locally

```sh
python3 scripts/prepare_flutter_pilot.py --flutter /Users/ishwar/Development/flutter/bin/flutter
```

Outputs under ignored `data/flutter_pilot/`:

- `train.jsonl`: five seed examples.
- `evaluation.jsonl`: two held-out family examples; never include in training.
- `manifest.json` and individual test logs: validation evidence.

The offline dependency step needs the Flutter fixture dependencies already cached.

## Remaining gates before AMD training

1. Expand with independently authored examples for stale async state, disposal,
   account isolation, failed requests, offline fallback, and navigation errors.
2. Keep repository/fixture families and near-duplicates within one split. Add
   held-out state and caching families, not only navigation evaluation.
3. Review provenance and labels; validate each defect and its proposed repair.
   Widget tests alone do not prove browser rendering or end-to-end flow correctness.
4. Tokenize with the exact Qwen tokenizer and chat template. Measure lengths;
   reject oversize examples instead of silently truncating away answers. Mask
   prompt tokens during supervised training. The current records are not yet
   tokenizer-validated and may exceed the tested 512-token setting.
5. Implement baseline evaluation and an AMD pilot runner that saves only adapters,
   records dataset/model hashes, checks finite gradients, and tests save/reload.
6. Run a short bounded pilot and evaluate baseline versus adapter on held-out
   cases. Do not publish a model merely because training loss decreased.

Five training records are suitable for debugging a pipeline, not for teaching
Flutter broadly. Flutter docs remain a separate retrieval corpus; these seeds
are not evidence that all documentation has been converted into training data.

## User action now

A tokenizer preflight command is now ready; see the 17 October update below. Keep the downloaded model only if continuing
soon. If ending the session, first preserve any files you need; deleting the
instance may remove its model cache and environment. The scripts and both test
reports are already saved locally.

## Validation result

All seven cases validated with real Flutter tests: three clean cases passed;
four seeded defects produced assertion failures. Exported five training and
two evaluation records. Source hashes and families do not overlap across splits.


## 17 October: runner and upload bundle

`scripts/train_flutter_pilot.py` now provides:

- Default tokenizer-only checks, pinned model revision, 512-token ceiling,
  explicit rejection rather than truncation, and prompt-label masking.
- Optional `--train`: exactly ten steps, batch one, rank-8 q/v LoRA.
- Held-out baseline/adapter reference losses and generated outputs for manual review.
- Adapter-only save plus tokenizer, followed by unload/reload verification.
- Dataset hashes, token lengths, seed, losses, GPU peak memory, failure report.

Local validation: three unit tests pass for masking, oversize rejection,
template mismatch, and split-family overlap. Existing seven fixture cases remain
validated. Actual Qwen tokenization, AMD training, and adapter reload are pending.
The default check may download small tokenizer files; it does not load weights.
Training requires the pinned weights already cached by the fit test. No automatic
full weight download, package installation, or upload occurs.

Bundle: `data/flutter-pilot-upload.zip` contains runner, both JSONL splits and
validation manifest. Extract it in AMD Jupyter. With the previously working venv:

```sh
. /workspace/forge-lora-env/bin/activate
python train_flutter_pilot.py --data flutter_pilot --output flutter-pilot-check
```

Share the output before training. If any case exceeds 512 tokens, revise the
examples or verify a longer context; do not discard/truncate cases silently.
If the AMD instance was deleted, restore the environment and model cache first.
Output directories must be new, so earlier results cannot be overwritten.

Only after token checks pass, a pipeline-debug run can be invoked with:

```sh
python train_flutter_pilot.py --data flutter_pilot --output flutter-pilot-run-01 --train
```

Preserve the entire output folder before deleting the instance. The runner saves
no optimizer state and does not resume interrupted runs. A failed report means
any partial adapter is unverified. This seven-case run is explicitly a pipeline
debug exercise; broader training is still gated on dataset expansion and stronger
held-out evaluations. Generated responses require human assessment; lower loss
is not a correctness score.

Implementation references:
https://huggingface.co/docs/transformers/chat_templating
https://huggingface.co/docs/peft/quicktour


## Pilot run 01 completed and backed up

The user-provided AMD report confirms ten training steps, adapter save/reload
verification, and peak allocated GPU memory of 14.884 GiB. Local archive
`data/flutter-pilot-run-01.zip` passed ZIP integrity checks and contains the
adapter weights/config, tokenizer, and report. Verification and archive SHA-256
are in `docs/flutter-pilot-backup-verification.json`. No local GPU inference
was performed.

Both baseline and adapter described the missing-content example as correct.
Its prompt omitted the requirement to display the selected item, so this is
not a sound accuracy benchmark. Fix explicit behavior contracts and broaden
held-out cases before further training. Do not treat reduced reference loss
as evidence of better defect detection.


## Second evaluation dataset

The v2 builder adds explicit behavior contracts to every prompt, plus four
held-out cases: clean/broken latest-search state and offline-cache refresh.
There are five training seeds and six evaluation cases. New output is kept in
`data/flutter_pilot_v2`; original data and the run-01 archive remain intact.
The navigation evaluation is now explicitly tied to displaying Fixture item.

The runner supports `--baseline-only`, mutually exclusive with `--train`.
This loads cached base weights and evaluates without creating an optimizer or
adapter. Run token checks first on v2 because its prompt lengths have changed.
These cases remain a tiny authored suite, not a broad benchmark. No further
training is justified merely by lower loss on these references.

V2 validation completed: all eleven cases behaved as expected (five clean
cases passed, six mutations triggered assertions). Split-family checks passed.
Bundle: `data/flutter-pilot-v2-upload.zip`. On AMD, extract then run:

```sh
python train_flutter_pilot.py --data flutter_pilot_v2 --output flutter-pilot-v2-check
```

After token checks pass:

```sh
python train_flutter_pilot.py --data flutter_pilot_v2 --output flutter-pilot-v2-baseline --baseline-only
```

Review `flutter-pilot-v2-baseline/report.json`, including whether output hit
the generation limit. AMD token checks and baseline evaluation remain pending.

## Baseline saved; concise evaluation follow-up

`docs/flutter-pilot-v2-baseline.json` verified: baseline_completed, six outputs,
all six reached the 128-token generation cap. No aggregate accuracy is claimed.
The runner now offers `--concise-review`: a generic verdict/evidence/fix format,
without case-specific hints. It records the added instruction and prompt lengths,
requires room for 128 output tokens within the 512-token envelope, and preserves
the original training data and reference-loss computation. Reference losses use
the original prompt, not the concise generation prompt; do not interpret them as
scores for the revised generation instruction. Local syntax and existing three
data checks pass; actual revised GPU generation remains untested.

Upload the revised runner only, then run:

```sh
python train_flutter_pilot.py --data flutter_pilot_v2 --output flutter-pilot-v2-concise --baseline-only --concise-review
cat flutter-pilot-v2-concise/report.json
```

These six cases are now a development evaluation set because prompt choices
have been informed by their outputs. A fresh unseen test set is needed before
claiming generalization. Concision is requested, not guaranteed; check the
output-limit flag again before grading complete answers.


## Pilot run 02 completed and backed up

The AMD report `docs/flutter-pilot-v2-train.json` confirms ten training steps
on `flutter_pilot_v2`, adapter save/reload verification, and peak allocated GPU memory
of 14.931 GiB on the ROCm environment. Local archive `data/flutter-pilot-v2-run.zip`
passed ZIP integrity checks and contains the adapter weights (`adapter_model.safetensors`),
PEFT config, tokenizer, and report. Verification and archive SHA-256 are in
`docs/flutter-pilot-v2-backup-verification.json`.

Evaluation reference loss decreased across all six held-out cases:
- `navigation_clean`: 4.056 -> 3.687
- `navigation_missing_content`: 3.422 -> 3.315
- `search_clean`: 3.502 -> 3.261
- `search_stale`: 2.890 -> 2.740
- `offline_clean`: 3.385 -> 3.156
- `offline_stale`: 3.796 -> 3.635

Reload verification succeeded (`reload_verified: true`). The pilot pipeline
proves end-to-end execution, finite gradients, LoRA parameter adaptation, and
persistence on AMD hardware.

