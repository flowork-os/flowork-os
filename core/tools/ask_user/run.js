#!/usr/bin/env node
const fs = require('fs');
let args = {};
try { args = JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch (_) {}
console.log(JSON.stringify({ status: "prompt_displayed", questions: args.questions || [] }, null, 2));
