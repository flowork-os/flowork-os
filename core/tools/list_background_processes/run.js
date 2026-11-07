#!/usr/bin/env node
const { spawnSync } = require('child_process');
const res = spawnSync('ps', ['-eo', 'pid,comm,args'], { encoding: 'utf8' });
console.log(JSON.stringify({ status: "ok", active_processes: (res.stdout || '').split('\n').slice(0, 20) }, null, 2));
