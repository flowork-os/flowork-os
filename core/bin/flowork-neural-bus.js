#!/usr/bin/env node
/**
 * 👑 FLOWORK OS — NEURAL BUS DAEMON (flowork-neural-bus)
 * High-performance semantic IPC over UNIX Domain Socket (/run/flowork/bus.sock)
 * and Localhost HTTP/SSE Bridge (:18095) for all 16+ Craft Suite applications.
 */

const fs = require('fs');
const http = require('http');
const net = require('net');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');

const HTTP_PORT = process.env.FLOWORK_BUS_PORT || 18095;
const RUN_DIR = '/run/flowork';
const FALLBACK_DIR = path.join(os.homedir() || '/tmp', '.flowork');
const SOCKET_NAME = 'bus.sock';

// Resolve socket path with fallback
let SOCKET_PATH = path.join(RUN_DIR, SOCKET_NAME);
try {
    if (!fs.existsSync(RUN_DIR)) {
        fs.mkdirSync(RUN_DIR, { recursive: true, mode: 0o777 });
    }
    // Test write
    fs.accessSync(RUN_DIR, fs.constants.W_OK);
} catch (_) {
    if (!fs.existsSync(FALLBACK_DIR)) {
        fs.mkdirSync(FALLBACK_DIR, { recursive: true, mode: 0o755 });
    }
    SOCKET_PATH = path.join(FALLBACK_DIR, SOCKET_NAME);
}

// Clean stale socket
if (fs.existsSync(SOCKET_PATH)) {
    try { fs.unlinkSync(SOCKET_PATH); } catch (_) {}
}

// State
const MAX_HISTORY = 100;
const eventHistory = [];
const unixClients = new Set();
const sseClients = new Set();
const registeredApps = new Map(); // app_id -> { lastSeen, capabilities, name }

function recordEvent(evt) {
    evt.id = 'evt_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 4);
    evt.timestamp = new Date().toISOString();
    eventHistory.push(evt);
    if (eventHistory.length > MAX_HISTORY) {
        eventHistory.shift();
    }
    return evt;
}

function broadcastEvent(evt) {
    const raw = JSON.stringify(evt);
    const line = raw + '\n';

    // Broadcast to UNIX socket clients
    for (const client of unixClients) {
        try {
            client.write(line);
        } catch (_) {
            unixClients.delete(client);
        }
    }

    // Broadcast to HTTP SSE clients
    const sseData = `data: ${raw}\n\n`;
    for (const res of sseClients) {
        try {
            res.write(sseData);
        } catch (_) {
            sseClients.delete(res);
        }
    }
}

// ==============================================================================
// 1. UNIX DOMAIN SOCKET SERVER
// ==============================================================================
const unixServer = net.createServer((socket) => {
    unixClients.add(socket);
    let buffer = '';

    socket.on('data', (chunk) => {
        buffer += chunk.toString('utf8');
        let lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            try {
                const msg = JSON.parse(trimmed);
                handleIncomingMessage(msg, (reply) => {
                    socket.write(JSON.stringify(reply) + '\n');
                });
            } catch (err) {
                socket.write(JSON.stringify({ error: err.message, status: 'error' }) + '\n');
            }
        }
    });

    socket.on('close', () => unixClients.delete(socket));
    socket.on('error', () => unixClients.delete(socket));
});

unixServer.listen(SOCKET_PATH, () => {
    try { fs.chmodSync(SOCKET_PATH, 0o666); } catch (_) {}
    // Standard universal symlink for cross-app client discovery
    const TMP_SYMLINK = '/tmp/flowork-neural-bus.sock';
    try {
        if (fs.existsSync(TMP_SYMLINK)) fs.unlinkSync(TMP_SYMLINK);
        fs.symlinkSync(SOCKET_PATH, TMP_SYMLINK);
    } catch (_) {}
    console.log(`⚡ Flowork Neural Bus UNIX Socket active: ${SOCKET_PATH}`);
    console.log(`⚡ Standard Symlink: /tmp/flowork-neural-bus.sock`);
});

