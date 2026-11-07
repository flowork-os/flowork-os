#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ status: "subagent_spawned", agent: args.agent_name, task_id: "agent_" + Date.now() }, null, 2));
