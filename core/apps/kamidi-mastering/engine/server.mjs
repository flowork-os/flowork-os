/**
 * 👑 FLOWORK OS — KAMIDI MASTERING CONSOLE PRO NATIVE ENGINE SERVER
 * High-performance Node.js DSP & IPC bridge.
 * Features:
 * - Native GTK / Zenity file dialog integration
 * - Video-to-audio extraction via ffmpeg with instant PCM WAV conversion
 * - High-speed binary streaming with HTTP Range (206) support
 * - Zero CORS restrictions, 100% local IPC
 */

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execFile, spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_DIR = path.dirname(__dirname);
const GUI_DIR = path.join(APP_DIR, 'gui');
const PORT = parseInt(process.env.FLOWORK_APP_PORT || '17860', 10);

const HOME = process.env.HOME || '/home/awenkaudico';
const PRESET_DIR = path.join(HOME, '.config', 'flowork', 'kamidi_presets');
const TEMP_AUDIO_DIR = '/tmp/flowork_audio';

// Ensure directories exist
for (const dir of [PRESET_DIR, TEMP_AUDIO_DIR]) {
  try {
    fs.mkdirSync(dir, { recursive: true });
  } catch (_) {}
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
  '.ogg': 'audio/ogg',
  '.flac': 'audio/flac',
  '.m4a': 'audio/mp4',
  '.aac': 'audio/aac',
  '.wasm': 'application/wasm',
};

const VIDEO_EXTS = new Set(['.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v']);

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE',
    'Access-Control-Allow-Headers': 'Content-Type, Range, Authorization',
  });
  res.end(JSON.stringify(data));
}

function sendCors(res) {
  res.writeHead(204, {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE',
    'Access-Control-Allow-Headers': 'Content-Type, Range, Authorization',
  });
  res.end();
}

/**
 * Extracts audio from a video file into PCM 16-bit stereo WAV.
 */
function extractAudioFromVideo(videoPath) {
  return new Promise((resolve, reject) => {
    const stat = fs.statSync(videoPath);
    const hash = Buffer.from(videoPath).toString('hex').slice(0, 16) + `_${stat.size}`;
    const outWav = path.join(TEMP_AUDIO_DIR, `extracted_${hash}.wav`);

    if (fs.existsSync(outWav)) {
      return resolve(outWav);
    }

    // Run ffmpeg extraction
    const args = [
      '-y',
      '-i', videoPath,
      '-vn',
      '-acodec', 'pcm_s16le',
      '-ar', '44100',
      '-ac', '2',
      outWav
    ];

    execFile('/usr/bin/ffmpeg', args, (err) => {
      if (err) {
        return reject(err);
      }
      resolve(outWav);
    });
  });
}

/**
 * Native GTK Open File Dialog via Zenity.
 */
function openFileDialog(options = {}) {
  return new Promise((resolve) => {
    const title = options.title || 'Select Audio or Video Track';
    const multiple = options.multiple !== false;

    const args = [
      '--file-selection',
      `--title=${title}`,
      '--file-filter=Audio & Video Files | *.wav *.mp3 *.flac *.ogg *.m4a *.aac *.aiff *.wma *.mp4 *.mkv *.webm *.mov *.avi',
      '--file-filter=All Files | *'
    ];

    if (multiple) {
      args.push('--multiple', '--separator=\\n');
    }

    execFile('/usr/bin/zenity', args, (err, stdout) => {
      if (err || !stdout.trim()) {
        return resolve(null);
      }
      const rawLines = stdout.trim().split('\n').filter(Boolean);
      const results = rawLines.map(p => ({
        path: p,
        name: path.basename(p)
      }));
      resolve(multiple ? results : (results[0] || null));
    });
  });
}

/**
 * Native GTK Save File Dialog via Zenity.
 */
