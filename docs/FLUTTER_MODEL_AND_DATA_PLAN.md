# Flutter documentation corpus and model experiment

Status: preparation only; no model has been trained. This adds an optional model experiment to the Flutter MCP roadmap; deterministic checks and host-agent operation remain useful independently.

## Pilot

Local application: `/Users/ishwar/Desktop/Apps/spacecraftarcade`.
User says it has no GitLab integration. Its manifest declares Flutter and Cupertino icons, without an explicit third-party state-management or caching package. No application files have been changed or uploaded.

## Source acquisition

Use the official `flutter/website` Git source rather than repeatedly scraping rendered pages. Run `python scripts/prepare_flutter_corpus.py` after checkout. Raw source and generated records live under ignored `data/flutter_docs/`; commit only the tooling and manifest summaries intended for sharing.

This source snapshot is not “all Flutter knowledge.” Inventory and then resolve site includes, frontmatter, code excerpts, redirects, and generated content. Add API documentation and Dart language documentation as separate versioned sources. External links, videos, and third-party package documentation are outside the initial download. The source records include infrastructure Markdown too and require filtering before use.

Retain per-file provenance, hashes, source commits, license notices, and attribution. Flutter's website identifies documentation as CC BY 4.0 and code samples as BSD-3-Clause, except where noted. Do not flatten third-party exceptions into a single blanket license. Use version metadata to avoid recommending current APIs to an older SDK project.

## Recommended experiment

- Baseline fine-tuning candidate: `Qwen/Qwen2.5-Coder-7B-Instruct`. A manageable dense coding model, not a claim that it is the newest or best Flutter model. Pin the exact model revision before experiments.
- Optional stronger comparison: `Qwen/Qwen3-Coder-30B-A3B-Instruct`; evaluate before choosing it for training. Its active parameter count is not its total weight-memory requirement.
- Retrieval candidate: `Qwen/Qwen3-Embedding-0.6B`; assess retrieval on real Flutter queries before selecting permanently.
- Start with BF16 LoRA on the 7B candidate. Avoid depending on unverified quantization kernels for the first AMD run.

First measure the unchanged model, then model plus retrieved docs, then the fine-tuned adapter plus retrieval. Training is justified only by measured improvements in finding correctness, valid patches, executable tests, and evidence-grounded explanations. A code model does not replace rendering screenshots or executed flow tests.

## AMD provisioning request

Preferred first rental: one AMD Instinct MI300X with 192 GB HBM3, Linux, a compatible driver/ROCm/PyTorch container, SSH access, and container permissions. Suggested host budget: 128 GB RAM and 200 GB free SSD. Host RAM/storage are planning allowances, not strict measured minima.

A smaller supported AMD GPU may suffice for 7B LoRA, but confirm the exact GPU, VRAM, driver, and kernel support before committing. MI300X is a comfortable supported target, not a minimum purchase requirement. Do not rent an eight-GPU node for this initial experiment.

Start with a short GPU compatibility and forward/backward smoke test. Initial trial settings: 2K–4K token sequences, microbatch 1, gradient accumulation, checkpointing, low-rank adapters. Measure peak memory and examples/second, then estimate full cost and duration from actual corpus token counts. Do not reserve a long run before this measurement. Full-parameter pretraining is outside scope.

## Dataset preparation and evaluation

1. Inventory official docs, preserve notices, normalize rendered text and code examples, and label supported SDK versions.
2. Build retrieval first so documentation can be cited and refreshed without retraining.
3. Build supervised examples: question/repository context → evidence-backed review → patch → test outcome. Raw pages are not ready-made instruction pairs.
4. Seed controlled lifecycle, cache, navigation, and conflict defects in executable fixtures. Include healthy examples and correct abstentions to measure false alarms.
5. Use official `flutter/samples` as a candidate source of runnable examples, reviewing its composite/per-file licenses and compatibility first. It is not an already labeled bug-fix dataset.
6. Review any supplied Hugging Face dataset for actual Dart/Flutter content, origin, license, sensitive data, duplicates, and executable evidence. A dataset named “DART” can describe something unrelated to the programming language.
7. Split by repository and near-duplicate group before generating training examples. Hold out pilot tasks and their solutions from training; otherwise measured success is misleading.
8. Compare baseline, retrieval, and LoRA on the same held-out tasks, with no test-answer leakage. Record precision/recall, false-positive rate, patch/test success, retrieval grounding, latency, and cost.
9. Publish an adapter/model card only after results and redistribution permissions are verified. Keep the internal model endpoint optional for MCP users.

