#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ status: "skill_activated", skill: args.name || "unknown" }, null, 2));
