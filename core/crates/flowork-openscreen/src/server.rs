use crate::assets::{serve_streaming_asset, serve_web_asset};
use std::{
    io::{BufRead, BufReader, Read, Write},
    net::{TcpListener, TcpStream},
    path::{Path, PathBuf},
    sync::Arc,
    thread,
};

pub struct EmbeddedServer {
    pub port: u16,
}

impl EmbeddedServer {
    pub fn start(
        web_dir: PathBuf,
        resources_dir: PathBuf,
        recordings_dir: PathBuf,
    ) -> Result<Self, std::io::Error> {
        let listener = TcpListener::bind("127.0.0.1:0")?;
        let port = listener.local_addr()?.port();

        let web_dir = Arc::new(web_dir);
        let resources_dir = Arc::new(resources_dir);
        let recordings_dir = Arc::new(recordings_dir);

        thread::spawn(move || {
            for stream in listener.incoming().flatten() {
                let w = web_dir.clone();
                let r = resources_dir.clone();
                let rec = recordings_dir.clone();
                thread::spawn(move || {
                    handle_connection(stream, &w, &r, &rec);
                });
            }
        });

        Ok(Self { port })
    }
}

fn handle_connection(
    mut stream: TcpStream,
    web_dir: &Path,
    resources_dir: &Path,
    recordings_dir: &Path,
) {
    let mut reader = BufReader::new(&stream);
    let mut request_line = String::new();
    if reader.read_line(&mut request_line).is_err() || request_line.is_empty() {
        return;
    }

    let parts: Vec<&str> = request_line.split_whitespace().collect();
    if parts.len() < 2 {
        return;
    }

    let raw_uri = parts[1];
    let path = raw_uri.split('?').next().unwrap_or("/");

    let mut range_header: Option<String> = None;
    for line in reader.by_ref().lines().map_while(Result::ok) {
        if line.is_empty() || line == "\r" {
            break;
        }
        if line.to_lowercase().starts_with("range:") {
            range_header = Some(line["range:".len()..].trim().to_string());
        }
    }

    let response = if path.starts_with("/recordings/") {
        let rel = path.trim_start_matches("/recordings/");
        serve_streaming_asset(&recordings_dir.join(rel).to_string_lossy(), range_header.as_deref())
    } else if path.starts_with("/resources/") {
        let rel = path.trim_start_matches("/resources/");
        serve_streaming_asset(&resources_dir.join(rel).to_string_lossy(), range_header.as_deref())
    } else {
        serve_web_asset(web_dir, path)
    };

    let status = response.status();
    let status_code = status.as_u16();
    let status_text = status.canonical_reason().unwrap_or("OK");

    let mut header_bytes = Vec::new();
    let _ = write!(header_bytes, "HTTP/1.1 {} {}\r\n", status_code, status_text);

    for (k, v) in response.headers() {
        if let Ok(v_str) = v.to_str() {
            let _ = write!(header_bytes, "{}: {}\r\n", k.as_str(), v_str);
        }
    }
    let _ = write!(header_bytes, "Connection: close\r\n\r\n");

    let _ = stream.write_all(&header_bytes);
    let _ = stream.write_all(response.body());
    let _ = stream.flush();
}
