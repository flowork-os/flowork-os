#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN TOOL RUNNER: agent_desktop
 * Bridges Flowork OS agents directly to Linux OS Accessibility Tree (AT-SPI2)
 */

const { execFileSync } = require('child_process');
const fs = require('fs');

// 1. Environment & Session D-Bus Resolution
const uid = process.getuid();
const busCandidates = [
  process.env.DBUS_SESSION_BUS_ADDRESS,
  `unix:path=/run/user/${uid}/bus`,
  'unix:path=/run/user/1001/bus',
  'unix:path=/run/user/1000/bus'
].filter(Boolean);

for (const candidate of busCandidates) {
  const socketPath = candidate.replace('unix:path=', '');
  if (fs.existsSync(socketPath)) {
    process.env.DBUS_SESSION_BUS_ADDRESS = candidate;
    break;
  }
}

if (!process.env.DISPLAY) {
  process.env.DISPLAY = ':0';
}

// 2. Parse arguments from CLI args or STDIN
let params = {};
if (process.argv.length > 2) {
  try {
    params = JSON.parse(process.argv[2]);
  } catch (e) {
    params.action = process.argv[2];
    if (process.argv[3]) params.ref = process.argv[3];
    if (process.argv[4]) params.text = process.argv[4];
  }
} else if (process.env.ACTION) {
  params.action = process.env.ACTION;
  params.app = process.env.APP;
  params.ref = process.env.REF;
  params.text = process.env.TEXT;
  params.key = process.env.KEY;
}

if (!params.action) {
  console.error("FLOWORK TOOL ERROR: 'action' parameter is required.");
  process.exit(1);
}

// 3. Build agent-desktop CLI arguments
const cliArgs = [];
switch (params.action) {
  case 'status':
    cliArgs.push('status');
    break;
  case 'list_windows':
    cliArgs.push('list-windows');
    break;
  case 'snapshot':
    cliArgs.push('snapshot');
    if (params.app) cliArgs.push('--app', params.app);
    if (params.window_id) cliArgs.push('--window-id', params.window_id);
    if (params.interactive_only !== false) cliArgs.push('-i');
    break;
  case 'click':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' parameter is required for 'click' action.");
      process.exit(1);
    }
    cliArgs.push('click', params.ref);
    break;
  case 'type':
    if (!params.ref || params.text === undefined) {
      console.error("FLOWORK TOOL ERROR: 'ref' and 'text' parameters are required for 'type' action.");
      process.exit(1);
    }
    cliArgs.push('type', params.ref, String(params.text));
    break;
  case 'press_key':
    if (!params.key) {
      console.error("FLOWORK TOOL ERROR: 'key' parameter is required for 'press_key' action.");
      process.exit(1);
    }
    cliArgs.push('press-key', params.key);
    break;
  case 'hover':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' parameter is required for 'hover' action.");
      process.exit(1);
    }
    cliArgs.push('hover', params.ref);
    break;
  default:
    console.error(`FLOWORK TOOL ERROR: Unknown action '${params.action}'.`);
    process.exit(1);
}

// 4. Execute binary
try {
  const binPath = '/usr/bin/agent-desktop';
  const stdout = execFileSync(binPath, cliArgs, {
    env: process.env,
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024
  });
  console.log(stdout.trim());
  process.exit(0);
} catch (err) {
  if (err.stdout) {
    console.log(err.stdout.trim());
  }
  if (err.stderr) {
    console.error(err.stderr.trim());
  } else {
    console.error(`FLOWORK TOOL EXECUTION ERROR: ${err.message}`);
  }
  process.exit(err.status || 1);
}
