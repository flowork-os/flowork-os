#!/usr/bin/env python3
"""
⚡ FLOWORK OS — LLMS.TXT GENERATOR CLI
Generates standard-compliant /llms.txt and /llms-full.txt for web apps and sites.
Enables instant discovery for autonomous AI swarms and LLM search agents.
"""

import sys
import os
import argparse
from pathlib import Path

LLMS_TXT_TEMPLATE = """# {project_name}

> {project_summary}

## Overview
{project_description}

## Core Capabilities & Features
{features_block}

## Documentation & API Endpoints
{docs_block}

## Technical Constraints & Integration
- Architecture: {architecture}
- Content Negotiation: Header `Accept: text/markdown` preferred for AI agents.
- License: {license}
"""

def generate_llms_txt(project_name: str, summary: str, description: str, features: list, docs: list, arch: str, lic: str) -> str:
    feat_text = "\n".join([f"- {f}" for f in features]) if features else "- Autonomous agent ready\n- Sovereign interface"
    doc_text = "\n".join([f"- [{d['title']}]({d['url']}): {d.get('desc', '')}" for d in docs]) if docs else "- [Architecture](docs/ARCHITECTURE.md): System design and contracts"

    return LLMS_TXT_TEMPLATE.format(
        project_name=project_name,
        project_summary=summary,
        project_description=description,
        features_block=feat_text,
        docs_block=doc_text,
        architecture=arch,
        license=lic
    )

def main():
    parser = argparse.ArgumentParser(description="Generate standard-compliant /llms.txt")
    parser.add_argument("--name", required=True, help="Project / Website name")
    parser.add_argument("--summary", required=True, help="One-line summary for AI models")
    parser.add_argument("--desc", default="High-performance autonomous application platform.", help="Detailed overview")
    parser.add_argument("--arch", default="Flowork Sovereign Architecture", help="Architecture description")
    parser.add_argument("--license", default="Proprietary / Sovereign", help="Software license")
    parser.add_argument("--out", default="llms.txt", help="Output file path (default: llms.txt)")
    args = parser.parse_args()

    content = generate_llms_txt(
        project_name=args.name,
        summary=args.summary,
        description=args.desc,
        features=[
            "Autonomous Tool Interception & Agentic Workflow",
            "High-Density Semantic Information Extraction",
            "Sub-Millisecond Edge Evaluation"
        ],
        docs=[
            {"title": "Core System Mandates", "url": "/docs/mandates", "desc": "Security and execution boundaries"},
            {"title": "API Specification", "url": "/api/v1", "desc": "REST and MCP tool interfaces"}
        ],
        arch=args.arch,
        lic=args.license
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding='utf-8')
    print(f"✅ Generated standard-compliant llms.txt at: {out_path.resolve()}")
    sys.exit(0)

if __name__ == "__main__":
    main()
