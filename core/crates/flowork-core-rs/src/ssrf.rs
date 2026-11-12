use reqwest::redirect::Policy;
use reqwest::{Client, Url};
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
use std::time::Duration;
use tokio::net::lookup_host;

const MAX_REDIRECT_HOPS: usize = 5;
const MAX_FETCH_BODY_BYTES: usize = 8 * 1024 * 1024;

/// Opt-in environment switch allowing intentional local/LAN dev testing.
pub fn env_allows_private_network() -> bool {
    matches!(
        std::env::var("FLOWORK_ALLOW_PRIVATE_NETWORK")
            .ok()
            .as_deref()
            .map(str::trim)
            .map(str::to_ascii_lowercase)
            .as_deref(),
        Some("1") | Some("true") | Some("yes") | Some("on")
    )
}

/// Centralized SSRF IP deny-set covering loopback, RFC1918, CGNAT, link-local
/// (including cloud metadata 169.254.169.254), unspecified/broadcast/multicast,
/// IPv6 unique-local/link-local, and IPv4-mapped/compatible IPv6 addresses.
pub fn is_forbidden_ip(ip: IpAddr) -> bool {
    match ip {
        IpAddr::V4(v4) => is_forbidden_ipv4(v4),
        IpAddr::V6(v6) => is_forbidden_ipv6(v6),
    }
}

fn is_forbidden_ipv4(v4: Ipv4Addr) -> bool {
    let o = v4.octets();
    v4.is_loopback()
        || v4.is_private()
        || v4.is_link_local()
        || v4.is_broadcast()
        || v4.is_documentation()
        || v4.is_unspecified()
        || v4.is_multicast()
        // 0.0.0.0/8 ("this host on this network")
        || o[0] == 0
        // 100.64.0.0/10 (Carrier-Grade NAT / shared address space)
        || (o[0] == 100 && (o[1] & 0xC0) == 64)
        // 198.18.0.0/15 (network benchmark tests)
        || (o[0] == 198 && (o[1] & 0xFE) == 18)
        // 240.0.0.0/4 (reserved/future use)
        || o[0] >= 240
}

fn is_forbidden_ipv6(v6: Ipv6Addr) -> bool {
    if let Some(mapped) = v6.to_ipv4_mapped() {
        return is_forbidden_ipv4(mapped);
    }
    if let Some(compat) = v6.to_ipv4() {
        return is_forbidden_ipv4(compat);
    }
    let segs = v6.segments();
    v6.is_loopback()
        || v6.is_unspecified()
        || v6.is_multicast()
        // fc00::/7 (Unique Local Addresses)
        || (segs[0] & 0xfe00) == 0xfc00
        // fe80::/10 (Link-Local Unicast)
        || (segs[0] & 0xffc0) == 0xfe80
        // 2001:db8::/32 (Documentation)
        || (segs[0] == 0x2001 && segs[1] == 0x0db8)
}

fn is_forbidden_hostname(host_lower: &str) -> bool {
    host_lower == "localhost"
        || host_lower.ends_with(".localhost")
        || host_lower.ends_with(".local")
        || host_lower == "metadata.google.internal"
        || host_lower.ends_with(".internal")
}

/// Validates URL syntax, scheme, and literal host without performing DNS lookup.
/// Returns `Ok(None)` when `allow_about_blank` is true and the URL is `about:blank`.
pub fn validate_url_syntax(raw_url: &str, allow_about_blank: bool) -> Result<Option<Url>, String> {
    let trimmed = raw_url.trim();
    if allow_about_blank && trimmed.eq_ignore_ascii_case("about:blank") {
        return Ok(None);
    }
    let parsed = Url::parse(trimmed)
        .map_err(|e| format!("Invalid URL '{}': {}", trimmed, e))?;

    match parsed.scheme() {
        "http" | "https" => {}
        other => {
            return Err(format!(
                "SSRF guard blocked unsupported URL scheme '{}://' (only http/https allowed)",
                other
            ));
        }
    }

    let allow_private = env_allows_private_network();
    let host_str = parsed
        .host_str()
        .ok_or_else(|| format!("Invalid URL '{}': missing host", trimmed))?;
    let host_unbracketed = host_str.trim_start_matches('[').trim_end_matches(']');

    if !allow_private {
        if let Ok(ip) = host_unbracketed.parse::<IpAddr>() {
            if is_forbidden_ip(ip) {
                return Err(format!(
                    "SSRF guard blocked private/internal IP target '{}'",
                    ip
                ));
            }
        } else {
            let lower = host_unbracketed.trim_end_matches('.').to_ascii_lowercase();
            if is_forbidden_hostname(&lower) {
                return Err(format!(
                    "SSRF guard blocked internal hostname '{}'",
                    host_unbracketed
                ));
            }
        }
    }

    Ok(Some(parsed))
}

