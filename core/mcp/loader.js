#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — SOVEREIGN MCP AUTO-DISCOVERY LOADER
 * Scans /opt/floworkos/mcp/ for modular MCP server configurations.
 * Emits JSON object of mcpServers for MrFlow settings (Flowork OS).
 */

const fs = require('fs');
const path = require('path');

const MCP_DIR = path.resolve(__dirname);

function discoverMcpServers() {
    const servers = {};

    try {
        const entries = fs.readdirSync(MCP_DIR, { withFileTypes: true });

        for (const entry of entries) {
            if (!entry.isDirectory()) continue;

            const configPath = path.join(MCP_DIR, entry.name, 'config.json');
            if (fs.existsSync(configPath)) {
                try {
                    const raw = fs.readFileSync(configPath, 'utf8');
                    const config = JSON.parse(raw);
                    const serverName = config.name || entry.name;

                    servers[serverName] = {
                        command: config.command,
                        args: config.args || [],
                        env: config.env || {},
                        description: config.description || ''
                    };
                } catch (err) {
                    // Skip malformed configs
                }
            }
        }
    } catch (_) {}

    return servers;
}

if (require.main === module) {
    const servers = discoverMcpServers();
    console.log(JSON.stringify(servers, null, 2));
}

module.exports = { discoverMcpServers };