// ==============================================================================
// 2. HTTP & SERVER-SENT EVENTS (SSE) SERVER (:18095)
// ==============================================================================
const httpServer = http.createServer((req, res) => {
    // Enable CORS for Quantum Glass micro-webviews
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        return res.end();
    }

    const url = new URL(req.url, `http://127.0.0.1:${HTTP_PORT}`);
    const pathname = url.pathname;

    // Health
    if (pathname === '/health' || pathname === '/api/bus/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            status: 'ok',
            bus: 'Flowork Neural Bus v1.0.0',
            socket: SOCKET_PATH,
            unix_clients: unixClients.size,
            sse_clients: sseClients.size,
            events_recorded: eventHistory.length,
            registered_apps: Array.from(registeredApps.keys())
        }));
    }

    // Recent Events
    if (pathname === '/api/bus/events' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            status: 'ok',
            count: eventHistory.length,
            events: eventHistory
        }));
    }

    // SSE Stream
    if (pathname === '/api/bus/stream' || pathname === '/api/bus/subscribe') {
        res.writeHead(200, {
            'Content-Type': 'text/event-stream; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        });
        res.write(`data: ${JSON.stringify({ type: 'connected', socket: SOCKET_PATH })}\n\n`);
        sseClients.add(res);

        req.on('close', () => sseClients.delete(res));
        return;
    }

    // Publish
    if (pathname === '/api/bus/publish' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const msg = JSON.parse(body || '{}');
                handleIncomingMessage(msg, (reply) => {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(reply));
                });
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'error', error: err.message }));
            }
        });
        return;
    }

    // Pipe Execution
    if (pathname === '/api/bus/pipe' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const msg = JSON.parse(body || '{}');
                executePipeline(msg, (reply) => {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(reply));
                });
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'error', error: err.message }));
            }
        });
        return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint not found' }));
});

function handleIncomingMessage(msg, replyCb) {
    if (!msg || typeof msg !== 'object') {
        return replyCb({ status: 'error', message: 'Payload must be JSON object' });
    }

    const type = msg.type || 'event';
    const source = msg.source || 'anonymous';
    const target = msg.target || '*';
    const action = msg.action || 'ping';
    const payload = msg.payload || {};
    const shmKey = msg.shm_key || null;

    if (type === 'register') {
        registeredApps.set(source, {
            name: msg.name || source,
            capabilities: msg.capabilities || [],
            lastSeen: new Date().toISOString()
        });
        return replyCb({ status: 'ok', message: `App [${source}] registered on Neural Bus` });
    }

    if (type === 'list_apps') {
        return replyCb({
            status: 'ok',
            apps: Object.fromEntries(registeredApps.entries())
        });
    }

    // Standard Event
    const evt = recordEvent({
        type: type,
        source: source,
        target: target,
        action: action,
        payload: payload,
        shm_key: shmKey
    });

    broadcastEvent(evt);
    return replyCb({ status: 'ok', event_id: evt.id, timestamp: evt.timestamp });
}

function findHeadlessBinary(appName) {
    const candidates = [
        `/opt/floworkos/apps/${appName}/bin/${appName}-cli`,
        `/opt/floworkos/apps/${appName}/bin/${appName}`,
        `/opt/floworkos/bin/${appName}-cli`,
        `/opt/floworkos/bin/${appName}`,
        `/usr/local/bin/${appName}`
    ];
    for (const p of candidates) {
        if (fs.existsSync(p)) {
            try {
                fs.accessSync(p, fs.constants.X_OK);
                return p;
            } catch (_) {}
        }
    }
    // Check system PATH
    const envPath = process.env.PATH || '';
    const dirs = envPath.split(':');
    for (const dir of dirs) {
        const full = path.join(dir, appName);
        if (fs.existsSync(full)) {
            try {
                fs.accessSync(full, fs.constants.X_OK);
                return full;
            } catch (_) {}
        }
    }
    return null;
}

function resolvePlaceholders(val, payload) {
    if (typeof val !== 'string') return val;
    let res = val;
    res = res.replace(/\{prev\}/g, payload.output || payload.result || JSON.stringify(payload));
    res = res.replace(/\{file\}/g, payload.file || payload.path || '');
    res = res.replace(/\{input\}/g, payload.input || payload.text || '');
    return res;
}

