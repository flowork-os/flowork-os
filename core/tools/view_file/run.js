#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let args = {};
try {
    const raw = fs.readFileSync(0, 'utf8');
    if (raw && raw.trim()) args = JSON.parse(raw);
} catch (e) {}

const filePath = args.file_path || args.AbsolutePath || args.path || '';
if (!filePath) {
    console.error("Error: 'file_path' argument is required.");
    process.exit(1);
}

const resolvedPath = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);
if (!fs.existsSync(resolvedPath)) {
    console.error(`Error: File not found at '${resolvedPath}'`);
    process.exit(1);
}

try {
    const content = fs.readFileSync(resolvedPath, 'utf8');
    const lines = content.split('\n');
    const totalLines = lines.length;

    const startLine = Math.max(1, parseInt(args.start_line || args.StartLine || 1, 10));
    const endLine = Math.min(totalLines, parseInt(args.end_line || args.EndLine || totalLines, 10));

    const slicedLines = [];
    for (let i = startLine - 1; i < endLine; i++) {
        slicedLines.push(`${i + 1}: ${lines[i]}`);
    }

    const output = {
        file_path: resolvedPath,
        total_lines: totalLines,
        showing_lines: `${startLine}-${endLine}`,
        content: slicedLines.join('\n')
    };

    console.log(JSON.stringify(output, null, 2));
} catch (err) {
    console.error(`Read error: ${err.message}`);
    process.exit(1);
}
