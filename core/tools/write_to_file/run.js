#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.trim()) args = JSON.parse(raw);
} catch (e) {}

const filePath = args.file_path || args.TargetFile || args.path || '';
const content = args.content !== undefined ? args.content : (args.CodeContent !== undefined ? args.CodeContent : null);
const overwrite = args.overwrite !== undefined ? args.overwrite : (args.Overwrite !== undefined ? args.Overwrite : true);

if (!filePath) {
    console.error("Error: 'file_path' argument is required.");
    process.exit(1);
}

if (content === null) {
    console.error("Error: 'content' argument is required.");
    process.exit(1);
}

const resolvedPath = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);

if (fs.existsSync(resolvedPath) && !overwrite) {
    console.error(`Error: File '${resolvedPath}' already exists and overwrite is false.`);
    process.exit(1);
}

try {
    const parentDir = path.dirname(resolvedPath);
    if (!fs.existsSync(parentDir)) {
        fs.mkdirSync(parentDir, { recursive: true });
    }

    fs.writeFileSync(resolvedPath, content, 'utf8');

    const output = {
        status: "ok",
        file_path: resolvedPath,
        bytes_written: Buffer.byteLength(content, 'utf8'),
        message: `Successfully wrote to ${resolvedPath}`
    };

    console.log(JSON.stringify(output, null, 2));
} catch (err) {
    console.error(`Write error: ${err.message}`);
    process.exit(1);
}
