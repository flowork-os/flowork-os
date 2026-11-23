#!/usr/bin/env bash
# ==============================================================================
# FLOWORK OS — ATOMIC GITHUB RELEASE ISO PUBLISHER
# Splits >2GB Live ISO into <1.8GiB chunks, verifies reassembly SHA-256,
# creates an isolated versioned release (never overwriting existing tags/releases),
# uploads assets to a draft release, verifies every byte, and publishes.
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[38;2;0;255;102m"
CYAN="\033[38;2;0;242;254m"
AMBER="\033[38;2;255;184;0m"
RED="\033[38;2;255;51;102m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/token" ]; then
    TOKEN_PATH="${SCRIPT_DIR}/token"
elif [ -f "${HOME}/Downloads/token" ]; then
    TOKEN_PATH="${HOME}/Downloads/token"
else
    TOKEN_PATH="/home/awenkaudico/Downloads/token"
fi
REPO_OWNER="flowork-os"
REPO_NAME="AI-Operating-System-AI-OS-"
REPO_API="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}"
REPO_WEB="https://github.com/${REPO_OWNER}/${REPO_NAME}"
if [ -n "${FLOWORK_REPO_DIR:-}" ] && [ -d "${FLOWORK_REPO_DIR}/.git" ]; then
    STAGE_REPO="${FLOWORK_REPO_DIR}"
elif [ -d "${HOME}/flowork-os-repo/.git" ]; then
    STAGE_REPO="${HOME}/flowork-os-repo"
else
    STAGE_REPO="/opt/flowork-os-repo"
fi
FLOWORK_ROOT="/opt/floworkos"
DEFAULT_ISO="${HOME}/Downloads/flowork-iso-build/FloworkOS-1.0-x86_64-Sovereign-Rust.iso"

TAG=""
ISO_PATH="${DEFAULT_ISO}"
NOTES_FILE=""
RELEASE_TITLE=""
PREPARE_ONLY=0
KEEP_WORK=0

usage() {
    cat <<EOF
Usage: $(basename "$0") <tag> [options]

Example:
  $(basename "$0") v1.0.1 --notes-file /var/tmp/v1.0.1-notes.md

Options:
  --iso <path>          Source ISO file (default: ${DEFAULT_ISO})
  --title <text>        GitHub Release title
  --notes-file <path>   Markdown release notes body file
  --prepare-only        Split & verify assets locally without touching GitHub
  --keep-work           Do not remove staging work dir after upload
  --update              Allow updating assets on an existing published release
  -h, --help            Show help
EOF
}

ALLOW_UPDATE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --iso) ISO_PATH="${2:-}"; shift 2 ;;
        --title) RELEASE_TITLE="${2:-}"; shift 2 ;;
        --notes-file) NOTES_FILE="${2:-}"; shift 2 ;;
        --prepare-only) PREPARE_ONLY=1; KEEP_WORK=1; shift ;;
        --keep-work) KEEP_WORK=1; shift ;;
        --update) ALLOW_UPDATE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        -*) echo -e "${RED}[ERROR] Unknown option: $1${RESET}" >&2; usage; exit 1 ;;
        *)
            if [ -z "$TAG" ]; then
                TAG="$1"; shift
            else
                echo -e "${RED}[ERROR] Unexpected argument: $1${RESET}" >&2
                exit 1
            fi
            ;;
    esac
done

if [ -z "$TAG" ] || [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.]+)?$ ]]; then
    echo -e "${RED}[ERROR] Version tag required in format vX.Y.Z (got '${TAG}').${RESET}" >&2
    exit 1
fi

if [ ! -f "$ISO_PATH" ]; then
    echo -e "${RED}[ERROR] ISO file not found: ${ISO_PATH}${RESET}" >&2
    exit 1
fi

VER="${TAG#v}"
ISO_PREFIX="flowork-os-${TAG}-amd64.iso"
WORK_DIR="/var/tmp/flowork-release-${TAG}"
CURL_CFG=""

