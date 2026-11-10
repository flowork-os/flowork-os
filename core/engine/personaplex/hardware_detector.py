#!/usr/bin/env python3
"""
👑 FLOWORK OS — PERSONAPLEX HARDWARE DETECTOR & TIER SELECTOR
Evaluates system GPU, CUDA runtime, and memory to select optimal voice tier.

Tier 1: NVIDIA RTX GPU Full-Duplex Speech-to-Speech (PersonaPlex)
Tier 2: Ultra-Lightweight CPU Fallback (Whisper + Piper/CPU TTS)
"""

import os
import sys
import shutil
import subprocess


def detect_hardware():
    info = {
        "has_nvidia_device": False,
        "nvidia_gpu_model": "None",
        "nvidia_driver_active": False,
        "cuda_available": False,
        "total_ram_gb": 0,
        "recommended_tier": "TIER_2_CPU_FALLBACK"
    }

    # 1. Total RAM
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    info["total_ram_gb"] = round(kb / (1024 * 1024), 1)
                    break
    except Exception:
        pass

    # 2. Check PCIe for NVIDIA hardware
    try:
        lspci = subprocess.run(["lspci"], capture_output=True, text=True)
        for line in lspci.stdout.split("\n"):
            if "NVIDIA" in line.upper() and ("VGA" in line.upper() or "3D" in line.upper()):
                info["has_nvidia_device"] = True
                # Extract model
                if "[" in line and "]" in line:
                    info["nvidia_gpu_model"] = line.split("[")[1].split("]")[0]
                else:
                    info["nvidia_gpu_model"] = "NVIDIA GPU"
                break
    except Exception:
        pass

    # 3. Check NVIDIA Driver & CUDA
    if shutil.which("nvidia-smi"):
        try:
            smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=2)
            if smi.returncode == 0 and smi.stdout.strip():
                parts = smi.stdout.strip().split(",")
                info["nvidia_gpu_model"] = parts[0].strip()
                info["nvidia_driver_active"] = True
                info["cuda_available"] = True
        except Exception:
            pass

    # Select Tier
    if info["nvidia_driver_active"] and info["cuda_available"] and info["total_ram_gb"] >= 16:
        info["recommended_tier"] = "TIER_1_PERSONAPLEX"
    else:
        info["recommended_tier"] = "TIER_2_CPU_FALLBACK"

    return info


if __name__ == "__main__":
    hw = detect_hardware()
    print("┌────────────────────────────────────────────────────────┐")
    print("│ 🎙️  FLOWORK ACOUSTIC SUITE: HARDWARE ANALYSIS           │")
    print("├────────────────────────────────────────────────────────┤")
    print(f"│ Total System Memory  : {hw['total_ram_gb']} GB")
    print(f"│ NVIDIA Hardware      : {'Detected (' + hw['nvidia_gpu_model'] + ')' if hw['has_nvidia_device'] else 'Not Detected'}")
    print(f"│ Driver / CUDA Active : {'YES' if hw['nvidia_driver_active'] else 'NO (Module unlinked or non-NVIDIA)'}")
    print(f"│ Active Voice Tier    : {hw['recommended_tier']}")
    print("└────────────────────────────────────────────────────────┘")
