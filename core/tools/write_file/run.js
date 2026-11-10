#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const fp = args.file_path || '';
const content = args.content !== undefined ? args.content : null;
if (!fp || content === null) { console.error("Error: 'file_path' and 'content' required."); process.exit(1); }

const resPath = path.isAbsolute(fp) ? fp : path.resolve(process.cwd(), fp);
try {
  const dir = path.dirname(resPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(resPath, content, 'utf8');
  console.log(JSON.stringify({ status: "ok", file_path: resPath, bytes_written: Buffer.byteLength(content, 'utf8') }, null, 2));
} catch (err) { console.error(err.message); process.exit(1); }
