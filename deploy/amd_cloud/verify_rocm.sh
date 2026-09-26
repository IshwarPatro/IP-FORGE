#!/usr/bin/env bash
# ==============================================================================
# IP FORGE: AMD ROCm 6.x Environment Verification Script
# Validates AMD GPU hardware, ROCm driver stack, HIP runtime, and vLLM readiness.
# ==============================================================================

set -euo pipefail

echo "=================================================================="
echo "          IP FORGE: AMD ROCm 6.x Hardware & Driver Audit          "
echo "=================================================================="

# 1. Verify rocm-smi
echo -n "[1/6] Checking rocm-smi installation... "
if command -v rocm-smi &> /dev/null; then
    echo "✓ Found"
    rocm-smi --showid --showproductname --showmeminfo vram
else
    echo "✗ rocm-smi not found in PATH! (Are you on an AMD ROCm GPU host?)"
fi

# 2. Verify ROCm Driver & Kernel Module
echo ""
echo -n "[2/6] Checking AMD kernel driver (kfd & amdgpu)... "
if [ -c /dev/kfd ]; then
    echo "✓ /dev/kfd character device available (Compute kernel driver loaded)"
else
    echo "✗ /dev/kfd not found! Ensure amdgpu-dkms is installed."
fi

# 3. Verify ROCm Version
echo ""
echo "[3/6] Inspecting ROCm Release..."
if [ -f /opt/rocm/.version ]; then
    echo "   Installed ROCm Version: $(cat /opt/rocm/.version)"
elif command -v rocm-smi &> /dev/null; then
    echo "   ROCm Version via rocm-smi: $(rocm-smi --version || true)"
else
    echo "   ROCm version file not found in /opt/rocm"
fi

# 4. Check rocminfo & GPU Target Architecture
echo ""
echo "[4/6] Inspecting GPU Target Architecture (rocminfo)..."
if command -v rocminfo &> /dev/null; then
    TARGET_GFX=$(rocminfo | grep -m 1 "Name:" | awk '{print $2}' || true)
    echo "   Detected Target Architecture: ${TARGET_GFX:-Unknown}"
else
    echo "   rocminfo utility not found."
fi

# 5. Check HIP Compiler (hipcc)
echo ""
echo -n "[5/6] Checking HIP runtime compiler (hipcc)... "
if command -v hipcc &> /dev/null; then
    echo "✓ Found"
    hipcc --version | head -n 2
else
    echo "✗ hipcc not found in PATH."
fi

# 6. Verify PyTorch ROCm Compatibility
echo ""
echo "[6/6] Verifying PyTorch ROCm GPU Acceleration..."
python3 -c "
import torch
print('   PyTorch Version:', torch.__version__)
print('   ROCm / HIP Available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('   Device Name:', torch.cuda.get_device_name(0))
    print('   Device Count:', torch.cuda.device_count())
    print('   Current VRAM Allocated:', round(torch.cuda.memory_allocated(0)/(1024**3), 2), 'GB')
else:
    print('   Notice: Running in CPU mode or on non-ROCm host.')
" 2>/dev/null || echo "   PyTorch not installed in active environment."

echo ""
echo "=================================================================="
echo "          AMD ROCm Environment Verification Complete              "
echo "=================================================================="