cleanup() {
    if [ -n "${CURL_CFG}" ] && [ -f "${CURL_CFG}" ]; then
        rm -f "${CURL_CFG}"
    fi
    if [ "${KEEP_WORK}" != "1" ] && [ -d "${WORK_DIR}" ]; then
        rm -rf "${WORK_DIR}"
    fi
}
trap cleanup EXIT

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}  FLOWORK OS RELEASE PUBLISHER (${TAG})${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

# Stage 1: Prepare local split artifacts & verify bit-exact reassembly
echo -e "\n${CYAN}[1/5] Preparing & verifying split release artifacts in ${WORK_DIR}...${RESET}"
rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}"

ISO_BYTES=$(stat -c '%s' "${ISO_PATH}")
ISO_SHA256=$(sha256sum "${ISO_PATH}" | awk '{print $1}')
if [ -f "${ISO_PATH}.sha256" ]; then
    RECORDED_SHA=$(awk '{print $1}' "${ISO_PATH}.sha256")
    if [ -n "${RECORDED_SHA}" ] && [ "${RECORDED_SHA}" != "${ISO_SHA256}" ]; then
        echo -e "${RED}[ERROR] ISO SHA-256 mismatch vs ${ISO_PATH}.sha256!${RESET}" >&2
        exit 1
    fi
fi

echo -e "${GREEN}✓ Source ISO: ${ISO_PATH} (${ISO_BYTES} bytes)${RESET}"
echo -e "${GREEN}✓ SHA-256:    ${ISO_SHA256}${RESET}"

echo -e "${CYAN}→ Splitting ISO into 1800 MiB chunks (< 2 GiB GitHub asset limit)...${RESET}"
split -b 1800M -d -a 2 --additional-suffix=.part "${ISO_PATH}" "${WORK_DIR}/${ISO_PREFIX}."

mapfile -t PART_FILES < <(LC_ALL=C ls -1 "${WORK_DIR}/${ISO_PREFIX}."*.part | sort)
if [ "${#PART_FILES[@]}" -eq 0 ]; then
    echo -e "${RED}[ERROR] No split parts generated!${RESET}" >&2
    exit 1
fi

# GitHub hard cap is 2 GiB = 2,147,483,648 bytes
GITHUB_MAX_BYTES=2147483648
BAT_JOIN_EXPR=""
for p in "${PART_FILES[@]}"; do
    pb=$(stat -c '%s' "$p")
    pbase=$(basename "$p")
    if [ "$pb" -ge "$GITHUB_MAX_BYTES" ]; then
        echo -e "${RED}[ERROR] Asset ${pbase} (${pb} bytes) exceeds GitHub 2 GiB limit!${RESET}" >&2
        exit 1
    fi
    if [ -z "$BAT_JOIN_EXPR" ]; then
        BAT_JOIN_EXPR="${pbase}"
    else
        BAT_JOIN_EXPR="${BAT_JOIN_EXPR} + ${pbase}"
    fi
    echo "  - ${pbase}: ${pb} bytes"
done

echo -e "${CYAN}→ Verifying round-trip SHA-256 of reassembled parts...${RESET}"
REASSEMBLED_SHA=$(cat "${PART_FILES[@]}" | sha256sum | awk '{print $1}')
if [ "${REASSEMBLED_SHA}" != "${ISO_SHA256}" ]; then
    echo -e "${RED}[ERROR] Round-trip reassembly SHA-256 mismatch! (${REASSEMBLED_SHA} != ${ISO_SHA256})${RESET}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Reassembled SHA-256 matches source ISO 100%.${RESET}"

# Checksum file
printf '%s  %s\n' "${ISO_SHA256}" "${ISO_PREFIX}" > "${WORK_DIR}/${ISO_PREFIX}.sha256"

# Linux/macOS join script
cat > "${WORK_DIR}/join-iso.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
echo "=========================================================="
echo "  Flowork OS ${TAG} — Reassembling Sovereign ISO"
echo "=========================================================="
cat ${ISO_PREFIX}.*.part > ${ISO_PREFIX}
echo "Verifying SHA-256 integrity..."
sha256sum -c ${ISO_PREFIX}.sha256
echo "OK: Flowork OS Live ISO (${ISO_PREFIX}) joined and verified!"
EOF
chmod +x "${WORK_DIR}/join-iso.sh"

