#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const fp = args.file_path || '';
if (!fp) { console.error("Error: 'file_path' required."); process.exit(1); }
const resPath = path.isAbsolute(fp) ? fp : path.resolve(process.cwd(), fp);
if (!fs.existsSync(resPath)) { console.error("Error: File not found: " + resPath); process.exit(1); }

try {
  const lines = fs.readFileSync(resPath, 'utf8').split('\n');
  const total = lines.length;
  const start = Math.max(1, parseInt(args.start_line || 1, 10));
  const end = Math.min(total, parseInt(args.end_line || total, 10));
  const sliced = [];
  for (let i = start - 1; i < end; i++) sliced.push((i + 1) + ': ' + lines[i]);
  console.log(JSON.stringify({
    file_path: resPath,
    total_lines: total,
    showing_lines: start + '-' + end,
    content: sliced.join('\n')
  }, null, 2));
} catch (err) { console.error(err.message); process.exit(1); }
