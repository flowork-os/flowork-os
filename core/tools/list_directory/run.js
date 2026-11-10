#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const target = path.resolve(process.cwd(), args.path || '.');
if (!fs.existsSync(target)) { console.error("Error: Path not found: " + target); process.exit(1); }

try {
  const entries = fs.readdirSync(target, { withFileTypes: true });
  const items = entries.map(e => ({ name: e.name, type: e.isDirectory() ? 'directory' : (e.isSymbolicLink() ? 'symlink' : 'file') }));
  console.log(JSON.stringify({ path: target, total: items.length, items }, null, 2));
} catch (err) { console.error(err.message); process.exit(1); }