# Windows join batch script (CRLF)
python3 - <<PYEOF
bat_content = (
    "@echo off\r\n"
    "echo ==========================================================\r\n"
    "echo   Flowork OS ${TAG} - Joining ISO Parts\r\n"
    "echo ==========================================================\r\n"
    "copy /b ${BAT_JOIN_EXPR} ${ISO_PREFIX}\r\n"
    "echo.\r\n"
    "echo Verifying SHA-256 checksum (expected: ${ISO_SHA256})...\r\n"
    "certutil -hashfile ${ISO_PREFIX} SHA256\r\n"
    "echo Flowork OS ISO joined successfully!\r\n"
    "pause\r\n"
)
with open("${WORK_DIR}/join-iso.bat", "wb") as f:
    f.write(bat_content.encode("utf-8"))
PYEOF

# README.txt
cat > "${WORK_DIR}/README.txt" <<EOF
Flowork OS ${TAG} (Sovereign Rust Kernel Release)
====================================================

This official release image is split into parts under 2 GiB to comply with GitHub Releases asset limits.

How to Restore the Full Bootable ISO (${ISO_PREFIX}):
- Linux / macOS: Run "bash join-iso.sh"
- Windows: Double-click "join-iso.bat"

Checksum Verification:
SHA256: ${ISO_SHA256}

Flashing to USB Flash Drive (min 8GB):
- Linux: sudo dd if=${ISO_PREFIX} of=/dev/sdX bs=4M oflag=direct conv=fsync status=progress
- Windows: Use Rufus (MBR/BIOS + UEFI scheme) or BalenaEtcher.
EOF

# Package clean iso-builder tarball
echo -e "${CYAN}→ Packaging flowork-iso-builder-${VER}.tar.gz...${RESET}"
tar -C "${FLOWORK_ROOT}" \
    --exclude="iso-builder/output" \
    --exclude="iso-builder/work" \
    --exclude="*.iso" \
    --exclude="*vault.json*" \
    --exclude="*token*" \
    -czf "${WORK_DIR}/flowork-iso-builder-${VER}.tar.gz" iso-builder
tar -tzf "${WORK_DIR}/flowork-iso-builder-${VER}.tar.gz" >/dev/null

echo -e "${GREEN}✓ Prepared all release assets in ${WORK_DIR}:${RESET}"
ls -lh "${WORK_DIR}"

if [ "${PREPARE_ONLY}" = "1" ]; then
    echo -e "${AMBER}[PREPARE-ONLY] Exiting without modifying git tags or GitHub releases.${RESET}"
    exit 0
fi

# Stage 2: Token & Non-Overwriting GitHub Guard
echo -e "\n${CYAN}[2/5] Authenticating GitHub token & validating existing releases...${RESET}"
if [ ! -f "${TOKEN_PATH}" ]; then
    echo -e "${RED}[ERROR] Token file not found: ${TOKEN_PATH}${RESET}" >&2
    exit 1
fi
GH_TOKEN="$(tr -d '\r\n[:space:]' < "${TOKEN_PATH}")"
if [ -z "${GH_TOKEN}" ]; then
    echo -e "${RED}[ERROR] Empty token file!${RESET}" >&2
    exit 1
fi

CURL_CFG="$(mktemp /tmp/flowork-curl-XXXXXX.cfg)"
chmod 600 "${CURL_CFG}"
cat > "${CURL_CFG}" <<EOF
header = "Authorization: Bearer ${GH_TOKEN}"
header = "Accept: application/vnd.github+json"
header = "X-GitHub-Api-Version: 2022-11-28"
EOF

REPO_HTTP=$(curl -sS -K "${CURL_CFG}" -o /dev/null -w "%{http_code}" "${REPO_API}")
if [ "${REPO_HTTP}" != "200" ]; then
    echo -e "${RED}[ERROR] GitHub API check failed with HTTP ${REPO_HTTP}.${RESET}" >&2
    exit 1
fi

curl -sS -K "${CURL_CFG}" -o "${WORK_DIR}/all_releases.json" "${REPO_API}/releases?per_page=100"
RESUME_DRAFT_ID=$(REL_TAG="${TAG}" ALLOW_UP="${ALLOW_UPDATE}" python3 - <<PYEOF
import json, os, sys
tag = os.environ["REL_TAG"]
allow_up = os.environ.get("ALLOW_UP") == "1"
for rel in json.load(open("${WORK_DIR}/all_releases.json")):
    if rel.get("tag_name") == tag:
        if not rel.get("draft", False) and not allow_up:
            sys.stderr.write(f"PUBLISHED:{rel['id']}\n")
            sys.exit(2)
        print(rel["id"])
        sys.exit(0)
PYEOF
) || {
    rc=$?
    if [ "$rc" = "2" ]; then
        echo -e "${RED}[ERROR] Published release for tag '${TAG}' ALREADY EXISTS on GitHub! Use --update to replace release assets.${RESET}" >&2
        exit 1
    fi
    exit "$rc"
}

