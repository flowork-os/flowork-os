---
title: NVIDIA 595.99.02 DKMS Linux 7.3 DRM API & Intel CET IBT Fix
category: kernel
date: 2026-11-11
keywords:
  - nvidia_dkms
  - nvidia_drm
  - linux_7_3
  - atomic_create_state
  - drm_plane_funcs
  - drm_crtc_funcs
  - config_x86_kernel_ibt
  - cet_endbr64
  - config_werror
  - dkms_conf
  - makefile_modfinal
  - conftest_sh
---

# NVIDIA 595.99.02 DKMS Build Fix for Linux 7.3.0-flowork-rust (DRM API + CET IBT)

## Root Causes
1. **Linux 7.3 DRM State Hook Removal (`nvidia-drm/nvidia-drm-crtc.c`):** Upstream Linux `7.3` removed `.reset` on `struct drm_plane_funcs` / `struct drm_crtc_funcs` along with `drm_atomic_helper_{plane,crtc}_reset()`, replacing them with `.atomic_create_state` (returning `ERR_PTR(-ENOMEM)` on allocation failure) and `__drm_atomic_helper_{plane,crtc}_state_init(state, obj)` from `<drm/drm_atomic_state_helper.h>`.
2. **Stage-2 `Makefile.modfinal` `-Werror=attributes` vs `CONFIG_X86_KERNEL_IBT=y`:** Upstream `dkms.conf` forced `CONFIG_X86_KERNEL_IBT=` in `MAKE[0]`, injecting `-fcf-protection=none` while kernel `autoconf.h` kept `CONFIG_X86_KERNEL_IBT 1`. With `CONFIG_WERROR=y`, `__noendbr` expanded to `__attribute__((nocf_check))` and aborted all `*.mod.o` / `.module-common.o` builds. Furthermore, leaving `-fcf-protection=none` on a CET-active CPU risks `#CP` faults on indirect calls into module wrappers.
3. **`drm/drm_fb_helper.h` Removed in Linux 7.3 (`CONFIG_DRM_TTM_HELPER=m` triggers `NV_DRM_FBDEV_AVAILABLE`):** Enabling multi-vendor GPU drivers (`amdgpu`, `xe`, `nouveau`, `radeon`) activates `CONFIG_DRM_TTM_HELPER=m`, turning on `NV_DRM_FBDEV_AVAILABLE` in `nvidia-drm-conftest.h`. Upstream `conftest.sh` (`drm_fbdev_generic_setup`, `drm_fbdev_ttm_setup`, `drm_client_setup`) and `nvidia-drm/nvidia-drm-drv.c` hardcoded `#include <drm/drm_fb_helper.h>`, whereas Linux 7.3 moved it to `<drm/clients/drm_fbdev_helper.h>`.

## Verified Fix & Integration
- **Unified Patches:** `/opt/floworkos/system/kernel/nvidia-595.99.02-linux-7.3-drm-ibt.patch` + `/opt/floworkos/system/kernel/nvidia-595.99.02-linux-7.3-fbdev-helper.patch` patch `/usr/src/nvidia-595.99.02`:
  - `conftest.sh` & `nvidia-drm/nvidia-drm-sources.mk`: Add `drm_plane_funcs_has_atomic_create_state` and `drm_crtc_funcs_has_atomic_create_state` (`CAT="types"`).
  - `nvidia-drm/nvidia-drm-crtc.c`: Implement `nv_drm_plane_atomic_create_state` and `nv_drm_atomic_crtc_create_state` guarded by conftest defines while keeping `#else` fallback for older kernels.
  - `dkms.conf`: Drop `CONFIG_X86_KERNEL_IBT=` from `MAKE[0]` so `-fcf-protection=branch` and `endbr64` stay active (`nv-kernel.o_binary` and `nv-modeset-kernel.o_binary` already ship `endbr64` prologues; `.ibt_endbr_seal` passes `objtool --ibt` + `MODPOST`).
  - `header-presence-tests.mk`, `conftest.sh`, & `nvidia-drm/nvidia-drm-drv.c`: Detect `drm/drm_fb_helper.h` vs `drm/clients/drm_fbdev_helper.h` via `NV_DRM_CLIENTS_DRM_FBDEV_HELPER_H_PRESENT` and guard includes cleanly for both Linux <=7.2 and >=7.3.
- **Idempotency Trap in GNU `patch`:** `patch -R --dry-run` on an unpatched source exits `0` (`Unreversed patch detected! Ignoring -R.`). `/opt/floworkos/system/kernel/enable-landlock-and-nvidia.sh` avoids `-R` probing and explicitly greps file markers across the patched files before calling `patch -p1 -N --batch --no-backup-if-mismatch`.
- **Distribution Parity:** Both `/home` paths and tokens stay excluded; `upload-flowork-os.sh` syncs `system/kernel/*.patch` into `core/system/kernel/`, and `iso-builder/build-live-iso.sh` audits both patches + DKMS status during pre-flight.
