#!/usr/bin/env python3
"""
rea_runner.py - Orchestrator for Stickman Viral Concept REA Pipeline.
Automates the complete lifecycle: Deduplication -> Concept Breakdown -> Screenplay ->
Neural Voiceover -> Procedural SFX -> 2D Stickman Render -> SEO Scoring -> Packaging to finish/
"""

import sys
import os
import argparse
import subprocess
import json
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger
import ingest


def run_cmd(cmd: list, cwd: str = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}): {res.stderr}")
    return res.stdout


def step_scaffold(slug: str) -> str:
    proj_dir = f"/opt/floworkos/pipelines/stickman_{slug}"
    os.makedirs(proj_dir, exist_ok=True)
    return proj_dir


def step_package_to_finish(slug: str, master_video_path: str, sidecar_txt_path: str, seo_md_path: str, contact_sheet_path: str = None):
    """
    Deploys final deliverables to /home/awenkaudico/Documents/videos/finish/ and mirrors to /opt/floworkos/documents/videos/finish/
    """
    dest_dirs = [
        "/home/awenkaudico/Documents/videos/finish",
        "/opt/floworkos/documents/videos/finish"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)
        run_cmd(["cp", "-v", master_video_path, d + "/"])
        run_cmd(["cp", "-v", sidecar_txt_path, d + "/"])
        run_cmd(["cp", "-v", seo_md_path, d + "/"])
        if contact_sheet_path and os.path.exists(contact_sheet_path):
            run_cmd(["cp", "-v", contact_sheet_path, d + "/"])

        # Fix ownership
        subprocess.run(["chown", "-R", "awenkaudico:awenkaudico", d])
        subprocess.run(["chmod", "-R", "664", d])
        subprocess.run(["chmod", "775", d])


def main():
    parser = argparse.ArgumentParser(description="Stickman REA Orchestrator")
    parser.add_argument("query", help="YouTube URL or Topic Title to remake")
    parser.add_argument("--force", action="store_true", help="Force remake even if duplicate exists")
    args = parser.parse_args()

    print("=" * 80)
    print("🎬 [STICKMAN REA ENGINE] INGESTION & DEDUPLICATION GATE")
    print("=" * 80)

    # 1. Gatekeeper & Blueprint
    blueprint = ingest.ingest_concept(args.query, force=args.force)
    if blueprint.get("status") == "duplicate":
        print("Aborting: Concept already remade.")
        sys.exit(2)

    slug = blueprint["slug"]
    proj_dir = step_scaffold(slug)
    print(f"✅ Project Scaffolding Initialized: {proj_dir}")
    print(f"✅ Blueprint generated for topic: '{blueprint['source_title']}'")
    print("Next step: Proceed to scriptwriting, audio synthesis, and procedural rendering.")


if __name__ == "__main__":
    main()
