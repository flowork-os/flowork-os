#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN BROWSER MCP DISPATCH CLIENT
 * Bridges standalone Flowork OS browser tools to the Chrome DevTools MCP backend.
 */

const { spawn } = require('child_process');

function killTree(proc) {
    if (!proc) return;
    try {
        if (proc.pid) {
            process.kill(-proc.pid, 'SIGKILL');
        }
    } catch (_) {
        try { proc.kill('SIGKILL'); } catch (_) {}
    }
}

function callMcpTool(toolName, toolArgs = {}) {
    return new Promise((resolve, reject) => {
        const p = spawn('/opt/floworkos/tools/browser_backend/run.sh', [
            '--headless',
            '--no-usage-statistics',
            '--userDataDir=/tmp/flowork_sovereign_browser_profile'
        ], {
            stdio: ['pipe', 'pipe', 'pipe'],
            detached: true
        });

        const cleanup = () => killTree(p);
        process.once('SIGTERM', cleanup);
        process.once('SIGINT', cleanup);
        process.once('exit', cleanup);

        let output = '';
        let resolved = false;

        const finalize = () => {
            process.removeListener('SIGTERM', cleanup);
            process.removeListener('SIGINT', cleanup);
            process.removeListener('exit', cleanup);
            killTree(p);
        };

        p.stdout.on('data', (d) => {
            output += d.toString();
            const lines = output.split('\n');
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const msg = JSON.parse(line);
                    if (msg.id === 2) {
                        resolved = true;
                        finalize();
                        if (msg.error) {
                            reject(new Error(msg.error.message || JSON.stringify(msg.error)));
                        } else {
                            try {
                                const lifecycle = require('/opt/floworkos/tools/lifecycle_manager.js');
                                lifecycle.onToolExecuted(toolName, {
                                    reason: `Executed browser tool ${toolName}`,
                                    keywords: ['browser', 'web', 'page', 'dom', toolName]
                                });
                            } catch (_) {}
                            resolve(msg.result);
                        }
                    }
                } catch (_) {}
            }
        });

        p.stderr.on('data', () => {});

        p.on('error', (err) => {
            if (!resolved) {
                resolved = true;
                reject(err);
            }
        });

        // Step 1: Initialize MCP session
        p.stdin.write(JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'initialize',
            params: {
                protocolVersion: '2024-11-05',
                capabilities: {},
                clientInfo: { name: 'flowork-tool-runner', version: '1.0' }
            }
        }) + '\n');

        // Step 2: Dispatch tool execution
        setTimeout(() => {
            if (!resolved) {
                p.stdin.write(JSON.stringify({
                    jsonrpc: '2.0',
                    id: 2,
                    method: 'tools/call',
                    params: {
                        name: toolName,
                        arguments: toolArgs
                    }
                }) + '\n');
            }
        }, 800);

        // Step 3: Safety timeout
        setTimeout(() => {
            if (!resolved) {
                resolved = true;
                finalize();
                reject(new Error(`Timeout calling browser MCP tool: ${toolName}`));
            }
        }, 12000);
    });
}

// CLI execution helper
async function runCli(rawToolName) {
    let args = {};
    if (process.argv[2]) {
        try {
            args = JSON.parse(process.argv[2]);
        } catch (_) {
            args = { input: process.argv[2] };
        }
    }

    try {
        const res = await callMcpTool(rawToolName, args);
        if (res && res.content) {
            for (const item of res.content) {
                if (item.type === 'text') {
                    console.log(item.text);
                } else if (item.type === 'image') {
                    console.log(`[IMAGE DATA: ${item.mimeType}, size: ${item.data?.length || 0} bytes]`);
                }
            }
        } else {
            console.log(JSON.stringify(res, null, 2));
        }
        process.exit(0);
    } catch (err) {
        console.error(`FLOWORK BROWSER TOOL ERROR: ${err.message}`);
        process.exit(1);
    }
}

module.exports = { callMcpTool, runCli };

if (require.main === module) {
    const targetTool = process.argv[2] || 'list_pages';
    runCli(targetTool);
}
