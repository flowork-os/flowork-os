#!/usr/bin/env node
// =============================================================================
// 🚀 Flowork Sovereign OS — External Application Launcher & Window Controller
// Invokes and orchestrates external Linux applications (Chrome, VS Code, etc.)
// =============================================================================

import http from 'http';

const SYSD_URL = process.env.FLOWORK_SYSD_URL || 'http://127.0.0.1:18090';

function apiCall(endpoint, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint, SYSD_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method,
      headers: { 'Content-Type': 'application/json' }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (_) {
          resolve({ raw: data });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0] || '--list';

  if (cmd === '--list' || cmd === '-l') {
    const data = await apiCall('/api/system/apps');
    if (data.apps) {
      console.log(`📦 Installed Applications (${data.total}):`);
      data.apps.slice(0, 25).forEach(app => {
        console.log(`  - [${app.id}] ${app.name} -> ${app.exec}`);
      });
      if (data.total > 25) console.log(`  ... and ${data.total - 25} more.`);
    }
  } else if (cmd === '--launch' || cmd === '-x') {
    const target = args[1];
    if (!target) {
      console.error('Error: specify app name or command to launch');
      process.exit(1);
    }
    const res = await apiCall('/api/system/apps/launch', 'POST', { exec: target });
    console.log(`🚀 Launch result:`, res);
  } else if (cmd === '--windows' || cmd === '-w') {
    const data = await apiCall('/api/system/windows');
    console.log(`🪟 Active Desktop Windows:`, data.windows);
  } else {
    console.log('Usage: launcher.mjs [--list | --launch <cmd> | --windows]');
  }
}

main().catch(err => {
  console.error('Launcher error:', err.message);
  process.exit(1);
});
