#!/usr/bin/env node
const fs = require('fs');
const { spawnSync } = require('child_process');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const pattern = args.pattern || '*';
const root = args.path || '.';

const res = spawnSync('find', [root, '-name', pattern, '-not', '-path', '*/.*'], { encoding: 'utf8' });
console.log(JSON.stringify({ files: (res.stdout || '').trim().split('\n').filter(Boolean) }, null, 2));
