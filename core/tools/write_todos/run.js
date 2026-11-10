#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ status: "todos_saved", count: (args.todos || []).length, todos: args.todos || [] }, null, 2));
