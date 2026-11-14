#!/usr/bin/env python3
"""
👑 Sovereign Cloudflare Pages Direct Deployer
Zero npm/wrangler dependencies - Native Blake3 & Cloudflare Pages V4 REST Protocol
"""

import os
import sys
import json
import base64
import blake3
import uuid
import mimetypes
import urllib.request
import urllib.error
import time

CF_CONFIG_PATH = "/home/awenkaudico/Downloads/cloudeflare"
PUBLIC_DIR = "/opt/floworkos/apps/dramaboxflow/web/public"
WORKER_PATH = "/opt/floworkos/apps/dramaboxflow/web/_worker.js"
PROJECT_NAME = "dramaboxflow"

mimetypes.add_type("application/json", ".json")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/html", ".html")
mimetypes.add_type("image/png", ".png")

def log(msg):
    print(f"[CF-DEPLOY] {msg}", flush=True)

def read_credentials():
    if not os.path.exists(CF_CONFIG_PATH):
        raise FileNotFoundError(f"Cloudflare credentials file missing: {CF_CONFIG_PATH}")
    with open(CF_CONFIG_PATH, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    token = lines[2]
    account_id = lines[5]
    return token, account_id

def compute_cloudflare_hash(content: bytes, ext: str) -> str:
    # Cloudflare Pages hashFile formula:
    # blake3(base64(content) + ext).hex[:32]
    b64_str = base64.b64encode(content).decode("ascii")
    raw_to_hash = (b64_str + ext).encode("utf-8")
    return blake3.blake3(raw_to_hash).hexdigest()[:32]

def get_upload_token(account_id: str, token: str) -> str:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{PROJECT_NAME}/upload-token"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if not data.get("success"):
            raise RuntimeError(f"Failed to get upload token: {data}")
        return data["result"]["jwt"]

def check_missing_hashes(jwt: str, hashes: list) -> list:
    url = "https://api.cloudflare.com/client/v4/pages/assets/check-missing"
    payload = json.dumps({"hashes": hashes}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {jwt}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data.get("result", [])

def upload_assets(jwt: str, asset_payloads: list):
    # Upload in batches of up to 25 items or ~20MB
    batch = []
    current_size = 0
    max_batch_size = 20 * 1024 * 1024

    for item in asset_payloads:
        item_size = len(item["value"])
        if current_size + item_size > max_batch_size and batch:
            _send_batch(jwt, batch)
            batch = []
            current_size = 0
        batch.append(item)
        current_size += item_size

    if batch:
        _send_batch(jwt, batch)

def _send_batch(jwt: str, batch: list):
    url = "https://api.cloudflare.com/client/v4/pages/assets/upload"
    payload = json.dumps(batch).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {jwt}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if not data.get("success"):
            raise RuntimeError(f"Asset upload failed: {data}")
        log(f"Uploaded batch of {len(batch)} assets. Success count: {data.get('result', {}).get('successful_key_count')}")

def create_worker_bundle():
    with open(WORKER_PATH, "rb") as f:
        worker_code = f.read()

    inner_boundary = f"----InnerWorkerBoundary{uuid.uuid4().hex}"
    inner_metadata = {
        "main_module": "_worker.js",
        "compatibility_date": "2026-11-14",
        "compatibility_flags": []
    }

    parts = []
    # Metadata part
    parts.append(
        f"--{inner_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"metadata\"\r\n"
        f"Content-Type: application/json\r\n\r\n"
        + json.dumps(inner_metadata) + "\r\n"
    )
    # _worker.js script part
    parts.append(
        f"--{inner_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"_worker.js\"; filename=\"_worker.js\"\r\n"
        f"Content-Type: application/javascript+module\r\n\r\n"
    )
    bundle_bytes = "".join(parts).encode("utf-8") + worker_code + f"\r\n--{inner_boundary}--\r\n".encode("utf-8")
    return bundle_bytes, inner_boundary

def create_deployment(account_id: str, token: str, manifest: dict, worker_bundle: bytes, worker_boundary: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{PROJECT_NAME}/deployments"
    outer_boundary = f"----OuterDeployBoundary{uuid.uuid4().hex}"

    outer_parts = []
    # 0. Branch (promotes to production)
    outer_parts.append(
        f"--{outer_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"branch\"\r\n\r\n"
        f"main\r\n"
    )
    # 1. Manifest
    outer_parts.append(
        f"--{outer_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"manifest\"\r\n\r\n"
        + json.dumps(manifest) + "\r\n"
    )
    # 2. _worker.bundle
    outer_parts.append(
        f"--{outer_boundary}\r\n"
        f"Content-Disposition: form-data; name=\"_worker.bundle\"; filename=\"_worker.bundle\"\r\n"
        f"Content-Type: multipart/form-data; boundary={worker_boundary}\r\n\r\n"
    )
    outer_body = "".join(outer_parts).encode("utf-8") + worker_bundle + f"\r\n--{outer_boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=outer_body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={outer_boundary}")

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if not data.get("success"):
            raise RuntimeError(f"Deployment failed: {data}")
        return data["result"]

def wait_for_deployment(account_id: str, token: str, deployment_id: str, max_wait=30):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{PROJECT_NAME}/deployments/{deployment_id}"
    log(f"Waiting for deployment {deployment_id} to complete...")
    for i in range(max_wait):
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            stage = data["result"].get("latest_stage", {})
            status = stage.get("status")
            name = stage.get("name")
            log(f"Stage '{name}': status = {status} (elapsed: {i+1}s)")
            if status == "success":
                return data["result"]
            if status == "failure":
                raise RuntimeError(f"Deployment failed in stage '{name}': {data['result']}")
        time.sleep(1)
    raise TimeoutError("Deployment did not complete within timeout")

def main():
    log("Starting Cloudflare Pages deployment...")
    token, account_id = read_credentials()
    log(f"Loaded credentials for Account ID: {account_id[:6]}...{account_id[-6:]}")

    # 1. Scan and hash static assets
    manifest = {}
    file_map = {}
    for root, _, files in os.walk(PUBLIC_DIR):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            rel_path = "/" + os.path.relpath(fpath, PUBLIC_DIR).replace("\\", "/")
            ext = os.path.splitext(fname)[1].lstrip(".")
            with open(fpath, "rb") as f:
                content = f.read()
            h = compute_cloudflare_hash(content, ext)
            manifest[rel_path] = h
            mime_type, _ = mimetypes.guess_type(fpath)
            file_map[h] = {
                "path": rel_path,
                "content": content,
                "b64": base64.b64encode(content).decode("ascii"),
                "mime": mime_type or "application/octet-stream"
            }
            log(f"Asset: {rel_path:30} -> Hash: {h} ({len(content)} bytes)")

    log(f"Total static assets to manifest: {len(manifest)}")

    # 2. Get JWT upload token
    jwt = get_upload_token(account_id, token)
    log("Obtained Pages Direct Upload JWT token.")

    # 3. Check missing hashes
    missing = check_missing_hashes(jwt, list(file_map.keys()))
    log(f"Missing assets to upload: {len(missing)} of {len(file_map)}")

    # 4. Upload missing assets
    if missing:
        payloads = []
        for h in missing:
            finfo = file_map[h]
            payloads.append({
                "key": h,
                "value": finfo["b64"],
                "metadata": {
                    "contentType": finfo["mime"]
                },
                "base64": True
            })
        upload_assets(jwt, payloads)
    else:
        log("All assets already present on Cloudflare Edge store (cached).")

    # 5. Build worker bundle
    log("Building _worker.bundle...")
    worker_bundle, worker_boundary = create_worker_bundle()
    log(f"_worker.bundle ready ({len(worker_bundle)} bytes).")

    # 6. Deploy
    log("Submitting deployment to Cloudflare Pages...")
    dep_result = create_deployment(account_id, token, manifest, worker_bundle, worker_boundary)
    dep_id = dep_result["id"]
    dep_url = dep_result.get("url")
    log(f"Deployment triggered! ID: {dep_id}, Preview URL: {dep_url}")

    # 7. Wait
    final_res = wait_for_deployment(account_id, token, dep_id)
    log(f"SUCCESS! Production URL: https://{PROJECT_NAME}.pages.dev")
    log(f"Preview URL: {final_res.get('url')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
