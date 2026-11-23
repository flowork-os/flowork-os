use std::{
    borrow::Cow,
    fs::File,
    io::{Read, Seek, SeekFrom},
    path::{Path, PathBuf},
};
use wry::http::{header, Response, StatusCode};

pub fn serve_web_asset(base_dir: &Path, path: &str) -> Response<Cow<'static, [u8]>> {
    let clean_path = path.trim_start_matches('/');
    let clean_path = if clean_path.is_empty() {
        "index.html"
    } else {
        clean_path
    };

    let file_path = base_dir.join(clean_path);
    if !file_path.exists() || !file_path.is_file() {
        // Fallback to index.html for SPA routing
        let index_path = base_dir.join("index.html");
        if let Ok(bytes) = std::fs::read(&index_path) {
            return Response::builder()
                .header(header::CONTENT_TYPE, "text/html; charset=utf-8")
                .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
                .body(Cow::Owned(bytes))
                .unwrap_or_else(|_| not_found());
        }
        return not_found();
    }

    let mime = if clean_path.ends_with(".js") || clean_path.ends_with(".mjs") {
        "text/javascript; charset=utf-8".to_string()
    } else if clean_path.ends_with(".css") {
        "text/css; charset=utf-8".to_string()
    } else if clean_path.ends_with(".html") {
        "text/html; charset=utf-8".to_string()
    } else if clean_path.ends_with(".wasm") {
        "application/wasm".to_string()
    } else {
        mime_guess::from_path(&file_path)
            .first_or_octet_stream()
            .to_string()
    };

    match std::fs::read(&file_path) {
        Ok(bytes) => Response::builder()
            .header(header::CONTENT_TYPE, mime)
            .header(header::CONTENT_LENGTH, bytes.len().to_string())
            .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
            .body(Cow::Owned(bytes))
            .unwrap_or_else(|_| not_found()),
        Err(_) => not_found(),
    }
}

pub fn serve_streaming_asset(
    path_str: &str,
    range_header: Option<&str>,
) -> Response<Cow<'static, [u8]>> {
    let file_path = PathBuf::from(path_str);
    if !file_path.exists() || !file_path.is_file() {
        return not_found();
    }

    let mut file = match File::open(&file_path) {
        Ok(f) => f,
        Err(_) => return not_found(),
    };

    let total_len = match file.metadata() {
        Ok(m) => m.len(),
        Err(_) => return not_found(),
    };

    let mime = mime_guess::from_path(&file_path)
        .first_or_octet_stream()
        .to_string();

    if let Some(range_str) = range_header {
        if let Some((start, end)) = parse_range(range_str, total_len) {
            let chunk_len = end - start + 1;
            if file.seek(SeekFrom::Start(start)).is_ok() {
                let mut buf = vec![0u8; chunk_len as usize];
                if file.read_exact(&mut buf).is_ok() {
                    return Response::builder()
                        .status(StatusCode::PARTIAL_CONTENT)
                        .header(header::CONTENT_TYPE, mime)
                        .header(header::ACCEPT_RANGES, "bytes")
                        .header(
                            header::CONTENT_RANGE,
                            format!("bytes {}-{}/{}", start, end, total_len),
                        )
                        .header(header::CONTENT_LENGTH, chunk_len.to_string())
                        .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
                        .body(Cow::Owned(buf))
                        .unwrap_or_else(|_| not_found());
                }
            }
        }
    }

    // Default full read (for smaller files or when no Range header)
    let mut buf = Vec::with_capacity(total_len as usize);
    if file.read_to_end(&mut buf).is_ok() {
        Response::builder()
            .status(StatusCode::OK)
            .header(header::CONTENT_TYPE, mime)
            .header(header::ACCEPT_RANGES, "bytes")
            .header(header::CONTENT_LENGTH, total_len.to_string())
            .header(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*")
            .body(Cow::Owned(buf))
            .unwrap_or_else(|_| not_found())
    } else {
        not_found()
    }
}

fn parse_range(range_str: &str, total_len: u64) -> Option<(u64, u64)> {
    if !range_str.starts_with("bytes=") {
        return None;
    }
    let parts: Vec<&str> = range_str["bytes=".len()..].split('-').collect();
    if parts.len() != 2 {
        return None;
    }

    let start = parts[0].parse::<u64>().ok()?;
    let end = if parts[1].is_empty() {
        (start + 1024 * 1024 * 4).min(total_len.saturating_sub(1))
    } else {
        parts[1].parse::<u64>().ok()?.min(total_len.saturating_sub(1))
    };

    if start <= end && start < total_len {
        Some((start, end))
    } else {
        None
    }
}

fn not_found() -> Response<Cow<'static, [u8]>> {
    Response::builder()
        .status(StatusCode::NOT_FOUND)
        .header(header::CONTENT_TYPE, "text/plain")
        .body(Cow::Borrowed(b"404 Not Found".as_slice()))
        .unwrap()
}