/// Validates a URL and performs DNS-resolution-time SSRF inspection, returning the
/// parsed URL and resolved `SocketAddr` list so callers can pin connections against DNS rebinding.
pub async fn validate_url_with_dns(
    raw_url: &str,
    allow_about_blank: bool,
) -> Result<Option<(Url, Vec<SocketAddr>)>, String> {
    let Some(parsed) = validate_url_syntax(raw_url, allow_about_blank)? else {
        return Ok(None);
    };

    let host_str = parsed
        .host_str()
        .ok_or_else(|| "URL missing host".to_string())?;
    let host_unbracketed = host_str.trim_start_matches('[').trim_end_matches(']');
    let port = parsed
        .port_or_known_default()
        .ok_or_else(|| "URL missing known port".to_string())?;

    let addrs: Vec<SocketAddr> = if let Ok(ip) = host_unbracketed.parse::<IpAddr>() {
        vec![SocketAddr::new(ip, port)]
    } else {
        lookup_host((host_unbracketed, port))
            .await
            .map_err(|e| format!("DNS resolution failed for '{}': {}", host_unbracketed, e))?
            .collect()
    };

    if addrs.is_empty() {
        return Err(format!(
            "DNS resolution returned no addresses for '{}'",
            host_unbracketed
        ));
    }

    if !env_allows_private_network() {
        for addr in &addrs {
            if is_forbidden_ip(addr.ip()) {
                return Err(format!(
                    "SSRF guard blocked '{}' resolving to private/internal IP '{}'",
                    host_unbracketed,
                    addr.ip()
                ));
            }
        }
    }

    Ok(Some((parsed, addrs)))
}

/// Validates browser navigation targets (allows `about:blank` when requested, blocks `file://`,
/// `javascript:`, loopback, RFC1918, link-local/metadata, and DNS rebinding to internal hosts).
pub async fn validate_browser_url_dns(
    raw_url: &str,
    allow_about_blank: bool,
) -> Result<(), String> {
    let _ = validate_url_with_dns(raw_url, allow_about_blank).await?;
    Ok(())
}

