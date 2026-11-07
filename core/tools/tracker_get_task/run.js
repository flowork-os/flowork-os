#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ task_id: args.task_id, status: "active", title: "Task Details" }, null, 2));
