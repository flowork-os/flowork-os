#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const paths = args.paths || [];
const results = {};
for (const p of paths) {
  const resPath = path.isAbsolute(p) ? p : path.resolve(process.cwd(), p);
  try {
    if (fs.existsSync(resPath)) results[p] = fs.readFileSync(resPath, 'utf8');
    else results[p] = "[Error: Not found]";
  } catch (err) { results[p] = "[Error: " + err.message + "]"; }
}
console.log(JSON.stringify({ files: results }, null, 2));
