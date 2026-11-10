const fs = require('fs');
const file = 'engine/WorkletLoader.js';
let content = fs.readFileSync(file, 'utf8');

// The line is usually like:
// if (this.bypassed) { for (let ch=0;ch<numCh;ch++) output[ch].set(input[ch]); return true; }
// or
// if(this.bypassed){for(let ch=0;ch<output.length;ch++)if(input[ch])output[ch].set(input[ch]);return true;}
// or variations.

const regex = /^[ \t]*if\s*\(\s*this\.bypassed\s*\)\s*\{\s*for\s*\(.*?\)\s*(?:if\s*\(.*?\))?output\[ch\]\.set\(input\[ch\]\);\s*return\s+true;\s*\}/gm;

const newContent = content.replace(regex, '        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).');

fs.writeFileSync(file, newContent, 'utf8');
console.log('Fixed all bypass statements in WorkletLoader.js');
