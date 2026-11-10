#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — DYNAMIC SOVEREIGN TOOL CALL EXECUTOR
 * Decoupled modular execution dispatcher for MrFlow CLI (Flowork OS).
 * Receives tool name in argv[2] and JSON arguments via stdin.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const TOOLS_DIR = path.resolve(__dirname);

function main() {
    const toolName = process.argv[2];
    if (!toolName) {
        console.error("Error: Tool name argument missing.");
        process.exit(1);
    }

    let inputData = '';
    try {
        inputData = fs.readFileSync(0, 'utf8');
    } catch (_) {
        inputData = '{}';
    }

    const toolDir = path.join(TOOLS_DIR, toolName);
    if (!fs.existsSync(toolDir)) {
        console.error(`Error: Tool '${toolName}' not found in ${TOOLS_DIR}`);
        process.exit(1);
    }

    // Determine executable in priority order: run -> run.js -> run.sh -> run.py
    const candidates = [
        { file: path.join(toolDir, 'run'), cmd: path.join(toolDir, 'run'), args: [] },
        { file: path.join(toolDir, 'run.js'), cmd: process.execPath, args: [path.join(toolDir, 'run.js')] },
        { file: path.join(toolDir, 'run.sh'), cmd: '/bin/bash', args: [path.join(toolDir, 'run.sh')] },
        { file: path.join(toolDir, 'run.py'), cmd: '/usr/bin/python3', args: [path.join(toolDir, 'run.py')] }
    ];

    let target = null;
    for (const c of candidates) {
        if (fs.existsSync(c.file)) {
            target = c;
            break;
        }
    }

    if (!target) {
        console.error(`Error: No executable handler (run, run.js, run.sh, run.py) found for tool '${toolName}'.`);
        process.exit(1);
    }

    try {
        const res = spawnSync(target.cmd, target.args, {
            input: inputData,
            encoding: 'utf8',
            env: { ...process.env, FLOWORK_TOOL_NAME: toolName },
            maxBuffer: 20 * 1024 * 1024
        });

        if (res.error) {
            console.error(`Execution error: ${res.error.message}`);
            process.exit(1);
        }

        if (res.status !== 0 && res.stderr) {
            process.stderr.write(res.stderr);
            process.exit(res.status || 1);
        }

        process.stdout.write(res.stdout || '{"status": "ok"}');
    } catch (err) {
        console.error(`Fatal dispatch error: ${err.message}`);
        process.exit(1);
    }
}

main();
