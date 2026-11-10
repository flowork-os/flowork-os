#!/usr/bin/env node

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

function resolveNpxPath() {
    const homeDir = process.env.HOME || process.env.HOME || "/tmp";
    const nvmNpxPath = path.join(homeDir, ".nvm/versions/node/v22.23.4/bin/npx");
    if (fs.existsSync(nvmNpxPath)) {
        return nvmNpxPath;
    }
    return "npx";
}

function parseInput() {
    const rawInput = process.argv[2];
    if (!rawInput) {
        return { command: "capabilities" };
    }
    try {
        return JSON.parse(rawInput);
    } catch {
        return { command: rawInput };
    }
}

async function main() {
    const input = parseInput();
    const command = input.command || "capabilities";
    const target = input.target;
    const additionalArgs = Array.isArray(input.args) ? input.args : [];

    const npxBin = resolveNpxPath();
    const cliArgs = ["-y", "rea-agents@6.8.0", command];

    if (target) {
        cliArgs.push(target);
    }
    cliArgs.push(...additionalArgs);

    if (!cliArgs.includes("--format")) {
        cliArgs.push("--format", "json");
    }

    const homeDir = process.env.HOME || process.env.HOME || "/tmp";
    const nvmBinDir = path.join(homeDir, ".nvm/versions/node/v22.23.4/bin");
    const childEnv = Object.assign({}, process.env, {
        PATH: nvmBinDir + ":" + (process.env.PATH || "")
    });

    const proc = spawn(npxBin, cliArgs, {
        env: childEnv,
        stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", chunk => {
        stdout += chunk.toString();
    });

    proc.stderr.on("data", chunk => {
        stderr += chunk.toString();
    });

    proc.on("close", code => {
        if (code === 0 || stdout.trim().length > 0) {
            process.stdout.write(stdout.trim() + "\n");
            process.exit(0);
        } else {
            process.stderr.write("[REA ERROR]: Command " + command + " failed with code " + code + "\n" + stderr + "\n");
            process.exit(code || 1);
        }
    });

    proc.on("error", err => {
        process.stderr.write("[REA EXECUTION ERROR]: " + err.message + "\n");
        process.exit(1);
    });
}

main().catch(err => {
    process.stderr.write("[FATAL]: " + err.message + "\n");
    process.exit(1);
});
