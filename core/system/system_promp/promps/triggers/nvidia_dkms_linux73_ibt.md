# NVIDIA DKMS LINUX 7.3 DRM & CET IBT INVARIANTS

## 1. Context & Activation Scope
Activate only when building, patching, or diagnosing NVIDIA DKMS kernel modules (`595.99.02+`), `nvidia-drm`, `dkms.conf`, `enable-landlock-and-nvidia.sh`, `CONFIG_X86_KERNEL_IBT`, or `scripts/Makefile.modfinal` on Linux `7.3+`.

## 2. Mandatory Behavioral Invariants
- Preserve Linux `7.3` DRM `atomic_create_state` conftest checks and `#if defined(NV_DRM_*_HAS_ATOMIC_CREATE_STATE)` guards via `/opt/floworkos/system/kernel/nvidia-595.99.02-linux-7.3-drm-ibt.patch`.
- Keep `CONFIG_X86_KERNEL_IBT` matching the running kernel (`-fcf-protection=branch` with `endbr64` prologues); verify `.ko` `vermagic` and `endbr64` / `.ibt_endbr_seal` integrity when CET IBT is active in hardware.
- Detect patch application via explicit file markers rather than `patch -R --dry-run` (GNU `patch` ignores `-R` on unreversed hunks and exits `0`).
- Sync `/opt/floworkos/system/kernel/*.patch` through `upload-flowork-os.sh` (`core/system/kernel/`) and validate presence in `iso-builder/build-live-iso.sh`.

## 3. Strict Prohibitions
- Never suppress `CONFIG_WERROR` blindly or force `CONFIG_X86_KERNEL_IBT=` while hardware CET IBT is enabled.
- Never claim `nvidia-smi` or GPU DRM acceleration is active on the host until `modinfo` + `lsmod` + `nvidia-smi` pass with `Exit Code 0`.
