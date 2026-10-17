# Next step: Radeon GPU training compatibility check

Updated: 15 October 2026.

## Known environment (user-provided probe)

- AMD Radeon Pro W7900D, 48 GiB VRAM.
- Linux / Python 3.14.4.
- PyTorch `2.13.0+rocm10.0.0`; HIP reports `7.15.26333`.
- `/workspace`: 25 GiB free; `/tmp`: 4 GiB free.

These are reported values, not a validated support matrix. Do not replace the provider's PyTorch/ROCm installation based on the differing version labels. Python/package/kernel compatibility must be tested.

## What you do now

1. Have `scripts/amd_training_smoke_test.py` ready on your Mac before launching an instance.
2. Launch the same Radeon Cloud environment you used for the probe.
3. In JupyterLab, click the upload arrow above the left file list and select that script.
4. Open **Terminal** from the launcher. In the directory containing the uploaded file, run:

```bash
python amd_training_smoke_test.py
```

5. Send the JSON output here. If it reports missing packages or an import error, send that output without attempting a blanket upgrade. If it hangs for more than two minutes, interrupt with Ctrl+C and report the last output.
6. After obtaining the output, end the instance as described below. No trained model or useful checkpoint is created by this test.

You can also paste the script into a notebook cell, but the terminal is preferred because failure exit codes are expected and explicit.

## What this test does

- Lists relevant installed package versions.
- Checks BF16 matrix computation and backward gradients on the AMD GPU.
- If Transformers and PEFT are installed, builds a tiny randomly initialized Qwen-shaped model in memory.
- Adds LoRA adapters, performs one synthetic optimizer update, and checks that adapter weights actually change.
- Reports failure or missing dependencies honestly, without falling back to CPU success.

It does not download model weights, install packages, read your app, upload data, or train on Flutter documentation. A passing result only clears an initial compatibility gate. It does not predict full-model memory or training quality.

## Ending your Radeon Cloud instance

Your screenshot showed **AMD Radeon Cloud**, which differs from the generic hackathon notebook instructions previously given.

The Radeon Cloud guide says to destroy the instance when finished: **Profile → Active Instance → Destroy Instance**. Your embedded JupyterLab header labels the control **Delete instance**. Download anything important first. Files are removed unless your template uses Persistent (PVC) storage; a `/workspace` path alone is not proof of persistence.

Do not assume the generic hackathon's 3-hour quota/persistence rules apply to this interface. Check the actual template/credits configuration. Closing the browser tab does not terminate the instance.

Source: https://amd-aim.github.io/radeon-cloud-docs/guides/destroy/

## After the compatibility result

If packages are missing, we will prepare a constrained environment using the provider's existing torch and a compatible Transformers/PEFT combination. We will not automatically install a CUDA wheel or upgrade ROCm.

Then choose a modest coding checkpoint, measure actual memory with a short-context trial, and train only after the corpus and held-out tests are ready. A 7B BF16 checkpoint needs roughly 14 GB of weights before caches and other files; 25 GB disk space is tight. GPU memory and persistent disk are separate constraints.

The local corpus and retrieval baseline are ready, but unresolved templates, training-example validation, licensing/provenance review, and dataset splits still need work. See `FLUTTER_CORPUS_STATUS.md` and `FLUTTER_MODEL_AND_DATA_PLAN.md`.

## Earlier result: GPU passed; Hugging Face packages missing

The user's remote smoke test passed BF16 forward/backward on W7900D (47.98 GiB). Transformers, PEFT, Accelerate, and Safetensors were missing; the LoRA step did not run. GPU kernels are working for this small operation. Full training compatibility is still unknown.

Run the following in the SAME Radeon terminal directory containing the smoke script. This creates a separate environment while allowing it to reuse the provider's ROCm torch. It does not install torch or change the base environment.

```bash
python -m venv --system-site-packages /workspace/forge-lora-env
. /workspace/forge-lora-env/bin/activate
python -c 'import torch; from pathlib import Path; Path("/workspace/forge-torch-constraint.txt").write_text("torch==" + torch.__version__ + "\n"); print("Preserving", torch.__version__)'
python -m pip install --only-binary=:all: --no-cache-dir -c /workspace/forge-torch-constraint.txt transformers peft accelerate safetensors
```

Run commands in order; if any fails, stop and share the error. Binary-only installation avoids spending session time compiling dependencies. The exact torch constraint prevents dependency resolution from selecting a different torch build. No `--upgrade`, `--force-reinstall`, or `--ignore-installed` is needed. Do not relax the constraint to fix a resolver error.

After a successful install:

```bash
python -m pip check
python amd_training_smoke_test.py
```

Send the dependency-check result and smoke-test JSON. Package versions are recorded by the smoke test; once this combination works, record a lockfile for repeatable future sessions. These dependencies have not yet been tested against the provider's Python 3.14.4 image. A missing compatible wheel or import conflict is a compatibility finding, not a reason to replace ROCm torch blindly.

References: https://huggingface.co/docs/peft/install and https://pip.pypa.io/en/stable/user_guide/#constraints-files


## Current result: tiny LoRA test passed

User-reported result: BF16 and tiny Qwen LoRA update passed in 3.87 seconds,
peak allocated VRAM 0.15 GiB. Torch remained 2.13.0+rocm10.0.0;
Transformers 5.19.0, PEFT 0.21.2, Accelerate 1.15.0, Safetensors 0.8.0.
`pip check` passed. Package inventory saved locally in
`docs/forge-lora-working-packages.txt`; this is an inventory, not a portable installer.

The provider Python was itself a venv at `/opt/venv`. The new venv inherited
`/usr`, so a file `amd-provider.pth` in its site-packages was needed, containing
`/opt/venv/lib/python3.14/site-packages`. Recheck these paths on new instances.

## Next: actual 7B capacity test

Upload `scripts/amd_model_fit_test.py` to the existing working AMD instance.
If the instance was deleted, restore and pass the tiny smoke test first.
In the uploaded script directory:

```sh
. /workspace/forge-lora-env/bin/activate
python amd_model_fit_test.py
```

This downloads Qwen/Qwen2.5-Coder-7B-Instruct weights (roughly 15 GB) into
`/workspace/forge-hf-cache`. It checks disk space against repository metadata
plus a 3 GiB margin, records the resolved model revision, loads BF16 entirely
on the GPU, and tries one batch of 128 synthetic tokens with rank-8 q/v LoRA.
No CPU offloading, checkpoint saving, app upload, or Flutter training occurs.
It writes `amd-model-fit-result.json`; download and share this result.
A first download can take several minutes. A passing result only establishes
capacity for these settings, not production context lengths or accuracy.
The script has been syntax-checked locally; actual GPU execution is pending.
Model source: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct

## Saved 7B result and next context check

`docs/amd-model-fit-result.json` verified: 128 tokens, batch 1 passed;
14.522 GiB peak allocated, 14.6 GiB reserved, 0.88 seconds for one step.
This is user-provided remote evidence, not a local GPU run.

The fit script now defaults to the tested revision and subtracts complete cached
weight files from the disk requirement. Previously, a second run could incorrectly
require another full model's worth of free space. Partial files are conservatively
counted as missing; nothing is deleted.

Upload the updated script, replacing the remote copy, then run:

```sh
python amd_model_fit_test.py --tokens 512 --output amd-model-fit-512-result.json
```

Download the result. This tests a larger synthetic batch sequence, not Flutter
knowledge or final training context capacity.
