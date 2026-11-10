#!/usr/bin/env node
const fs = require('fs');
const { spawnSync } = require('child_process');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const pattern = args.pattern || '';
const searchPath = args.path || '.';
if (!pattern) { console.error("Error: 'pattern' required."); process.exit(1); }

const grepArgs = ['-rnI', '--max-count=50', pattern, searchPath];
if (args.include_pattern) grepArgs.splice(1, 0, '--include=' + args.include_pattern);

const res = spawnSync('grep', grepArgs, { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
console.log(JSON.stringify({ matches: (res.stdout || '').trim().split('\n').filter(Boolean) }, null, 2));
