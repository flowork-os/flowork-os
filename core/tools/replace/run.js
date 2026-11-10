#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const fp = args.file_path || '';
const oldStr = args.old_string !== undefined ? args.old_string : '';
const newStr = args.new_string !== undefined ? args.new_string : '';

if (!fp || !oldStr) { console.error("Error: 'file_path' and 'old_string' required."); process.exit(1); }
const resPath = path.isAbsolute(fp) ? fp : path.resolve(process.cwd(), fp);
if (!fs.existsSync(resPath)) { console.error("Error: File not found: " + resPath); process.exit(1); }

try {
  const original = fs.readFileSync(resPath, 'utf8');
  if (!original.includes(oldStr)) { console.error("Error: Target old_string not found in file."); process.exit(1); }
  const updated = args.allow_multiple ? original.replaceAll(oldStr, newStr) : original.replace(oldStr, newStr);
  fs.writeFileSync(resPath, updated, 'utf8');
  console.log(JSON.stringify({ status: "ok", file_path: resPath, message: "Content replaced successfully." }, null, 2));
} catch (err) { console.error(err.message); process.exit(1); }
