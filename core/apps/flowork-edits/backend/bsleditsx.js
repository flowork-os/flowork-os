/**
 * ⚡ FLOWORK OS — .BSLEDITSX PROJECT ENGINE
 * Reads and writes Instagram / Basel compatible project archives (.bsleditsx).
 */

const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

function createProjectArchive(projectDir, outputPath) {
    const manifest = {
        schema_version: 1,
        app_version: "454.0.0.38.112",
        project_id: "flowork-" + Date.now(),
        canvas: {
            width: 1080,
            height: 1920,
            aspect_ratio: "9:16",
            frame_rate: 30.0
        },
        assets: []
    };

    const composition = {
        format_version: "1.0",
        tracks: [
            {
                id: "track-captions",
                type: "text",
                elements: [
                    {
                        id: "caption-1",
                        text: "Flowork Edits on Linux",
                        start_time_ms: 0,
                        duration_ms: 3000
                    }
                ]
            },
            {
                id: "track-main-video",
                type: "video",
                elements: []
            },
            {
                id: "track-audio",
                type: "audio",
                elements: []
            }
        ]
    };

    const tmpDir = path.join("/tmp", "bsleditsx_" + Date.now());
    fs.mkdirSync(tmpDir, { recursive: true });

    fs.writeFileSync(path.join(tmpDir, "manifest.json"), JSON.stringify(manifest, null, 2));
    fs.writeFileSync(path.join(tmpDir, "composition.json"), JSON.stringify(composition, null, 2));

    // Pack into ZIP (.bsleditsx)
    execFileSync("7z", ["a", "-tzip", outputPath, path.join(tmpDir, "*")], { stdio: "ignore" });
    fs.rmSync(tmpDir, { recursive: true, force: true });
    return outputPath;
}

if (require.main === module) {
    const sampleOutput = "/tmp/Sample_Project.bsleditsx";
    createProjectArchive(null, sampleOutput);
    console.log("Sample .bsleditsx generated:", sampleOutput);
}

module.exports = { createProjectArchive };
