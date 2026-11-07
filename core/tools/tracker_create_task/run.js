#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ status: "created", id: "task_" + Date.now(), title: args.title }, null, 2));
