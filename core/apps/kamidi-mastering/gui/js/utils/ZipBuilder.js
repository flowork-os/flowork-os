/**
 * ZipBuilder.js - Minimal ZIP creator (STORE only, no compression)
 * Perfect for WAV files which don't benefit from compression.
 */

export class ZipBuilder {
    constructor() {
        this.files = [];
    }

    addFile(name, data) {
        if (!(data instanceof Uint8Array)) data = new Uint8Array(data);
        this.files.push({
            name: new TextEncoder().encode(name),
            data: data,
            crc: this._crc32(data)
        });
    }

    build() {
        const parts = [];
        const centralParts = [];
        let offset = 0;

        for (const file of this.files) {
            const lh = this._localHeader(file);
            parts.push(lh, file.data);
            centralParts.push(this._centralHeader(file, offset));
            offset += lh.length + file.data.length;
        }

        let cdSize = 0;
        for (const c of centralParts) cdSize += c.length;
        parts.push(...centralParts);
        parts.push(this._endRecord(this.files.length, cdSize, offset));

        let total = 0;
        for (const p of parts) total += p.length;
        const result = new Uint8Array(total);
        let pos = 0;
        for (const p of parts) { result.set(p, pos); pos += p.length; }
        return result;
    }

    _localHeader(f) {
        const h = new Uint8Array(30 + f.name.length);
        const v = new DataView(h.buffer);
        v.setUint32(0, 0x04034b50, true);
        v.setUint16(4, 20, true);
        v.setUint16(8, 0, true); // STORE
        v.setUint32(14, f.crc, true);
        v.setUint32(18, f.data.length, true);
        v.setUint32(22, f.data.length, true);
        v.setUint16(26, f.name.length, true);
        h.set(f.name, 30);
        return h;
    }

    _centralHeader(f, localOffset) {
        const h = new Uint8Array(46 + f.name.length);
        const v = new DataView(h.buffer);
        v.setUint32(0, 0x02014b50, true);
        v.setUint16(4, 20, true);
        v.setUint16(6, 20, true);
        v.setUint16(10, 0, true);
        v.setUint32(16, f.crc, true);
        v.setUint32(20, f.data.length, true);
        v.setUint32(24, f.data.length, true);
        v.setUint16(28, f.name.length, true);
        v.setUint32(42, localOffset, true);
        h.set(f.name, 46);
        return h;
    }

    _endRecord(count, cdSize, cdOffset) {
        const r = new Uint8Array(22);
        const v = new DataView(r.buffer);
        v.setUint32(0, 0x06054b50, true);
        v.setUint16(8, count, true);
        v.setUint16(10, count, true);
        v.setUint32(12, cdSize, true);
        v.setUint32(16, cdOffset, true);
        return r;
    }

    _crc32(data) {
        if (!ZipBuilder._t) {
            ZipBuilder._t = new Uint32Array(256);
            for (let i = 0; i < 256; i++) {
                let c = i;
                for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
                ZipBuilder._t[i] = c;
            }
        }
        let crc = 0xFFFFFFFF;
        for (let i = 0; i < data.length; i++) crc = ZipBuilder._t[(crc ^ data[i]) & 0xFF] ^ (crc >>> 8);
        return (crc ^ 0xFFFFFFFF) >>> 0;
    }
}
