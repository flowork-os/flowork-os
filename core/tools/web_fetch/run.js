#!/usr/bin/env node
const fs = require('fs');
const { spawnSync } = require('child_process');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const url = args.url || '';
if (!url) { console.error("Error: 'url' required."); process.exit(1); }

const res = spawnSync('curl', ['-sL', '--max-time', '15', url], { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
console.log(JSON.stringify({ url, status: res.status === 0 ? "ok" : "error", content: (res.stdout || '').substring(0, 50000) }, null, 2));
