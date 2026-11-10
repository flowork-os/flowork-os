#!/usr/bin/env node
/**
 * ⚡ FLOWORK OS — DYNAMIC SOVEREIGN TOOL DISCOVERY RUNNER
 * Decoupled modular discovery engine scanning /opt/floworkos/tools/
 * Emits JSON array of function declarations for MrFlow CLI (Flowork OS).
 * 
 * Dynamic Rules:
 *   - "always" vs "conditional" activation
 *   - Keyword triggers & Exclude keyword negation (strict veto)
 *   - Environmental behavior sniffing (file extensions, active URLs/domains)
 *   - Injects Flowork Tool Intercept Gate parameters: reason, keywords, goal.
 */

const fs = require('fs');
const path = require('path');
const sniffer = require('./context_sniffer.js');

const TOOLS_DIR = path.resolve(__dirname);

function discoverTools() {
    const discovered = [];
    const context = sniffer.sniffContext();

    try {
        const entries = fs.readdirSync(TOOLS_DIR, { withFileTypes: true });

        for (const entry of entries) {
            if (!entry.isDirectory()) continue;

            const toolDir = path.join(TOOLS_DIR, entry.name);
            const manifestPath = path.join(toolDir, 'manifest.json');

            if (fs.existsSync(manifestPath)) {
                try {
                    const raw = fs.readFileSync(manifestPath, 'utf8');
                    const manifest = JSON.parse(raw);

                    if (manifest.name && manifest.description) {
                        // Evaluate Dynamic Tool Activation (Always vs Conditional + Exclude + Behaviors)
                        const active = sniffer.isToolActive(manifest.name, manifest, context);
                        if (!active) {
                            // Conditional tool not triggered -> Drop to conserve tokens!
                            continue;
                        }

                        const schema = manifest.parametersJsonSchema || {
                            type: "object",
                            properties: {},
                            required: []
                        };
                        const props = schema.properties || {};
                        const req = Array.isArray(schema.required) ? [...schema.required] : [];

                        schema.properties = {
                            ...props,
                            reason: {
                                type: "string",
                                maxLength: 160,
                                description: "[MANDATORY AUDIT REASON] Explain why this tool is being used for this action. Required for auditability and safety. Must be in strict English, maximum 160 characters."
                            },
                            keywords: {
                                type: "array",
                                items: { type: "string" },
                                minItems: 5,
                                description: "[MANDATORY DYNAMIC ROUTING KEYWORDS] Provide at least 5 English semantic keywords describing this action. Required for the Dynamic Tool Router to match relevant tools (max 5) and trigger modular prompts without token bloat. Minimum 5 keywords."
                            },
                            goal: {
                                type: "string",
                                maxLength: 160,
                                description: "[INTERCEPT GATE OBJECTIVE] High-level task objective required on the initial tool call of an operation. Explains the overarching operational mission in concise English (maximum 160 characters)."
                            }
                        };
                        if (!req.includes("reason")) req.push("reason");
                        if (!req.includes("keywords")) req.push("keywords");
                        schema.required = req;

                        discovered.push({
                            name: manifest.name,
                            description: manifest.description,
                            parametersJsonSchema: schema,
                            activation: manifest.activation || "always"
                        });
                    }
                } catch (err) {
                    // Skip malformed manifests gracefully
                }
            }
        }
    } catch (err) {
        // Fallback to empty if directory cannot be read
    }

    console.log(JSON.stringify(discovered, null, 2));
}

discoverTools();
