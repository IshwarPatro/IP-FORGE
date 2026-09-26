#!/usr/bin/env bash
# ==============================================================================
# IP FORGE: AMD Developer Cloud vLLM ROCm Launch Script
# Deploys high-throughput vLLM OpenAI-compatible server on AMD Instinct / Radeon GPUs.
# ==============================================================================

set -euo pipefail

MODEL_NAME="${MODEL_NAME:-meta-llama/Meta-Llama-3-70B-Instruct}"
SERVE_HOST="${SERVE_HOST:-0.0.0.0}"
SERVE_PORT="${SERVE_PORT:-8000}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.92}"
DTYPE="${DTYPE:-bfloat16}"

echo "=================================================================="
echo "         IP FORGE: Starting vLLM Serving Engine on AMD ROCm       "
echo "=================================================================="
echo "Target Model:             ${MODEL_NAME}"
echo "Serving Address:          http://${SERVE_HOST}:${SERVE_PORT}/v1"
echo "Tensor Parallel GPUs:     ${TENSOR_PARALLEL_SIZE}"
echo "Context Window Limit:     ${MAX_MODEL_LEN} tokens"
echo "Precision / Dtype:        ${DTYPE}"
echo "GPU Memory Utilization:   ${GPU_MEMORY_UTILIZATION}"
echo "=================================================================="

# Export ROCm & HIP Optimization Flags
export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export VLLM_ROCM_PAGED_ATTN=1
export NCCL_DEBUG=WARN
export PYTORCH_HIP_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"

# Start the OpenAI-Compatible vLLM Server
exec python3 -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_NAME}" \
    --host "${SERVE_HOST}" \
    --port "${SERVE_PORT}" \
    --tensor-parallel-size "${TENSOR_PARALLEL_SIZE}" \
    --dtype "${DTYPE}" \
    --max-model-len "${MAX_MODEL_LEN}" \
    --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
    --trust-remote-code \
    --disable-log-requests