## What the user should provide next

- Available AMD GPU model/count/VRAM, hourly rate or credit budget, and rental time limit.
- Remote OS and whether ROCm/PyTorch are preconfigured; use an SSH connection/profile, not passwords pasted in chat.
- No dataset needs to be supplied by the user: candidate discovery is being handled here. User-owned additional examples are optional.
- Whether an optional trained reviewer hosted on AMD is the intended deployment, while users still have their own host agents.

No GitLab account or Hugging Face Pro subscription is required for initial local corpus preparation. An HF account may be needed later for gated model access or publishing. Do not send account passwords or tokens in chat.

## Sources

- Flutter docs and attribution: https://docs.flutter.dev/
- Official source: https://github.com/flutter/website
- Runnable sample candidates: https://github.com/flutter/samples
- Baseline model: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- Comparison model: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- Embeddings: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- AMD GPU specifications: https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html
- AMD training workflow: https://developer.amd.com/playbooks/pytorch-finetuning/

## Additional dataset candidates discovered (not downloaded or approved for training)

- [bbidpa/flutter-full-examples-v1](https://huggingface.co/datasets/bbidpa/flutter-full-examples-v1): synthetic complete-widget examples; inspect correctness and generation provenance before use.
- [dartmind/dartmind_dataset](https://huggingface.co/datasets/dartmind/dartmind_dataset): code corpus candidate; verify source licensing, repository splits, and deduplication.
- [Flutter-Code-with-Questions-Dataset-English](https://huggingface.co/datasets/NoirZangetsu/Flutter-Code-with-Questions-Dataset-English): question/code candidate; inspect label quality and rights before use.
- [MobileDev-Bench paper](https://arxiv.org/abs/2603.24946): potential external evaluation source; identify Flutter subset and access/license terms. Keep evaluation solutions out of training.

None of these has been validated here as a reliable state-management/caching bug-fix dataset. Official samples plus tested seeded defects remain the initial executable-data approach.

## Correction after checking the actual event page

The matching Academy Challenge URL now presents the AMD AI League. Its FAQ says AMD GPU notebook infrastructure is provided; participants do not need their own hardware/cloud/API credits. Start at https://notebooks.amd.com/hackathon using AMD Developer Program SSO. It states a 3-hour daily running-session quota and about 25 GB persistent storage. The correct persistent directory depends on notebook type: `/persistent` for `jupyter-hack-...`, `/workspace` for `rgapi-hackathon-...`. Verify these details inside the launched session. Turn off the session when idle.

Consequently, DO NOT rent the MI300X suggested above yet. That specification is an optional fallback, not an event requirement. First inspect the provided GPU and storage. A 7B BF16 model has approximately 14 GB of weights before caches, adapters, and other files; 25 GB persistence is tight. We may need a smaller initial checkpoint or careful temporary-cache/checkpoint handling. Exact training configuration remains pending the environment probe.

The page describes Match 5 as AI-Powered Code Repository Repair and a multi-agent system; do not assume a single-model documentation experiment alone satisfies the submission brief. Confirm the detailed rules for the user's enrolled match before finalizing submission scope. Source: https://lablab.ai/ai-hackathons/amd-lablab-ai-academy-challenge

Dataset inspection update: `bbidpa/flutter-full-examples-v1` lists about 14.6k synthetic examples and Apache-2.0 metadata; validation remains necessary. The English question/code dataset lists MIT metadata but its card also limits use to education/research and preserves original code licenses: hold it out of public-model training until those terms/provenance are resolved. The Dartmind corpus also requires source-level license review. These are candidates, not approved training inputs.


## Current implementation status (15 October 2026)

See [corpus status](FLUTTER_CORPUS_STATUS.md) for acquired-source counts and limitations, and [AMD notebook steps](AMD_NOTEBOOK_NEXT_STEPS.md) for the only user action currently needed. No training or model upload has occurred.


## Radeon environment confirmed by user — 15 October 2026

User reports W7900D 48 GiB, Python 3.14.4, torch 2.13.0+rocm10.0.0, HIP 7.15.26333, 25 GiB workspace and 4 GiB temporary space. These versions are unvalidated. The actual UI is Radeon Cloud: use its instance lifecycle and template PVC rules, not the generic event quota assumptions above. Current next action is the download-free compatibility test in [AMD notebook steps](AMD_NOTEBOOK_NEXT_STEPS.md). No AMD training has run.
