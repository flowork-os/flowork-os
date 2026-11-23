#!/usr/bin/env python3
"""
👑 FLOWORK OS — EARSHOT MODEL CONTEXT PROTOCOL (MCP) SERVER
Exposes procedural audio synthesis and audio auditing tools to Mr. Flow over standard MCP JSON-RPC.

Tools:
- sfx_list: List all procedural sound effect recipes
- sfx_render: Synthesize sound effects on CPU into .wav files
- sfx_play: Synthesize and instantly play audio through PipeWire
- audio_audit: Inspect audio waveform for clipping, DC offset, and quality metrics

Universal root: /opt/floworkos
Author: Flowork Architecture Board & Dr. Flow
"""

import sys
import os
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from earshot_engine import CATALOG, render_sound, play_sound, audit_audio_file


TOOLS = [
    {
        "name": "sfx_list",
        "description": "List all available procedural sound effects that Mr. Flow can synthesize on CPU.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "sfx_render",
        "description": "Procedurally synthesize a sound effect into a WAV file using pure CPU math without sample buffers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the sound (click, pop, bell, success, error, whoosh, shutter, laser, glass_tap)",
                    "enum": list(CATALOG.keys())
                },
                "output_path": {
                    "type": "string",
                    "description": "Target absolute file path for the .wav output (defaults to /opt/floworkos/sounds/<name>.wav)"
                },
                "duration": {
                    "type": "number",
                    "description": "Optional customized duration in seconds"
                },
                "pitch": {
                    "type": "number",
                    "description": "Optional customized root frequency / pitch in Hz"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "sfx_play",
        "description": "Synthesize and instantly play a procedural sound effect through Flowork OS PipeWire audio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of sound to play (click, pop, bell, success, error, whoosh, shutter, laser, glass_tap)",
                    "enum": list(CATALOG.keys())
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "audio_audit",
        "description": "Audit an audio WAV file for clipping, DC offset, peak amplitude, and dynamic range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the .wav file to inspect"
                }
            },
            "required": ["file_path"]
        }
    }
]


def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})

    if name == "sfx_list":
        res = {k: v["desc"] for k, v in CATALOG.items()}
        return {
            "content": [{"type": "text", "text": json.dumps({"status": "ok", "catalog": res}, indent=2)}]
        }

    elif name == "sfx_render":
        sfx_name = args.get("name")
        out_path = args.get("output_path")
        kwargs = {}
        if "duration" in args:
            kwargs["duration"] = float(args["duration"])
        if "pitch" in args:
            kwargs["pitch"] = float(args["pitch"])

        try:
            saved_file = render_sound(sfx_name, output_path=out_path, **kwargs)
            audit = audit_audio_file(saved_file)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "status": "ok",
                        "rendered_file": saved_file,
                        "duration_sec": audit["duration_seconds"],
                        "peak_dbfs": audit["peak_dbfs"],
                        "quality": audit["status"]
                    }, indent=2)
                }]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": json.dumps({"status": "error", "error": str(e)})}]}

    elif name == "sfx_play":
        sfx_name = args.get("name")
        try:
            ok = play_sound(sfx_name)
            return {
                "content": [{"type": "text", "text": json.dumps({"status": "ok", "played": ok, "sound": sfx_name})}]
            }
        except Exception as e:
            return {"content": [{"type": "text", "text": json.dumps({"status": "error", "error": str(e)})}]}

    elif name == "audio_audit":
        wav_path = args.get("file_path")
        audit = audit_audio_file(wav_path)
        return {
            "content": [{"type": "text", "text": json.dumps(audit, indent=2)}]
        }

    return {"content": [{"type": "text", "text": json.dumps({"error": f"Unknown tool: {name}"})}]}


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "earshot", "version": "1.0.0"}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
            elif method == "tools/call":
                result = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e), "data": traceback.format_exc()}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
