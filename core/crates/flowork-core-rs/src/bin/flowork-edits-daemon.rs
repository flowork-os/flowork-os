use axum::body::{Body, Bytes};
use axum::extract::Path as AxumPath;
use axum::http::{HeaderMap, HeaderValue, Method, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use flowork_core_rs::{content_type_for_path, resolve_home_dir};
use futures_util::stream;
use serde_json::{json, Value};
use std::env;
use std::fs;
use std::io::SeekFrom;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncReadExt, AsyncSeekExt};
use tokio::net::TcpListener;
use tower_http::cors::{Any, CorsLayer};

const EDITS_ROOT: &str = "/opt/floworkos/apps/flowork-edits";

fn now_millis() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

fn create_project_archive(output_path: &Path) -> Result<(), String> {
    let ts = now_millis();
    let manifest = json!({
        "schema_version": 1,
        "app_version": "454.0.0.38.112",
        "project_id": format!("flowork-{}", ts),
        "canvas": {
            "width": 1080,
            "height": 1920,
            "aspect_ratio": "9:16",
            "frame_rate": 30.0
        },
        "assets": []
    });

    let composition = json!({
        "format_version": "1.0",
        "tracks": [
            {
                "id": "track-captions",
                "type": "text",
                "elements": [
                    {
                        "id": "caption-1",
                        "text": "Flowork Edits on Linux",
                        "start_time_ms": 0,
                        "duration_ms": 3000
                    }
                ]
            },
            {
                "id": "track-main-video",
                "type": "video",
                "elements": []
            },
            {
                "id": "track-audio",
                "type": "audio",
                "elements": []
            }
        ]
    });

    let tmp_dir = PathBuf::from(format!("/tmp/bsleditsx_{}", ts));
    fs::create_dir_all(&tmp_dir).map_err(|e| format!("mkdir {:?}: {}", tmp_dir, e))?;
    fs::write(
        tmp_dir.join("manifest.json"),
        serde_json::to_string_pretty(&manifest).unwrap_or_default(),
    )
    .map_err(|e| format!("write manifest.json: {}", e))?;
    fs::write(
        tmp_dir.join("composition.json"),
        serde_json::to_string_pretty(&composition).unwrap_or_default(),
    )
    .map_err(|e| format!("write composition.json: {}", e))?;

    let status = Command::new("7z")
        .arg("a")
        .arg("-tzip")
        .arg(output_path)
        .arg(tmp_dir.join("manifest.json"))
        .arg(tmp_dir.join("composition.json"))
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map_err(|e| format!("Failed launching 7z: {}", e))?;

    let _ = fs::remove_dir_all(&tmp_dir);
    if !status.success() {
        return Err(format!("7z exited with status {:?}", status.code()));
    }
    Ok(())
}

fn safe_join(base_dir: &Path, rel: &str) -> Option<PathBuf> {
    let base_canon = fs::canonicalize(base_dir).ok()?;
    let trimmed = rel.trim_start_matches('/');
    let candidate = base_canon.join(trimmed);
    let canon = fs::canonicalize(&candidate).ok()?;
    if canon.starts_with(&base_canon) && canon.is_file() {
        Some(canon)
    } else {
        None
    }
}

async fn handle_info() -> impl IntoResponse {
    Json(json!({
        "app": "Flowork Edits",
        "version": "454.0.0-sovereign",
        "engine": "Flowork Media Composition Engine (MCE-Linux)",
        "platform": "Flowork OS",
        "sampleVideo": "/assets/sample_reel.mp4",
        "handoff": "Ready (_baseltransfer._tcp)"
    }))
}

async fn handle_export(body: Bytes) -> impl IntoResponse {
    let parsed: Value = if body.is_empty() {
        json!({})
    } else {
        match serde_json::from_slice(&body) {
            Ok(v) => v,
            Err(e) => {
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    Json(json!({ "error": e.to_string() })),
                );
            }
        }
    };
    let project_title = parsed
        .get("projectTitle")
        .and_then(|v| v.as_str())
        .unwrap_or("Untitled_Reel");
    let aspect_ratio = parsed
        .get("aspectRatio")
        .and_then(|v| v.as_str())
        .unwrap_or("9:16");
    let dest = parsed
        .get("outputPath")
        .and_then(|v| v.as_str())
        .map(str::to_string)
        .unwrap_or_else(|| {
            resolve_home_dir()
                .join("Videos")
                .join(format!("{}.mp4", project_title))
                .to_string_lossy()
                .to_string()
        });

    (
        StatusCode::OK,
        Json(json!({
            "status": "rendering_started",
            "destPath": dest,
            "aspectRatio": aspect_ratio
        })),
    )
}