function executePipeline(pipeReq, replyCb) {
    const pipeline = pipeReq.pipeline || [];
    if (!Array.isArray(pipeline) || pipeline.length === 0) {
        return replyCb({ status: 'error', message: 'Pipeline array cannot be empty' });
    }

    const pipelineId = 'pipe_' + Date.now().toString(36);
    console.log(`[NeuralBus] Executing pipeline [${pipelineId}] with ${pipeline.length} stages...`);

    let currentPayload = pipeReq.initial_payload || {};
    const results = [];

    for (let i = 0; i < pipeline.length; i++) {
        const stage = pipeline[i];
        const appName = stage.app || stage.target;
        const action = stage.action || 'run';

        // Resolve params against currentPayload
        const resolvedParams = {};
        for (const [k, v] of Object.entries(stage.params || {})) {
            resolvedParams[k] = resolvePlaceholders(v, currentPayload);
        }

        const evt = recordEvent({
            type: 'pipeline_stage',
            pipeline_id: pipelineId,
            stage: i + 1,
            total_stages: pipeline.length,
            target: appName,
            action: action,
            payload: { ...resolvedParams, input_data: currentPayload }
        });
        broadcastEvent(evt);

        // Check for headless binary execution
        const binPath = findHeadlessBinary(appName);
        let stageOutput = null;
        let stageSuccess = true;
        let stageError = null;

        if (binPath) {
            console.log(`[NeuralBus] Stage ${i + 1}: Found executable binary ${binPath}`);
            const args = [];
            if (action && action !== 'default' && action !== 'run') {
                args.push(action);
            }
            for (const [k, v] of Object.entries(resolvedParams)) {
                if (typeof v === 'boolean') {
                    if (v) args.push(`--${k}`);
                } else if (v !== undefined && v !== null) {
                    args.push(`--${k}`, String(v));
                }
            }

            try {
                const spawnRes = spawnSync(binPath, args, {
                    input: JSON.stringify(currentPayload),
                    encoding: 'utf-8',
                    timeout: 45000,
                    env: { ...process.env, FLOWORK_PIPELINE_ID: pipelineId, FLOWORK_STAGE: String(i + 1) }
                });

                if (spawnRes.status !== 0) {
                    stageSuccess = false;
                    stageError = (spawnRes.stderr || spawnRes.stdout || `Exit code ${spawnRes.status}`).trim();
                } else {
                    const rawOut = (spawnRes.stdout || '').trim();
                    try {
                        stageOutput = JSON.parse(rawOut);
                    } catch (_) {
                        stageOutput = { output: rawOut };
                    }
                }
            } catch (err) {
                stageSuccess = false;
                stageError = err.message;
            }
        } else {
            console.log(`[NeuralBus] Stage ${i + 1}: App [${appName}] dispatched via event broadcast`);
            stageOutput = { dispatched: true, target: appName, action: action };
        }

        if (!stageSuccess) {
            const failEvt = recordEvent({
                type: 'pipeline_failed',
                pipeline_id: pipelineId,
                stage: i + 1,
                target: appName,
                error: stageError
            });
            broadcastEvent(failEvt);

            return replyCb({
                status: 'error',
                pipeline_id: pipelineId,
                failed_stage: i + 1,
                target: appName,
                error: stageError,
                results: results
            });
        }

        // Merge stageOutput into currentPayload for next stage
        currentPayload = {
            ...currentPayload,
            ...(typeof stageOutput === 'object' && stageOutput !== null ? stageOutput : { result: stageOutput }),
            last_stage: i + 1,
            last_target: appName
        };

        results.push({
            stage: i + 1,
            target: appName,
            action: action,
            event_id: evt.id,
            output: stageOutput
        });
    }

    const completeEvt = recordEvent({
        type: 'pipeline_complete',
        pipeline_id: pipelineId,
        total_stages: pipeline.length,
        final_payload: currentPayload
    });
    broadcastEvent(completeEvt);

    return replyCb({
        status: 'ok',
        pipeline_id: pipelineId,
        stages_completed: results.length,
        results: results,
        final_payload: currentPayload
    });
}

httpServer.listen(HTTP_PORT, '127.0.0.1', () => {
    console.log("=============================================================================");
    console.log("  ⚡ Flowork OS — Neural Bus Daemon Online (Semantic Agentic Pipe)");
    console.log(`  UNIX Socket:  ${SOCKET_PATH}`);
    console.log(`  HTTP Bridge:  http://127.0.0.1:${HTTP_PORT}`);
    console.log("=============================================================================");
});

// Graceful Exit
function cleanup() {
    console.log("\n[NeuralBus] Shutting down cleanly...");
    try { if (fs.existsSync(SOCKET_PATH)) fs.unlinkSync(SOCKET_PATH); } catch (_) {}
    try { if (fs.existsSync('/tmp/flowork-neural-bus.sock')) fs.unlinkSync('/tmp/flowork-neural-bus.sock'); } catch (_) {}
    process.exit(0);
}
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