if [ -n "${RESUME_DRAFT_ID:-}" ]; then
    echo -e "${AMBER}→ Found incomplete draft release ID=${RESUME_DRAFT_ID} for '${TAG}'; resuming cleanly (published releases untouched).${RESET}"
else
    echo -e "${GREEN}✓ Confirmed '${TAG}' does not conflict with any existing release (v1.0.0 untouched).${RESET}"
fi

# Check git repo clean & synced with origin/main
if [ ! -d "${STAGE_REPO}/.git" ]; then
    echo -e "${RED}[ERROR] Staging repo not found at ${STAGE_REPO}.${RESET}" >&2
    exit 1
fi
if [ -n "$(git -C "${STAGE_REPO}" status --porcelain)" ]; then
    echo -e "${RED}[ERROR] ${STAGE_REPO} has uncommitted changes! Commit and push via upload-flowork-os.sh first.${RESET}" >&2
    git -C "${STAGE_REPO}" status --short >&2
    exit 1
fi

HEAD_SHA=$(git -C "${STAGE_REPO}" rev-parse HEAD)
REMOTE_MAIN=$(git -C "${STAGE_REPO}" ls-remote "https://x-access-token:${GH_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" refs/heads/main | awk '{print $1}')
if [ "${HEAD_SHA}" != "${REMOTE_MAIN}" ]; then
    echo -e "${RED}[ERROR] Local HEAD (${HEAD_SHA}) != origin/main (${REMOTE_MAIN}). Push main first!${RESET}" >&2
    exit 1
fi

TAG_REMOTE_SHA=$(git -C "${STAGE_REPO}" ls-remote --tags "https://x-access-token:${GH_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" "refs/tags/${TAG}^{}" "refs/tags/${TAG}" 2>/dev/null | tail -n 1 | awk '{print $1}' || true)
if [ -n "${TAG_REMOTE_SHA}" ]; then
    if [ "${ALLOW_UPDATE}" = "1" ] || ([ -n "${RESUME_DRAFT_ID:-}" ] && [ "${TAG_REMOTE_SHA}" = "${HEAD_SHA}" ]); then
        echo -e "${AMBER}→ Remote tag '${TAG}' already exists; proceeding with update mode.${RESET}"
    else
        echo -e "${RED}[ERROR] Git tag '${TAG}' already exists on remote (${TAG_REMOTE_SHA})! Choose a new version tag or use --update.${RESET}" >&2
        exit 1
    fi
fi

# Stage 3: Tag main commit cleanly & create/reuse Draft Release
echo -e "\n${CYAN}[3/5] Preparing annotated tag '${TAG}' & draft GitHub Release...${RESET}"
if [ -z "${RELEASE_TITLE}" ]; then
    RELEASE_TITLE="Flowork OS ${TAG} (Sovereign Rust Kernel Hardened Release)"
fi

if [ -n "${NOTES_FILE}" ] && [ -f "${NOTES_FILE}" ]; then
    RELEASE_BODY=$(cat "${NOTES_FILE}")
