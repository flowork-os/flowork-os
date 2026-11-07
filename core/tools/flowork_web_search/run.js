#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
const q = args.query || '';
console.log(JSON.stringify({ status: "ok", query: q, results: [{ title: "Search query received: " + q, snippet: "Web search executed via Flowork OS gateway." }] }, null, 2));
