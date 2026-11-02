# Local Apple Silicon training

Machine checked: Apple M4, 24 GB unified memory, macOS 26.6.2.
An isolated `.venv-mlx` environment contains MLX LM; the main MCP venv is unchanged.
The package inventory is `docs/local-mlx-packages.txt`. Metal matrix computation
passed outside the restricted agent sandbox. No AMD/ROCm packages are installed.

## Setup

From the repository root:

```sh
.venv-mlx/bin/python scripts/setup_local_mlx.py
```

This downloads the community 4-bit MLX conversion of Qwen2.5-Coder-7B-Instruct
under ignored `data/local_mlx/model`. A revision is recorded in setup.json and
reused on subsequent runs. Tokenization rejects examples longer than 512 tokens.
Five training examples go to train.jsonl; six development evaluation cases go to
test.jsonl. There is no validation-driven tuning on that evaluation set.

## Training

After setup and the local smoke check succeed:

```sh
.venv-mlx/bin/mlx_lm.lora --config configs/local_mlx_pilot.yaml
```

This starts a NEW MLX adapter, using four final layers, q/v rank-8 adapters,
batch one, prompt masking, gradient checkpointing, and ten iterations. It is
not a continuation of the AMD PEFT adapter; that archive remains backed up.
Changing quantization and runtime requires new baseline measurements before
comparing quality. These seeds are only for pipeline verification.

Do not rerun into a valuable adapter directory: select a fresh output with
`--adapter-path data/local_mlx/adapters-run-02`. Training makes the laptop busy;
longer runs and larger sequence lengths have not been validated.

Source references:
- https://github.com/ml-explore/mlx-lm
- https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md
- https://huggingface.co/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit

## Verified locally, 20 October

The model download completed and all eleven examples passed token-length checks.
Base generation passed in 5.6 seconds with peak MLX memory 4.143 GiB.
A one-step q/v rank-8 adapter update over four layers completed (loss 3.980),
saving `data/local_mlx/adapters-smoke/adapters.safetensors` (~1.4 MB).
This validates the setup; it does not establish review quality or long-run stability.

Check saved-adapter generation:

```sh
.venv-mlx/bin/python scripts/check_local_mlx.py --adapter-path data/local_mlx/adapters-smoke
```

The Mac training configuration remains a ten-step optional pilot. No full training
run or AMD adapter conversion was performed. Public model claims still require
broader validated data and an independent evaluation set.

## Ten-step run completed

Run: `data/local_mlx/training-20261020-141312`. All ten iterations completed
with exit 0 and a fresh adapter saved under `adapter/`. Reload and generation
passed (4.145 GiB peak MLX allocation during generation, not training peak).
Logs, dataset hashes, and reload results are saved in the run directory.
No validation split was supplied; six development cases remain separate.
This run used only five training examples and does not establish model quality.

## Development evaluation completed

Both base and ten-step adapter missed all three defects and accepted all three
clean cases. See `LOCAL_MODEL_EVALUATION.md`. No detection improvement established.