function saveFileDialog(options = {}) {
  return new Promise((resolve) => {
    const title = options.title || 'Export Mastered WAV';
    const defaultPath = options.defaultPath || 'Master_Track.wav';

    const args = [
      '--file-selection',
      '--save',
      '--confirm-overwrite',
      `--title=${title}`,
      `--filename=${defaultPath}`,
      '--file-filter=WAV Audio | *.wav',
      '--file-filter=All Files | *'
    ];

    execFile('/usr/bin/zenity', args, (err, stdout) => {
      if (err || !stdout.trim()) {
        return resolve(null);
      }
      let selected = stdout.trim();
      if (!selected.toLowerCase().endsWith('.wav')) {
        selected += '.wav';
      }
      resolve({ path: selected, name: path.basename(selected) });
    });
  });
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    return sendCors(res);
  }

  const parsedUrl = new URL(req.url, `http://127.0.0.1:${PORT}`);
  const pathname = parsedUrl.pathname;

  // --------------------------------------------------------------------------
  // API ROUTING: Native Flowork Bridge Endpoints
  // --------------------------------------------------------------------------
  if (pathname === '/api/dialog/open') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const opts = body ? JSON.parse(body) : {};
        const result = await openFileDialog(opts);
        sendJson(res, 200, result);
      } catch (err) {
        sendJson(res, 500, { error: err.message });
      }
    });
    return;
  }

  if (pathname === '/api/dialog/save') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const opts = body ? JSON.parse(body) : {};
        const result = await saveFileDialog(opts);
        sendJson(res, 200, result);
      } catch (err) {
        sendJson(res, 500, { error: err.message });
      }
    });
    return;
  }

  if (pathname === '/api/fs/read') {
    let targetPath = parsedUrl.searchParams.get('path');
    if (!targetPath) {
      return sendJson(res, 400, { error: 'Missing path parameter' });
    }

    try {
      if (!fs.existsSync(targetPath)) {
        return sendJson(res, 404, { error: `File not found: ${targetPath}` });
      }

      const ext = path.extname(targetPath).toLowerCase();
      // If user selected a video file, auto-extract audio via ffmpeg
      if (VIDEO_EXTS.has(ext)) {
        targetPath = await extractAudioFromVideo(targetPath);
      }

      const stat = fs.statSync(targetPath);
      const mime = MIME_TYPES[path.extname(targetPath).toLowerCase()] || 'application/octet-stream';

      // Support HTTP 206 Partial Content (Range requests) for audio seeking
      const range = req.headers.range;
      if (range) {
        const parts = range.replace(/bytes=/, '').split('-');
        const start = parseInt(parts[0], 10);
        const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1;
        const chunksize = (end - start) + 1;
        const fileStream = fs.createReadStream(targetPath, { start, end });

        res.writeHead(206, {
          'Content-Range': `bytes ${start}-${end}/${stat.size}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': chunksize,
          'Content-Type': mime,
          'Access-Control-Allow-Origin': '*',
        });
        fileStream.pipe(res);
      } else {
        res.writeHead(200, {
          'Content-Length': stat.size,
          'Content-Type': mime,
          'Accept-Ranges': 'bytes',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'no-cache',
        });
        fs.createReadStream(targetPath).pipe(res);
      }
    } catch (err) {
      sendJson(res, 500, { error: err.message });
    }
    return;
  }

  if (pathname === '/api/fs/write') {
    const targetPath = parsedUrl.searchParams.get('path');
    if (!targetPath) {
      return sendJson(res, 400, { error: 'Missing path parameter' });
    }

    try {
      const parentDir = path.dirname(targetPath);
      if (!fs.existsSync(parentDir)) {
        fs.mkdirSync(parentDir, { recursive: true });
      }

      const fileStream = fs.createWriteStream(targetPath);
      req.pipe(fileStream);

      fileStream.on('finish', () => {
        sendJson(res, 200, { success: true, path: targetPath });
      });

      fileStream.on('error', (err) => {
        sendJson(res, 500, { error: err.message });
      });
    } catch (err) {
      sendJson(res, 500, { error: err.message });
    }
    return;
  }

  if (pathname === '/api/fs/extract_audio') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const { path: videoPath } = JSON.parse(body || '{}');
        if (!videoPath || !fs.existsSync(videoPath)) {
          return sendJson(res, 400, { error: 'Invalid video path' });
        }
        const wavPath = await extractAudioFromVideo(videoPath);
        sendJson(res, 200, { path: wavPath, name: path.basename(wavPath) });
      } catch (err) {
        sendJson(res, 500, { error: err.message });
      }
    });
    return;
  }

  // Handle Preset Commands & Tauri Invoke compatibility
  if (pathname.startsWith('/api/invoke/')) {
    const cmd = pathname.replace('/api/invoke/', '');
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const args = body ? JSON.parse(body) : {};

        if (cmd === 'bypass_read_dir_presets' || cmd === 'get_preset_files') {
          const files = fs.readdirSync(PRESET_DIR).filter(f => f.endsWith('.json'));
          return sendJson(res, 200, files);
        }

        if (cmd === 'bypass_read_preset' || cmd === 'load_preset_file') {
          const presetName = path.basename(args.path || args.name || '');
          const presetFile = path.join(PRESET_DIR, presetName);
          if (fs.existsSync(presetFile)) {
            const content = fs.readFileSync(presetFile, 'utf8');
            return sendJson(res, 200, content);
          }
          return sendJson(res, 200, '');
        }

        if (cmd === 'bypass_save_preset' || cmd === 'save_preset_file') {
          const presetName = path.basename(args.path || args.name || '');
          const presetFile = path.join(PRESET_DIR, presetName);
          const data = typeof args.data === 'string' ? args.data : JSON.stringify(args.data || args.content || {});
          fs.writeFileSync(presetFile, data, 'utf8');
          return sendJson(res, 200, { success: true });
        }

        if (cmd === 'bypass_delete_preset' || cmd === 'delete_preset_file') {
          const presetName = path.basename(args.path || args.name || '');
          const presetFile = path.join(PRESET_DIR, presetName);
          if (fs.existsSync(presetFile)) {
            fs.unlinkSync(presetFile);
          }
          return sendJson(res, 200, { success: true });
        }

        sendJson(res, 200, null);
      } catch (err) {
        sendJson(res, 500, { error: err.message });
      }
    });
    return;
  }

  // --------------------------------------------------------------------------
  // STATIC FILE SERVING FOR GUI
  // --------------------------------------------------------------------------
  let filePath = path.join(GUI_DIR, pathname === '/' ? 'index.html' : pathname);

  // Security: prevent directory traversal outside GUI_DIR
  if (!filePath.startsWith(GUI_DIR)) {
    filePath = path.join(GUI_DIR, 'index.html');
  }

  // SPA fallback
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(GUI_DIR, 'index.html');
  }

  try {
    const ext = path.extname(filePath).toLowerCase();
    const mime = MIME_TYPES[ext] || 'application/octet-stream';
    const stat = fs.statSync(filePath);

    res.writeHead(200, {
      'Content-Type': mime,
      'Content-Length': stat.size,
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-cache',
    });
    fs.createReadStream(filePath).pipe(res);
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Internal Server Error: ' + err.message);
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[KamidiMastering] Sovereign DSP & IPC Engine running on http://127.0.0.1:${PORT}`);
});