async fn stream_range_file(full_path: PathBuf, headers: HeaderMap) -> Response {
    let Ok(meta) = tokio::fs::metadata(&full_path).await else {
        return StatusCode::NOT_FOUND.into_response();
    };
    let file_size = meta.len();
    let content_type = content_type_for_path(&full_path);

    let range_hdr = headers
        .get("range")
        .and_then(|v| v.to_str().ok())
        .map(str::to_string);

    let (start, end, is_partial) = if let Some(ref raw_range) = range_hdr {
        if file_size == 0 {
            return StatusCode::RANGE_NOT_SATISFIABLE.into_response();
        }
        match http_range_header::parse_range_header(raw_range)
            .and_then(|parsed| parsed.validate(file_size))
        {
            Ok(ranges) if !ranges.is_empty() => {
                let first = &ranges[0];
                (*first.start(), *first.end(), true)
            }
            _ => return StatusCode::RANGE_NOT_SATISFIABLE.into_response(),
        }
    } else {
        (0u64, file_size.saturating_sub(1), false)
    };

    let Ok(mut file) = tokio::fs::File::open(&full_path).await else {
        return StatusCode::INTERNAL_SERVER_ERROR.into_response();
    };
    if start > 0 && file.seek(SeekFrom::Start(start)).await.is_err() {
        return StatusCode::INTERNAL_SERVER_ERROR.into_response();
    }

    let total_len = if file_size == 0 { 0 } else { end - start + 1 };
    let byte_stream = stream::unfold((file, total_len), |(mut f, remaining)| async move {
        if remaining == 0 {
            return None;
        }
        let to_read = remaining.min(64 * 1024) as usize;
        let mut buf = vec![0u8; to_read];
        match f.read(&mut buf).await {
            Ok(0) => None,
            Ok(n) => {
                buf.truncate(n);
                Some((Ok::<Bytes, std::io::Error>(Bytes::from(buf)), (f, remaining - n as u64)))
            }
            Err(e) => Some((Err(e), (f, 0))),
        }
    });

    let mut builder = Response::builder()
        .status(if is_partial {
            StatusCode::PARTIAL_CONTENT
        } else {
            StatusCode::OK
        })
        .header("Accept-Ranges", HeaderValue::from_static("bytes"))
        .header("Content-Type", HeaderValue::from_static(content_type))
        .header("Content-Length", total_len.to_string())
        .header("Access-Control-Allow-Origin", HeaderValue::from_static("*"));

    if is_partial {
        let cr = format!("bytes {}-{}/{}", start, end, file_size);
        if let Ok(hv) = HeaderValue::from_str(&cr) {
            builder = builder.header("Content-Range", hv);
        }
    }

    builder
        .body(Body::from_stream(byte_stream))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

async fn handle_asset(AxumPath(rel): AxumPath<String>, headers: HeaderMap) -> Response {
    let assets_dir = Path::new(EDITS_ROOT).join("assets");
    if let Some(full_path) = safe_join(&assets_dir, &rel) {
        stream_range_file(full_path, headers).await
    } else {
        serve_frontend_path(Some(&format!("assets/{}", rel))).await
    }
}

async fn handle_root() -> Response {
    serve_frontend_path(None).await
}

async fn handle_static_fallback(AxumPath(rel): AxumPath<String>) -> Response {
    serve_frontend_path(Some(&rel)).await
}

async fn serve_frontend_path(rel_opt: Option<&str>) -> Response {
    let frontend_dir = Path::new(EDITS_ROOT).join("frontend");
    if let Some(rel) = rel_opt {
        if let Some(file_path) = safe_join(&frontend_dir, rel) {
            if let Ok(bytes) = tokio::fs::read(&file_path).await {
                return Response::builder()
                    .status(StatusCode::OK)
                    .header("Content-Type", HeaderValue::from_static(content_type_for_path(&file_path)))
                    .body(Body::from(bytes))
                    .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
            }
        }
    }

    let index_path = frontend_dir.join("index.html");
    if let Ok(bytes) = tokio::fs::read(&index_path).await {
        return Response::builder()
            .status(StatusCode::OK)
            .header("Content-Type", HeaderValue::from_static("text/html; charset=utf-8"))
            .body(Body::from(bytes))
            .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response());
    }

    (StatusCode::NOT_FOUND, "Not Found").into_response()
}

#[tokio::main]
async fn main() {
    let mut port: u16 = env::var("FLOWORK_EDITS_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(3456);

    let args: Vec<String> = env::args().skip(1).collect();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--help" | "-h" => {
                println!("flowork-edits-daemon — Flowork Media Composition Engine & HTTP Range Server");
                println!("Usage: flowork-edits-daemon [--check] [--pack [out.bsleditsx]] [--port <port>] [--help]");
                return;
            }
            "--check" => {
                println!("flowork-edits-daemon: OK (native Rust HTTP Range + .bsleditsx)");
                return;
            }
            "--pack" => {
                let out_path = args
                    .get(i + 1)
                    .map(PathBuf::from)
                    .unwrap_or_else(|| PathBuf::from("/tmp/Sample_Project.bsleditsx"));
                match create_project_archive(&out_path) {
                    Ok(_) => {
                        println!("Sample .bsleditsx generated: {}", out_path.display());
                        return;
                    }
                    Err(e) => {
                        eprintln!("Failed generating .bsleditsx: {}", e);
                        std::process::exit(1);
                    }
                }
            }
            "--port" => {
                if let Some(p) = args.get(i + 1).and_then(|s| s.parse().ok()) {
                    port = p;
                    i += 1;
                }
            }
            _ => {}
        }
        i += 1;
    }

    let projects_dir = Path::new(EDITS_ROOT).join("projects");
    let _ = fs::create_dir_all(&projects_dir);

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::OPTIONS])
        .allow_headers(Any);

    let app = Router::new()
        .route("/api/info", get(handle_info))
        .route("/api/project/export", post(handle_export))
        .route("/assets/*rest", get(handle_asset))
        .route("/", get(handle_root))
        .route("/*rest", get(handle_static_fallback))
        .layer(cors);

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let listener = match TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("Flowork Edits bind error on {}: {}", addr, e);
            std::process::exit(1);
        }
    };

    println!("⚡ Flowork Edits Engine with Video Range Streaming listening on port {}", port);
    let _ = axum::serve(listener, app).await;
}