/// Performs an SSRF-hardened HTTP GET with:
/// - scheme & hostname filtering
/// - DNS-resolution-time private IP blocking
/// - socket pinning (`resolve_to_addrs`) to defeat DNS-rebinding TOCTOU
/// - manual per-hop redirect validation (blocking 3xx redirects into localhost/LAN/metadata)
/// - bounded response body read (max 8 MiB)
pub async fn safe_http_get(
    raw_url: &str,
    user_agent: &str,
    timeout: Duration,
) -> Result<(u16, String, String), String> {
    let mut current_url = raw_url.trim().to_string();

    for hop in 0..=MAX_REDIRECT_HOPS {
        let Some((parsed, addrs)) = validate_url_with_dns(&current_url, false).await? else {
            return Err("about:blank is not valid for HTTP fetch".to_string());
        };

        let host_unbracketed = parsed
            .host_str()
            .unwrap_or_default()
            .trim_start_matches('[')
            .trim_end_matches(']');

        let mut builder = Client::builder()
            .timeout(timeout)
            .user_agent(user_agent)
            .redirect(Policy::none());

        if host_unbracketed.parse::<IpAddr>().is_err() {
            builder = builder.resolve_to_addrs(host_unbracketed, &addrs);
        }

        let client = builder
            .build()
            .map_err(|e| format!("Failed to construct HTTP client: {}", e))?;

        let resp = client
            .get(parsed.clone())
            .send()
            .await
            .map_err(|e| format!("HTTP request failed: {}", e))?;

        let status = resp.status();
        if status.is_redirection() {
            if hop == MAX_REDIRECT_HOPS {
                return Err(format!("Exceeded maximum redirect hops ({})", MAX_REDIRECT_HOPS));
            }
            let loc = resp
                .headers()
                .get(reqwest::header::LOCATION)
                .and_then(|v| v.to_str().ok())
                .ok_or_else(|| "Redirect response missing Location header".to_string())?;
            let next = parsed
                .join(loc)
                .map_err(|e| format!("Invalid redirect target '{}': {}", loc, e))?;
            current_url = next.to_string();
            continue;
        }

        let code = status.as_u16();
        let final_url = parsed.to_string();
        let bytes = resp
            .bytes()
            .await
            .map_err(|e| format!("Failed reading HTTP body: {}", e))?;
        let slice = if bytes.len() > MAX_FETCH_BODY_BYTES {
            &bytes[..MAX_FETCH_BODY_BYTES]
        } else {
            &bytes[..]
        };
        let text = String::from_utf8_lossy(slice).into_owned();
        return Ok((code, final_url, text));
    }

    Err("Unexpected redirect loop exit".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    use tokio::net::TcpListener;

    #[test]
    fn denies_all_private_and_special_ips() {
        let forbidden = [
            "127.0.0.1",
            "127.0.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "172.31.255.254",
            "192.168.1.1",
            "169.254.169.254",
            "100.64.0.1",
            "0.0.0.0",
            "198.18.0.1",
            "224.0.0.1",
            "::1",
            "::",
            "fc00::1",
            "fd12:3456::1",
            "fe80::1",
            "::ffff:127.0.0.1",
            "::ffff:169.254.169.254",
        ];
        for raw in forbidden {
            let ip: IpAddr = raw.parse().expect("valid test IP");
            assert!(is_forbidden_ip(ip), "Expected forbidden IP: {}", raw);
        }

        let allowed = ["8.8.8.8", "1.1.1.1", "93.184.216.34", "2606:4700:4700::1111"];
        for raw in allowed {
            let ip: IpAddr = raw.parse().expect("valid public IP");
            assert!(!is_forbidden_ip(ip), "Expected allowed public IP: {}", raw);
        }
    }

    #[test]
    fn blocks_schemes_and_literal_private_urls() {
        assert!(validate_url_syntax("file:///etc/passwd", false).is_err());
        assert!(validate_url_syntax("javascript:alert(1)", false).is_err());
        assert!(validate_url_syntax("http://127.0.0.1:9099/api/vault", false).is_err());
        assert!(validate_url_syntax("http://169.254.169.254/latest/meta-data/", false).is_err());
        assert!(validate_url_syntax("http://[::1]:18090/health", false).is_err());
        assert!(validate_url_syntax("http://localhost:18095/events", false).is_err());
        assert!(validate_url_syntax("http://2130706433/", false).is_err());
        assert!(validate_url_syntax("about:blank", true).unwrap().is_none());
        assert!(validate_url_syntax("about:blank", false).is_err());
        assert!(validate_url_syntax("https://example.com/path", false).is_ok());
    }

    #[tokio::test]
    async fn blocks_local_http_fetch_by_default() {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        tokio::spawn(async move {
            if let Ok((mut sock, _)) = listener.accept().await {
                let mut buf = [0u8; 512];
                let _ = sock.read(&mut buf).await;
                let _ = sock.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok").await;
            }
        });
        let res = safe_http_get(
            &format!("http://127.0.0.1:{}/secret", addr.port()),
            "test-agent",
            Duration::from_secs(2),
        )
        .await;
        assert!(res.is_err());
    }
}
