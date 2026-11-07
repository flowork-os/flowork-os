#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN TOOL RUNNER: agent_browser
 * Bridges Flowork OS agents directly to native Rust agent-browser daemon over CDP.
 */

const { execFileSync } = require('child_process');

let params = {};
if (process.argv.length > 2) {
  try {
    params = JSON.parse(process.argv[2]);
  } catch (e) {
    params.action = process.argv[2];
    if (process.argv[3]) params.url = process.argv[3];
    if (process.argv[4]) params.ref = process.argv[4];
  }
} else if (process.env.ACTION) {
  params.action = process.env.ACTION;
  params.url = process.env.URL;
  params.ref = process.env.REF;
  params.text = process.env.TEXT;
  params.key = process.env.KEY;
}

if (!params.action) {
  console.error("FLOWORK TOOL ERROR: 'action' parameter is required.");
  process.exit(1);
}

const cliArgs = [];
if (params.session) {
  cliArgs.push('--session', params.session);
}

switch (params.action) {
  case 'open':
    if (!params.url) {
      console.error("FLOWORK TOOL ERROR: 'url' parameter is required for 'open'.");
      process.exit(1);
    }
    cliArgs.push('open', params.url);
    break;
  case 'snapshot':
    cliArgs.push('snapshot');
    if (params.interactive_only !== false) cliArgs.push('-i');
    break;
  case 'click':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' parameter is required for 'click'.");
      process.exit(1);
    }
    cliArgs.push('click', params.ref);
    break;
  case 'dblclick':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' parameter is required for 'dblclick'.");
      process.exit(1);
    }
    cliArgs.push('dblclick', params.ref);
    break;
  case 'type':
    if (!params.ref || params.text === undefined) {
      console.error("FLOWORK TOOL ERROR: 'ref' and 'text' are required for 'type'.");
      process.exit(1);
    }
    cliArgs.push('type', params.ref, String(params.text));
    break;
  case 'fill':
    if (!params.ref || params.text === undefined) {
      console.error("FLOWORK TOOL ERROR: 'ref' and 'text' are required for 'fill'.");
      process.exit(1);
    }
    cliArgs.push('fill', params.ref, String(params.text));
    break;
  case 'press':
    if (!params.key) {
      console.error("FLOWORK TOOL ERROR: 'key' parameter is required for 'press'.");
      process.exit(1);
    }
    cliArgs.push('press', params.key);
    break;
  case 'hover':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' is required for 'hover'.");
      process.exit(1);
    }
    cliArgs.push('hover', params.ref);
    break;
  case 'focus':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' is required for 'focus'.");
      process.exit(1);
    }
    cliArgs.push('focus', params.ref);
    break;
  case 'check':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' is required for 'check'.");
      process.exit(1);
    }
    cliArgs.push('check', params.ref);
    break;
  case 'uncheck':
    if (!params.ref) {
      console.error("FLOWORK TOOL ERROR: 'ref' is required for 'uncheck'.");
      process.exit(1);
    }
    cliArgs.push('uncheck', params.ref);
    break;
  case 'get':
    cliArgs.push('get', params.property || 'url');
    break;
  case 'eval':
    if (!params.js_code) {
      console.error("FLOWORK TOOL ERROR: 'js_code' is required for 'eval'.");
      process.exit(1);
    }
    cliArgs.push('eval', params.js_code);
    break;
  case 'screenshot':
    cliArgs.push('screenshot');
    if (params.text) cliArgs.push(params.text);
    break;
  case 'connect':
    cliArgs.push('connect', params.url || '9222');
    break;
  case 'close':
    cliArgs.push('close');
    break;
  default:
    console.error(`FLOWORK TOOL ERROR: Unknown action '${params.action}'.`);
    process.exit(1);
}

try {
  const binPath = '/usr/bin/agent-browser';
  const stdout = execFileSync(binPath, cliArgs, {
    env: process.env,
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024
  });
  console.log(stdout.trim());
  process.exit(0);
} catch (err) {
  if (err.stdout) console.log(err.stdout.trim());
  if (err.stderr) console.error(err.stderr.trim());
  process.exit(err.status || 1);
}
