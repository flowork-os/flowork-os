#!/usr/bin/env node
const fs = require('fs');
const { spawnSync } = require('child_process');

let args = {};
try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.trim()) args = JSON.parse(raw);
} catch (e) {}

const command = args.command || args.CommandLine || '';
const cwd = args.cwd || args.Cwd || process.cwd();

if (!command) {
    console.error("Error: 'command' argument is required.");
    process.exit(1);
}

const res = spawnSync('/bin/bash', ['-c', command], {
    cwd: fs.existsSync(cwd) ? cwd : process.cwd(),
    encoding: 'utf8',
    maxBuffer: 50 * 1024 * 1024,
    env: { ...process.env, PAGER: 'cat' }
});

const output = {
    stdout: res.stdout || '',
    stderr: res.stderr || '',
    exit_code: res.status ?? (res.error ? 1 : 0)
};

console.log(JSON.stringify(output, null, 2));