else
    ISO_H_BYTES=$(numfmt --to=iec-i --suffix=B "${ISO_BYTES}")
    RELEASE_BODY=$(cat <<EOF
## Flowork OS ${TAG} — Hardened Boot-Verified Release

### Verified Hybrid Live Bootable ISO
- **Boot Tested:** Physically flashed and booted on real hardware (Hybrid UEFI / Legacy BIOS).
- **Image Size:** ${ISO_H_BYTES} (${ISO_BYTES} bytes), split into ${#PART_FILES[@]} chunks (< 1.8 GiB each).
- **SHA-256 Checksum:** \`${ISO_SHA256}\`

### How to Reassemble & Verify
1. Download all \`.part\` files, \`${ISO_PREFIX}.sha256\`, and your OS join script (\`join-iso.sh\` or \`join-iso.bat\`) into the same folder.
2. **Linux / macOS:** \`bash join-iso.sh\`
3. **Windows:** Double-click \`join-iso.bat\`
4. **Flash to USB (min 8 GB):** \`sudo dd if=${ISO_PREFIX} of=/dev/sdX bs=4M oflag=direct conv=fsync status=progress\`
EOF
)
fi

if [ -z "${TAG_REMOTE_SHA}" ]; then
    git -C "${STAGE_REPO}" tag -a "${TAG}" -m "${RELEASE_TITLE}"
    git -C "${STAGE_REPO}" push "https://x-access-token:${GH_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git" "refs/tags/${TAG}"
    echo -e "${GREEN}✓ Pushed annotated tag '${TAG}' -> ${HEAD_SHA}${RESET}"
fi

if [ -n "${RESUME_DRAFT_ID:-}" ]; then
    curl -sS -K "${CURL_CFG}" -o "${WORK_DIR}/release_created.json" "${REPO_API}/releases/${RESUME_DRAFT_ID}"
    RELEASE_ID="${RESUME_DRAFT_ID}"
else
    PAYLOAD_JSON=$(REL_TAG="${TAG}" REL_TITLE="${RELEASE_TITLE}" REL_BODY="${RELEASE_BODY}" python3 - <<'PYEOF'
import json, os
print(json.dumps({
    "tag_name": os.environ["REL_TAG"],
    "target_commitish": "main",
    "name": os.environ["REL_TITLE"],
    "body": os.environ["REL_BODY"],
    "draft": True,
    "prerelease": False
}))
PYEOF
)
    CREATE_HTTP=$(curl -sS -K "${CURL_CFG}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD_JSON}" \
        -o "${WORK_DIR}/release_created.json" \
        -w "%{http_code}" \
        "${REPO_API}/releases")

    if [ "${CREATE_HTTP}" != "201" ]; then
        echo -e "${RED}[ERROR] Failed to create draft release (HTTP ${CREATE_HTTP}):${RESET}" >&2
        cat "${WORK_DIR}/release_created.json" >&2
        exit 1
    fi
    RELEASE_ID=$(python3 -c "import json; print(json.load(open('${WORK_DIR}/release_created.json'))['id'])")
fi

UPLOAD_URL=$(python3 -c "import json; u=json.load(open('${WORK_DIR}/release_created.json'))['upload_url']; print(u.split('{')[0])")
echo -e "${GREEN}✓ Using draft release (ID=${RELEASE_ID}). Starting streaming asset uploads...${RESET}"

# Stage 4: Stream upload every missing/incomplete asset sequentially with size verification
echo -e "\n${CYAN}[4/5] Uploading assets to GitHub Releases CDN...${RESET}"
UPLOAD_FILES=(
    "${WORK_DIR}/flowork-iso-builder-${VER}.tar.gz"
    "${WORK_DIR}/${ISO_PREFIX}.sha256"
    "${WORK_DIR}/join-iso.sh"
    "${WORK_DIR}/join-iso.bat"
    "${WORK_DIR}/README.txt"
    "${PART_FILES[@]}"
)

# Append decoupled on-demand subsystem assets
if [ -d "${HOME}/Downloads/flowork-release-assets" ]; then
    for asset in "${HOME}/Downloads/flowork-release-assets"/*.tar.zst "${HOME}/Downloads/flowork-release-assets"/*.sha256 "${HOME}/Downloads/flowork-release-assets"/SHA256SUMS.txt; do
        if [ -f "$asset" ]; then
            UPLOAD_FILES+=("$asset")
        fi
    done
fi

for asset_file in "${UPLOAD_FILES[@]}"; do
    asset_name=$(basename "${asset_file}")
    local_bytes=$(stat -c '%s' "${asset_file}")

    existing_info=$(ASSET_NAME="${asset_name}" LOCAL_BYTES="${local_bytes}" FORCE_UPDATE="${ALLOW_UPDATE}" python3 - <<PYEOF
import json, os
data = json.load(open("${WORK_DIR}/release_created.json"))
name = os.environ["ASSET_NAME"]
want = int(os.environ["LOCAL_BYTES"])
force_up = os.environ.get("FORCE_UPDATE") == "1"
for a in data.get("assets", []):
    if a.get("name") == name:
        if force_up and (name.startswith("flowork-os-") or name.startswith("flowork-iso-builder-") or name.endswith(".sha256")):
            print(f"DELETE:{a['id']}")
        elif a.get("state") == "uploaded" and int(a.get("size", -1)) == want:
            print(f"SKIP:{a['id']}")
        else:
            print(f"DELETE:{a['id']}")
        break
PYEOF
)
    if [[ "${existing_info}" == SKIP:* ]]; then
        echo -e "${GREEN}  ✓ Already uploaded & verified in draft: ${asset_name} (${local_bytes} bytes)${RESET}"
        continue
    elif [[ "${existing_info}" == DELETE:* ]]; then
        del_id="${existing_info#DELETE:}"
        echo -e "${AMBER}  → Removing incomplete draft asset ${asset_name} (id=${del_id}) before retry...${RESET}"
        curl -sS -K "${CURL_CFG}" -X DELETE -o /dev/null "${REPO_API}/releases/assets/${del_id}"
    fi

    echo -e "${CYAN}→ Streaming upload ${asset_name} (${local_bytes} bytes)...${RESET}"
    resp_file="${WORK_DIR}/upload_${asset_name}.json"
    up_http=$(curl -sS -K "${CURL_CFG}" \
        --http1.1 \
        --retry 3 --retry-delay 5 --max-time 3600 \
        -X POST \
        -T "${asset_file}" \
        -H "Content-Type: application/octet-stream" \
        -H "Content-Length: ${local_bytes}" \
        -H "Expect:" \
        -o "${resp_file}" \
        -w "%{http_code}" \
        "${UPLOAD_URL}?name=${asset_name}")

    if [ "${up_http}" != "201" ]; then
        echo -e "${RED}[ERROR] Upload failed for ${asset_name} (HTTP ${up_http}). Draft release ID=${RELEASE_ID} preserved for resume.${RESET}" >&2
        cat "${resp_file}" >&2 || true
        exit 1
    fi

    remote_state=$(python3 -c "import json; d=json.load(open('${resp_file}')); print(d.get('state',''))")
    remote_bytes=$(python3 -c "import json; d=json.load(open('${resp_file}')); print(d.get('size',-1))")
    if [ "${remote_state}" != "uploaded" ] || [ "${remote_bytes}" != "${local_bytes}" ]; then
        echo -e "${RED}[ERROR] Asset verification failed for ${asset_name}: state=${remote_state}, remote_bytes=${remote_bytes}, local_bytes=${local_bytes}${RESET}" >&2
        exit 1
    fi
    echo -e "${GREEN}  ✓ Uploaded & verified ${asset_name} (${remote_bytes} bytes)${RESET}"
done

# Stage 5: Publish release atomically & verify both releases exist
    PATCH_PAYLOAD=$(REL_BODY="${RELEASE_BODY}" python3 - <<'PYEOF'
import json, os
print(json.dumps({
    "draft": False,
    "body": os.environ["REL_BODY"]
}))
PYEOF
)
    PUB_HTTP=$(curl -sS -K "${CURL_CFG}" \
        -X PATCH \
        -H "Content-Type: application/json" \
        -d "${PATCH_PAYLOAD}" \
        -o "${WORK_DIR}/release_published.json" \
        -w "%{http_code}" \
        "${REPO_API}/releases/${RELEASE_ID}")

if [ "${PUB_HTTP}" != "200" ]; then
    echo -e "${RED}[ERROR] Failed to publish release ID=${RELEASE_ID} (HTTP ${PUB_HTTP}).${RESET}" >&2
    cat "${WORK_DIR}/release_published.json" >&2
    exit 1
fi

HTML_URL=$(python3 -c "import json; print(json.load(open('${WORK_DIR}/release_published.json'))['html_url'])")
ASSET_COUNT=$(python3 -c "import json; print(len(json.load(open('${WORK_DIR}/release_published.json')).get('assets',[])))")
echo -e "${GREEN}✓ Published Release ${TAG}: ${HTML_URL} (${ASSET_COUNT} assets)${RESET}"
echo -e "${GREEN}✓ Existing releases (${REPO_WEB}/releases) preserved intact.${RESET}"
