#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.trim()) args = JSON.parse(raw);
} catch (e) {}

const filePath = args.file_path || args.TargetFile || args.path || '';
const target = args.target !== undefined ? args.target : (args.TargetContent !== undefined ? args.TargetContent : '');
const replacement = args.replacement !== undefined ? args.replacement : (args.ReplacementContent !== undefined ? args.ReplacementContent : '');

if (!filePath) {
    console.error("Error: 'file_path' argument is required.");
    process.exit(1);
}

if (!target) {
    console.error("Error: 'target' argument is required.");
    process.exit(1);
}

const resolvedPath = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);
if (!fs.existsSync(resolvedPath)) {
    console.error(`Error: File '${resolvedPath}' does not exist.`);
    process.exit(1);
}

try {
    const original = fs.readFileSync(resolvedPath, 'utf8');
    if (!original.includes(target)) {
        console.error(`Error: Target string not found in '${resolvedPath}'`);
        process.exit(1);
    }

    const updated = original.replace(target, replacement);
    fs.writeFileSync(resolvedPath, updated, 'utf8');

    const output = {
        status: "ok",
        file_path: resolvedPath,
        message: "Successfully replaced content."
    };

    console.log(JSON.stringify(output, null, 2));
} catch (err) {
    console.error(`Replace error: ${err.message}`);
    process.exit(1);
}
