const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { execFile } = require("node:child_process");

const PORT = 3456;
const ROOT_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIR = path.join(ROOT_DIR, "frontend");
const ASSETS_DIR = path.join(ROOT_DIR, "assets");
const PROJECTS_DIR = path.join(ROOT_DIR, "projects");

if (!fs.existsSync(PROJECTS_DIR)) {
    fs.mkdirSync(PROJECTS_DIR, { recursive: true });
}

function getContentType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    switch (ext) {
        case ".html": return "text/html; charset=utf-8";
        case ".css": return "text/css; charset=utf-8";
        case ".js": return "application/javascript; charset=utf-8";
        case ".json": return "application/json";
        case ".png": return "image/png";
        case ".jpg": case ".jpeg": return "image/jpeg";
        case ".svg": return "image/svg+xml";
        case ".mp4": return "video/mp4";
        case ".mov": return "video/quicktime";
        case ".mp3": return "audio/mpeg";
        default: return "application/octet-stream";
    }
}

function parseJsonBody(req) {
    return new Promise((resolve, reject) => {
        let body = "";
        req.on("data", chunk => { body += chunk; });
        req.on("end", () => {
            try {
                resolve(body ? JSON.parse(body) : {});
            } catch (err) {
                reject(err);
            }
        });
        req.on("error", reject);
    });
}

function serveStreamableFile(req, res, fullPath) {
    const stat = fs.statSync(fullPath);
    const fileSize = stat.size;
    const range = req.headers.range;
    const contentType = getContentType(fullPath);

    if (range) {
        const parts = range.replace(/bytes=/, "").split("-");
        const start = parseInt(parts[0], 10);
        const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
        const chunksize = (end - start) + 1;
        const file = fs.createReadStream(fullPath, { start, end });
        const head = {
            "Content-Range": `bytes ${start}-${end}/${fileSize}`,
            "Accept-Ranges": "bytes",
            "Content-Length": chunksize,
            "Content-Type": contentType,
            "Access-Control-Allow-Origin": "*"
        };
        res.writeHead(206, head);
        file.pipe(res);
    } else {
        const head = {
            "Content-Length": fileSize,
            "Content-Type": contentType,
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*"
        };
        res.writeHead(200, head);
        fs.createReadStream(fullPath).pipe(res);
    }
}

const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://localhost:" + PORT);
    const pathname = url.pathname;

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Range");

    if (req.method === "OPTIONS") {
        res.writeHead(204);
        return res.end();
    }

    if (pathname === "/api/info") {
        res.writeHead(200, { "Content-Type": "application/json" });
        return res.end(JSON.stringify({
            app: "Flowork Edits",
            version: "454.0.0-sovereign",
            engine: "Flowork Media Composition Engine (MCE-Linux)",
            platform: "Flowork OS",
            sampleVideo: "/assets/sample_reel.mp4",
            handoff: "Ready (_baseltransfer._tcp)"
        }));
    }

    if (pathname === "/api/project/export" && req.method === "POST") {
        try {
            const body = await parseJsonBody(req);
            const { projectTitle, aspectRatio, outputPath } = body;
            const dest = outputPath || path.join(process.env.HOME || "/tmp", "Videos", (projectTitle || "Untitled_Reel") + ".mp4");

            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                status: "rendering_started",
                destPath: dest,
                aspectRatio: aspectRatio || "9:16"
            }));
        } catch (e) {
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: e.message }));
        }
        return;
    }

    // Static Assets from assets/ (Supports Range request streaming)
    if (pathname.startsWith("/assets/")) {
        const rel = pathname.replace("/assets/", "");
        const fullPath = path.join(ASSETS_DIR, rel);
        if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
            return serveStreamableFile(req, res, fullPath);
        }
    }

    // Static Frontend files
    let staticPath = path.join(FRONTEND_DIR, pathname === "/" ? "index.html" : pathname.slice(1));
    if (fs.existsSync(staticPath) && fs.statSync(staticPath).isFile()) {
        res.writeHead(200, { "Content-Type": getContentType(staticPath) });
        return fs.createReadStream(staticPath).pipe(res);
    }

    const indexPath = path.join(FRONTEND_DIR, "index.html");
    if (fs.existsSync(indexPath)) {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        return fs.createReadStream(indexPath).pipe(res);
    }

    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found");
});

server.listen(PORT, "127.0.0.1", () => {
    console.log("⚡ Flowork Edits Engine with Video Range Streaming listening on port " + PORT);
});
