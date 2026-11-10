#!/usr/bin/env node
const fs = require('fs');
const { spawnSync, spawn } = require('child_process');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const cmd = args.command || '';
if (!cmd) { console.error("Error: 'command' required."); process.exit(1); }

if (args.is_background) {
  const child = spawn('/bin/bash', ['-c', cmd], { detached: true, stdio: 'ignore' });
  child.unref();
  console.log(JSON.stringify({ status: "running_background", pid: child.pid }));
  process.exit(0);
}

const timeoutMs = args.timeout_ms ? parseInt(args.timeout_ms) : 180000;
const res = spawnSync('/bin/bash', ['-c', cmd], {
  encoding: 'utf8',
  maxBuffer: 50 * 1024 * 1024,
  timeout: timeoutMs,
  env: { ...process.env, PAGER: 'cat' }
});
console.log(JSON.stringify({
  stdout: res.stdout || '',
  stderr: res.stderr || '',
  exit_code: res.status ?? (res.error ? 1 : 0)
}, null, 2));
