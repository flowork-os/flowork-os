"""Pure-Python X GraphQL search client for the last30days pipeline.

Direct HTTPS client querying X's GraphQL SearchTimeline endpoint using
stdlib urllib (via lib.http.open_request) and browser-cookie auth
(AUTH_TOKEN / CT0). Zero Node.js or external CLI subprocess dependency.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import secrets
import shutil
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import env, health, http, log
from .relevance import token_overlap_relevance as _compute_relevance

# How many times to retry when X returns an HTML interstitial or non-JSON body.
MAX_JSON_DECODE_RETRIES = 2
JSON_DECODE_RETRY_DELAY = 5.0  # seconds between retry attempts

# X GraphQL constants (migrated from legacy bird-search client).
_TWITTER_API_BASE = "https://x.com/i/api/graphql"
_TWITTER_WEB_BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_DISCOVERY_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)

_SEARCH_TIMELINE_QUERY_IDS: Tuple[str, ...] = (
    "6AAys3t42mosm_yTI_QENg",
    "M1jEez78PEfVfbQLvlWMvQ",
    "5h0kNbk3ii97rmfY6CdgAA",
    "Tp1sewRU1AsZpBWhqCZicQ",
)

_DEFAULT_SEARCH_FEATURES: Dict[str, bool] = {
    "rweb_video_screen_enabled": True,
    "profile_label_improvements_pcf_label_in_post_enabled": True,
    "responsive_web_profile_redirect_enabled": True,
    "rweb_tipjar_consumption_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "premium_content_api_read_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
    "responsive_web_grok_analyze_post_followups_enabled": False,
    "responsive_web_grok_annotations_enabled": False,
    "responsive_web_jetfuel_frame": True,
    "post_ctas_fetch_enabled": True,
    "responsive_web_grok_share_attachment_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_grok_show_grok_translated_post": False,
    "responsive_web_grok_analysis_button_from_backend": True,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_grok_image_annotation_enabled": True,
    "responsive_web_grok_imagine_annotation_enabled": True,
    "responsive_web_grok_community_note_auto_translation_is_enabled": False,
    "articles_preview_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

_DEFAULT_FEATURE_OVERRIDES: Dict[str, Any] = {
    "global": {
        "responsive_web_grok_annotations_enabled": False,
        "post_ctas_fetch_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
    },
    "sets": {},
}

_DISCOVERY_PAGES: Tuple[str, ...] = (
    "https://x.com/?lang=en",
    "https://x.com/explore",
    "https://x.com/notifications",
    "https://x.com/settings/profile",
)
_BUNDLE_URL_RE = re.compile(
    r"https://abs\.twimg\.com/responsive-web/client-web(?:-legacy)?/[A-Za-z0-9.-]+\.js"
)
_QUERY_ID_VALID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_OPERATION_PATTERNS: Tuple[Tuple[re.Pattern[str], int, int], ...] = (
    (
        re.compile(
            r"""e\.exports\s*=\s*\{\s*queryId\s*:\s*["']([^"']+)["']\s*,\s*operationName\s*:\s*["']([^"']+)["']""",
            re.DOTALL,
        ),
        2,
        1,
    ),
    (
        re.compile(
            r"""e\.exports\s*=\s*\{\s*operationName\s*:\s*["']([^"']+)["']\s*,\s*queryId\s*:\s*["']([^"']+)["']""",
            re.DOTALL,
        ),
        1,
        2,
    ),
    (
        re.compile(
            r"""operationName\s*[:=]\s*["']([^"']+)["'](.{0,4000}?)queryId\s*[:=]\s*["']([^"']+)["']""",
            re.DOTALL,
        ),
        1,
        3,
    ),
    (
        re.compile(
            r"""queryId\s*[:=]\s*["']([^"']+)["'](.{0,4000}?)operationName\s*[:=]\s*["']([^"']+)["']""",
            re.DOTALL,
        ),
        3,
        1,
    ),
)
_RAW_QUERY_MISSING_RE = re.compile(r"must be defined", re.IGNORECASE)
_QUERY_ID_CACHE_TTL_MS = 24 * 60 * 60 * 1000
_QUERY_ID_LOCK = threading.Lock()
_cached_search_query_id: Optional[str] = None

# Depth configurations: number of results to request
DEPTH_CONFIG = {
    "quick": 12,
    "default": 30,
    "deep": 60,
}

# Module-level credentials injected from .env config or browser failover
_credentials: Dict[str, str] = {}

# Browser-session failover: the browser that supplied the current session and
# a callback that extracts the next browser's session after X rejects it.
_session_browser: Optional[str] = None
_next_session: Optional[Any] = None
_session_lock = threading.Lock()

_CLIENT_UUID = str(uuid.uuid4())
_CLIENT_DEVICE_ID = str(uuid.uuid4())


class _JsonDecodePayloadError(ValueError):
    """Raised when X responds with non-JSON / interstitial HTML payload."""

    def __init__(self, preview: str, message: str):
        super().__init__(message)
        self.preview = preview


def _leading_mentions(text: str) -> list:
    """Leading-run @mention parse, shared with other X-shaped sources (xquik)."""
    from .query import leading_mentions
    return leading_mentions(text)


def _first_of(*values):
    """Return first value that is not None."""
    for v in values:
        if v is not None:
            return v
    return None


def set_credentials(auth_token: Optional[str], ct0: Optional[str]):
    """Inject AUTH_TOKEN/CT0 from .env config or browser cookie extraction."""
    if auth_token:
        _credentials["AUTH_TOKEN"] = auth_token
    if ct0:
        _credentials["CT0"] = ct0


def set_session_failover(browser: Optional[str], next_session: Optional[Any]) -> None:
    """Register where the injected session came from and how to replace it.

    ``next_session`` takes no arguments and returns ``(auth_token, ct0,
    browser)`` for the next browser's session, or None when none is left.
    """
    global _session_browser, _next_session
    with _session_lock:
        _session_browser = browser
        _next_session = next_session


# X answers a search made with an expired or revoked session either with a
# 401 "Could not authenticate you" (code 32) or, for the POST SearchTimeline
# call, with HTTP 200 and a GraphQL "Internal server error" on the timeline.
_SESSION_REJECTED_MARKERS = ("could not authenticate", "http 401", '"code":32')
_SESSION_SUSPECT_MARKERS = ("internal server error",)


def _session_rejected(error: str) -> bool:
    text = error.lower()
    return any(m in text for m in _SESSION_REJECTED_MARKERS)


def _session_suspect(error: str) -> bool:
    text = error.lower()
    return _session_rejected(error) or any(m in text for m in _SESSION_SUSPECT_MARKERS)


def _has_injected_credentials() -> bool:
    """Return True when both X session cookies were injected from config."""
    return bool(_credentials.get("AUTH_TOKEN") and _credentials.get("CT0"))


def _has_process_credentials() -> bool:
    """Return True when AUTH_TOKEN/CT0 are present in process env."""
    return bool(
        (env.read_secret_env("AUTH_TOKEN") or env.read_secret_env("TWITTER_AUTH_TOKEN"))
        and (env.read_secret_env("CT0") or env.read_secret_env("TWITTER_CT0"))
    )


def _resolve_cookies() -> Tuple[Optional[str], Optional[str]]:
    """Resolve active (auth_token, ct0) pair from injected config or env."""
    auth_token = (
        _credentials.get("AUTH_TOKEN")
        or env.read_secret_env("AUTH_TOKEN")
        or env.read_secret_env("TWITTER_AUTH_TOKEN")
    )
    ct0 = (
        _credentials.get("CT0")
        or env.read_secret_env("CT0")
        or env.read_secret_env("TWITTER_CT0")
    )
    return (auth_token or None, ct0 or None)


def _log(msg: str):
    log.source_log("Bird", msg, tty_only=False)


def _scrub_credentials(text: str) -> str:
    """Redact X session cookie values from error strings and log lines."""
    scrubbed = text
    for name in ("AUTH_TOKEN", "CT0", "TWITTER_AUTH_TOKEN", "TWITTER_CT0"):
        value = _credentials.get(name) or os.environ.get(name)
        if value and len(value) >= 8:
            scrubbed = scrubbed.replace(value, "<redacted>")
    return scrubbed


def classify_run_failure(detail: str) -> str:
    """Map Bird HTTP/GraphQL failure shapes to run outcome states."""
    text = detail.lower()
    if any(marker in text for marker in ("interstitial", "non-json", "invalid json")):
        return health.SCHEMA_DRIFT
    if any(
        marker in text
        for marker in (
            "cookie expired", "expired cookie", "unauthorized", "forbidden",
            "login required", "could not authenticate", "session rejected",
        )
    ):
        return health.AUTH_FAILED
    return http.classify_failure(message=detail)


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for X search."""
    from .query import extract_core_subject
    return extract_core_subject(topic, max_words=5, strip_suffixes=True)


def _plain_query_tokens(text: str) -> list[str]:
    """Return lexical tokens without Bird query grouping syntax."""
    separators = str.maketrans({char: " " for char in '"“”()[]{}'})
    return [
        clean
        for token in text.translate(separators).split()
        if (clean := token.strip("'‘’"))
    ]


_GROUPING_CHARS = "“”()[]{}"


def _date_filters(from_date: str, to_date: Optional[str] = None) -> str:
    filters = f"since:{from_date}"
    if to_date is not None:
        end = date.fromisoformat(to_date)
        if end == date.max:
            return filters
        until = end + timedelta(days=1)
        filters += f" until:{until.isoformat()}"
    return filters


def build_topic_query(
    topic: str, from_date: str, to_date: Optional[str] = None
) -> str:
    """Build the X topic query, preserving quoted proper-noun phrases."""
    separators = str.maketrans({char: " " for char in _GROUPING_CHARS})
    cleaned = topic.translate(separators)
    if cleaned.count('"') % 2:
        cleaned = cleaned.replace('"', " ")
    tokens = [
        clean
        for token in cleaned.split()
        if (clean := token.strip("'‘’"))
    ]
    core = " ".join(tokens).strip()
    return " ".join(part for part in (core, _date_filters(from_date, to_date)) if part)


def is_bird_installed() -> bool:
    """Pure-Python X GraphQL client is built in; always available."""
    return True


def is_bird_authenticated() -> Optional[str]:
    """Check if explicit X credentials are available."""
    if _has_injected_credentials():
        return "env AUTH_TOKEN"
    if _has_process_credentials():
        return "env AUTH_TOKEN"
    return None


_probe_cache: Optional[Optional[bool]] = "unset"  # "unset" | True | False | None


def probe_works(timeout: int = 8) -> Optional[bool]:
    """Cheap runtime check that X auth actually returns data."""
    global _probe_cache
    if _probe_cache != "unset":
        return _probe_cache  # type: ignore[return-value]
    if not (_has_injected_credentials() or _has_process_credentials()):
        _probe_cache = False
        return False
    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    resp = _run_bird_search(f"from:x since:{since}", count=1, timeout=timeout)
    if isinstance(resp, dict) and resp.get("error"):
        err = str(resp.get("error")).lower()
        if "timed out" in err or "timeout" in err:
            _probe_cache = None
            return None
        _probe_cache = False
        return False
    _probe_cache = True
    return True


def check_npm_available() -> bool:
    """Check if npm is available (kept for API compatibility)."""
    return shutil.which("npm") is not None


def install_bird() -> Tuple[bool, str]:
    """No-op. Pure-Python X GraphQL search is built in, no installation needed."""
    return True, "Bird X GraphQL search is built into /last30days (Pure Python) - no Node.js or external install needed."


def get_bird_status() -> Dict[str, Any]:
    """Get comprehensive Bird search status."""
    installed = is_bird_installed()
    auth_source = is_bird_authenticated() if installed else None

    return {
        "installed": installed,
        "authenticated": auth_source is not None,
        "username": auth_source,
        "can_install": True,
    }


def _normalize_feature_map(value: Any) -> Dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    return {k: v for k, v in value.items() if isinstance(k, str) and isinstance(v, bool)}


def _load_search_features() -> Dict[str, bool]:
    """Build SearchTimeline GraphQL features dict with optional overrides."""
    features = dict(_DEFAULT_SEARCH_FEATURES)
    overrides_list: List[Dict[str, Any]] = [_DEFAULT_FEATURE_OVERRIDES]

    cache_override = (
        os.environ.get("BIRD_FEATURES_CACHE")
        or os.environ.get("BIRD_FEATURES_PATH")
        or ""
    ).strip()
    cache_path = (
        Path(cache_override).expanduser()
        if cache_override
        else Path.home() / ".config" / "bird" / "features.json"
    )
    if cache_path.is_file():
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                overrides_list.append(raw)
        except (OSError, ValueError):
            pass

    env_json = (os.environ.get("BIRD_FEATURES_JSON") or "").strip()
    if env_json:
        try:
            raw = json.loads(env_json)
            if isinstance(raw, dict):
                overrides_list.append(raw)
        except ValueError:
            pass

    for ov in overrides_list:
        features.update(_normalize_feature_map(ov.get("global")))
        sets = ov.get("sets")
        if isinstance(sets, dict):
            features.update(_normalize_feature_map(sets.get("search")))

    return features


def _query_ids_cache_path() -> Path:
    override = (os.environ.get("BIRD_QUERY_IDS_CACHE") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".config" / "bird" / "query-ids-cache.json"


def _read_cached_search_query_id() -> Optional[str]:
    path = _query_ids_cache_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    ids = data.get("ids")
    if isinstance(ids, dict):
        qid = ids.get("SearchTimeline")
        if isinstance(qid, str) and _QUERY_ID_VALID_RE.match(qid.strip()):
            return qid.strip()
    return None


def _get_search_query_ids() -> List[str]:
    """Return ordered deduplicated SearchTimeline GraphQL query IDs."""
    candidates: List[str] = []
    with _QUERY_ID_LOCK:
        if _cached_search_query_id:
            candidates.append(_cached_search_query_id)
    cached = _read_cached_search_query_id()
    if cached:
        candidates.append(cached)
    candidates.extend(_SEARCH_TIMELINE_QUERY_IDS)

    deduped: List[str] = []
    seen = set()
    for qid in candidates:
        if qid and qid not in seen:
            seen.add(qid)
            deduped.append(qid)
    return deduped


def _fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _DISCOVERY_USER_AGENT,
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        },
        method="GET",
    )
    resp = http.open_request(req, timeout=timeout)
    try:
        raw = resp.read()
        encoding = (
            (resp.headers.get("Content-Encoding") or "").lower()
            if getattr(resp, "headers", None)
            else ""
        )
        if "gzip" in encoding or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", errors="replace")
    finally:
        close_fn = getattr(resp, "close", None)
        if callable(close_fn):
            close_fn()


def _refresh_search_query_id(timeout: int = 15) -> Optional[str]:
    """Discover the current SearchTimeline queryId from x.com web JS bundles."""
    global _cached_search_query_id
    bundle_urls: List[str] = []
    seen_urls = set()
    for page in _DISCOVERY_PAGES:
        try:
            html_body = _fetch_text(page, timeout=min(timeout, 12))
            for url in _BUNDLE_URL_RE.findall(html_body):
                if url not in seen_urls:
                    seen_urls.add(url)
                    bundle_urls.append(url)
        except Exception:
            continue

    discovered_qid: Optional[str] = None
    for url in bundle_urls[:18]:
        try:
            js_text = _fetch_text(url, timeout=min(timeout, 12))
        except Exception:
            continue
        for pattern, op_grp, qid_grp in _OPERATION_PATTERNS:
            for match in pattern.finditer(js_text):
                if match.group(op_grp) == "SearchTimeline":
                    cand = match.group(qid_grp).strip()
                    if _QUERY_ID_VALID_RE.match(cand):
                        discovered_qid = cand
                        break
            if discovered_qid:
                break
        if discovered_qid:
            break

    if not discovered_qid:
        return None

    with _QUERY_ID_LOCK:
        _cached_search_query_id = discovered_qid

    cache_path = _query_ids_cache_path()
    try:
        existing: Dict[str, Any] = {}
        if cache_path.is_file():
            try:
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    existing = loaded
            except (OSError, ValueError):
                pass
        ids = existing.get("ids")
        if not isinstance(ids, dict):
            ids = {}
        ids["SearchTimeline"] = discovered_qid
        snapshot = {
            "fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ttlMs": _QUERY_ID_CACHE_TTL_MS,
            "ids": ids,
            "discovery": {
                "pages": list(_DISCOVERY_PAGES),
                "bundles": [u.rsplit("/", 1)[-1] for u in bundle_urls],
            },
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    return discovered_qid


def _build_json_headers(auth_token: str, ct0: str) -> Dict[str, str]:
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip",
        "authorization": f"Bearer {_TWITTER_WEB_BEARER}",
        "x-csrf-token": ct0,
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en",
        "x-client-uuid": _CLIENT_UUID,
        "x-twitter-client-deviceid": _CLIENT_DEVICE_ID,
        "x-client-transaction-id": secrets.token_hex(16),
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "user-agent": _DEFAULT_USER_AGENT,
        "origin": "https://x.com",
        "referer": "https://x.com/",
        "content-type": "application/json",
    }


def _read_http_response_bytes(resp: Any) -> bytes:
    raw = resp.read()
    encoding = ""
    hdrs = getattr(resp, "headers", None)
    if hdrs is not None:
        encoding = (hdrs.get("Content-Encoding") or "").lower()
    if "gzip" in encoding or raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw)
        except OSError:
            return raw
    return raw


def _is_query_id_mismatch(raw_body: str) -> bool:
    try:
        parsed = json.loads(raw_body)
    except ValueError:
        return False
    errors = parsed.get("errors") if isinstance(parsed, dict) else None
    if not isinstance(errors, list):
        return False
    for err in errors:
        if not isinstance(err, dict):
            continue
        ext = err.get("extensions")
        if isinstance(ext, dict) and ext.get("code") == "GRAPHQL_VALIDATION_FAILED":
            return True
        path = err.get("path")
        msg = str(err.get("message") or "")
        if isinstance(path, list) and "rawQuery" in path and _RAW_QUERY_MISSING_RE.search(msg):
            return True
    return False


# --- GraphQL response -> Bird tweet object conversion ----------------------


def _first_text(*values: Any) -> Optional[str]:
    for val in values:
        if isinstance(val, str):
            trimmed = val.strip()
            if trimmed:
                return trimmed
    return None


def _collect_text_fields(value: Any, keys: set, output: List[str]) -> None:
    if not value or isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            _collect_text_fields(item, keys, output)
        return
    if isinstance(value, dict):
        for k, nested in value.items():
            if k in keys and isinstance(nested, str):
                trimmed = nested.strip()
                if trimmed:
                    output.append(trimmed)
                continue
            _collect_text_fields(nested, keys, output)


def _unique_ordered(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _render_block_text(block: Dict[str, Any], entity_map: Dict[int, Dict[str, Any]]) -> str:
    text = str(block.get("text") or "")
    ranges = []
    for r in block.get("entityRanges") or []:
        if not isinstance(r, dict):
            continue
        key = r.get("key")
        entity = entity_map.get(key) if isinstance(key, int) else None
        data = entity.get("data") if isinstance(entity, dict) else None
        if (
            isinstance(entity, dict)
            and entity.get("type") == "LINK"
            and isinstance(data, dict)
            and data.get("url")
        ):
            ranges.append((int(r.get("offset", 0)), int(r.get("length", 0)), str(data["url"])))
    ranges.sort(key=lambda item: item[0], reverse=True)
    for offset, length, url in ranges:
        link_text = text[offset : offset + length]
        text = text[:offset] + f"[{link_text}]({url})" + text[offset + length :]
    return text.strip()


def _render_atomic_block(block: Dict[str, Any], entity_map: Dict[int, Dict[str, Any]]) -> Optional[str]:
    ranges = block.get("entityRanges") or []
    if not ranges or not isinstance(ranges[0], dict):
        return None
    entity = entity_map.get(ranges[0].get("key"))
    if not isinstance(entity, dict):
        return None
    etype = entity.get("type")
    data = entity.get("data") if isinstance(entity.get("data"), dict) else {}
    if etype == "MARKDOWN":
        md = data.get("markdown")
        return str(md).strip() if isinstance(md, str) and md.strip() else None
    if etype == "DIVIDER":
        return "---"
    if etype == "TWEET" and data.get("tweetId"):
        return f"[Embedded Tweet: https://x.com/i/status/{data['tweetId']}]"
    if etype == "LINK" and data.get("url"):
        return f"[Link: {data['url']}]"
    if etype == "IMAGE":
        return "[Image]"
    return None


def _render_content_state(content_state: Any) -> Optional[str]:
    if not isinstance(content_state, dict):
        return None
    blocks = content_state.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        return None

    entity_map: Dict[int, Dict[str, Any]] = {}
    raw_emap = content_state.get("entityMap") or []
    if isinstance(raw_emap, list):
        for entry in raw_emap:
            if isinstance(entry, dict) and "key" in entry:
                try:
                    entity_map[int(entry["key"])] = entry.get("value") or {}
                except (TypeError, ValueError):
                    pass
    elif isinstance(raw_emap, dict):
        for k, v in raw_emap.items():
            try:
                entity_map[int(k)] = v or {}
            except (TypeError, ValueError):
                pass

    lines: List[str] = []
    ordered_counter = 0
    prev_type: Optional[str] = None
    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype != "ordered-list-item" and prev_type == "ordered-list-item":
            ordered_counter = 0
        if btype == "header-one":
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"# {t}")
        elif btype == "header-two":
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"## {t}")
        elif btype == "header-three":
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"### {t}")
        elif btype == "unordered-list-item":
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"- {t}")
        elif btype == "ordered-list-item":
            ordered_counter += 1
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"{ordered_counter}. {t}")
        elif btype == "blockquote":
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(f"> {t}")
        elif btype == "atomic":
            ent = _render_atomic_block(block, entity_map)
            if ent:
                lines.append(ent)
        else:
            t = _render_block_text(block, entity_map)
            if t:
                lines.append(t)
        prev_type = btype

    rendered = "\n\n".join(lines).strip()
    return rendered or None


def _extract_article_text(result: Dict[str, Any]) -> Optional[str]:
    article = result.get("article")
    if not isinstance(article, dict):
        return None
    article_res = (
        (article.get("article_results") or {}).get("result")
        if isinstance(article.get("article_results"), dict)
        else None
    ) or article
    if not isinstance(article_res, dict):
        article_res = article

    title = _first_text(article_res.get("title"), article.get("title"))
    rich_body = _render_content_state(article_res.get("content_state"))
    if rich_body:
        if title:
            ntitle = title.strip()
            tbody = rich_body.lstrip()
            has_title = (
                tbody == ntitle
                or tbody.startswith(f"{ntitle}\n")
                or any(tbody.startswith(f"{h} {ntitle}") for h in ("#", "##", "###"))
            )
            if not has_title:
                return f"{title}\n\n{rich_body}"
        return rich_body

    def _dig(obj: Any, *keys: str) -> Any:
        cur = obj
        for k in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    body = _first_text(
        article_res.get("plain_text"),
        article.get("plain_text"),
        _dig(article_res, "body", "text"),
        _dig(article_res, "body", "richtext", "text"),
        _dig(article_res, "body", "rich_text", "text"),
        _dig(article_res, "content", "text"),
        _dig(article_res, "content", "richtext", "text"),
        _dig(article_res, "content", "rich_text", "text"),
        article_res.get("text"),
        _dig(article_res, "richtext", "text"),
        _dig(article_res, "rich_text", "text"),
        _dig(article, "body", "text"),
        _dig(article, "body", "richtext", "text"),
        _dig(article, "body", "rich_text", "text"),
        _dig(article, "content", "text"),
        _dig(article, "content", "richtext", "text"),
        _dig(article, "content", "rich_text", "text"),
        article.get("text"),
        _dig(article, "richtext", "text"),
        _dig(article, "rich_text", "text"),
    )
    if body and title and body.strip() == title.strip():
        body = None
    if not body:
        collected: List[str] = []
        _collect_text_fields(article_res, {"text", "title"}, collected)
        _collect_text_fields(article, {"text", "title"}, collected)
        unique = _unique_ordered(collected)
        filtered = [v for v in unique if v != title] if title else unique
        if filtered:
            body = "\n\n".join(filtered)
    if title and body and not body.startswith(title):
        return f"{title}\n\n{body}"
    return body or title


def _extract_note_tweet_text(result: Dict[str, Any]) -> Optional[str]:
    nt = result.get("note_tweet")
    if not isinstance(nt, dict):
        return None
    ntr = nt.get("note_tweet_results")
    note = ntr.get("result") if isinstance(ntr, dict) else None
    if not isinstance(note, dict):
        return None
    rt = note.get("richtext") if isinstance(note.get("richtext"), dict) else {}
    rt2 = note.get("rich_text") if isinstance(note.get("rich_text"), dict) else {}
    cnt = note.get("content") if isinstance(note.get("content"), dict) else {}
    cnt_rt = cnt.get("richtext") if isinstance(cnt.get("richtext"), dict) else {}
    cnt_rt2 = cnt.get("rich_text") if isinstance(cnt.get("rich_text"), dict) else {}
    return _first_text(
        note.get("text"),
        rt.get("text"),
        rt2.get("text"),
        cnt.get("text"),
        cnt_rt.get("text"),
        cnt_rt2.get("text"),
    )


def _extract_tweet_text(result: Dict[str, Any]) -> Optional[str]:
    legacy = result.get("legacy") if isinstance(result.get("legacy"), dict) else {}
    return (
        _extract_article_text(result)
        or _extract_note_tweet_text(result)
        or _first_text(legacy.get("full_text"), legacy.get("text"))
    )


def _unwrap_tweet_result(result: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(result, dict):
        return None
    if isinstance(result.get("tweet"), dict):
        return result["tweet"]
    return result


def _map_tweet_result(result: Any, quote_depth: int = 1) -> Optional[Dict[str, Any]]:
    unwrapped = _unwrap_tweet_result(result)
    if not unwrapped:
        return None
    tweet_id = unwrapped.get("rest_id")
    core = unwrapped.get("core") if isinstance(unwrapped.get("core"), dict) else {}
    user_results = core.get("user_results") if isinstance(core.get("user_results"), dict) else {}
    user_res = user_results.get("result") if isinstance(user_results.get("result"), dict) else {}
    user_legacy = user_res.get("legacy") if isinstance(user_res.get("legacy"), dict) else {}
    user_core = user_res.get("core") if isinstance(user_res.get("core"), dict) else {}

    username = user_legacy.get("screen_name") or user_core.get("screen_name")
    name = user_legacy.get("name") or user_core.get("name") or username
    if not tweet_id or not username:
        return None

    text = _extract_tweet_text(unwrapped)
    if not text:
        return None

    quoted_tweet = None
    if quote_depth > 0:
        qsr = unwrapped.get("quoted_status_result")
        if isinstance(qsr, dict) and qsr.get("result"):
            quoted_tweet = _map_tweet_result(qsr["result"], quote_depth=quote_depth - 1)

    legacy = unwrapped.get("legacy") if isinstance(unwrapped.get("legacy"), dict) else {}
    mapped: Dict[str, Any] = {
        "id": str(tweet_id),
        "text": text,
        "permanent_url": f"https://x.com/{username}/status/{tweet_id}",
        "createdAt": legacy.get("created_at"),
        "replyCount": legacy.get("reply_count"),
        "retweetCount": legacy.get("retweet_count"),
        "likeCount": legacy.get("favorite_count"),
        "quoteCount": legacy.get("quote_count"),
        "conversationId": legacy.get("conversation_id_str"),
        "inReplyToStatusId": legacy.get("in_reply_to_status_id_str"),
        "author": {
            "username": username,
            "name": name or username,
        },
        "authorId": user_res.get("rest_id"),
    }
    if quoted_tweet is not None:
        mapped["quotedTweet"] = quoted_tweet
    return mapped


def _collect_tweet_results_from_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    def _push(res: Any) -> None:
        unwrapped = _unwrap_tweet_result(res)
        if isinstance(unwrapped, dict) and unwrapped.get("rest_id"):
            results.append(unwrapped)

    content = entry.get("content")
    if not isinstance(content, dict):
        return results

    ic = content.get("itemContent")
    if isinstance(ic, dict):
        tr = ic.get("tweet_results")
        if isinstance(tr, dict):
            _push(tr.get("result"))

    item_wrap = content.get("item")
    if isinstance(item_wrap, dict) and isinstance(item_wrap.get("itemContent"), dict):
        tr = item_wrap["itemContent"].get("tweet_results")
        if isinstance(tr, dict):
            _push(tr.get("result"))

    for item in content.get("items") or []:
        if not isinstance(item, dict):
            continue
        for candidate in (
            (item.get("item") or {}).get("itemContent") if isinstance(item.get("item"), dict) else None,
            item.get("itemContent"),
            (item.get("content") or {}).get("itemContent") if isinstance(item.get("content"), dict) else None,
        ):
            if isinstance(candidate, dict) and isinstance(candidate.get("tweet_results"), dict):
                _push(candidate["tweet_results"].get("result"))

    return results


def _parse_tweets_from_instructions(
    instructions: Any, quote_depth: int = 1
) -> List[Dict[str, Any]]:
    tweets: List[Dict[str, Any]] = []
    seen = set()
    if not isinstance(instructions, list):
        return tweets
    for instruction in instructions:
        if not isinstance(instruction, dict):
            continue
        for entry in instruction.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            for res in _collect_tweet_results_from_entry(entry):
                mapped = _map_tweet_result(res, quote_depth=quote_depth)
                if not mapped or mapped["id"] in seen:
                    continue
                seen.add(mapped["id"])
                tweets.append(mapped)
    return tweets


def _extract_cursor_from_instructions(
    instructions: Any, cursor_type: str = "Bottom"
) -> Optional[str]:
    if not isinstance(instructions, list):
        return None
    for instruction in instructions:
        if not isinstance(instruction, dict):
            continue
        for entry in instruction.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            content = entry.get("content")
            if (
                isinstance(content, dict)
                and content.get("cursorType") == cursor_type
                and isinstance(content.get("value"), str)
                and content["value"]
            ):
                return content["value"]
    return None


def _fetch_graphql_search_page(
    query: str,
    page_count: int,
    cursor: Optional[str],
    auth_token: str,
    ct0: str,
    features: Dict[str, bool],
    timeout: int,
) -> Dict[str, Any]:
    """Fetch a single SearchTimeline GraphQL page; refresh queryIds on 404/mismatch."""

    def _attempt(query_ids: List[str]) -> Dict[str, Any]:
        last_error: Optional[str] = None
        had_404 = False
        for query_id in query_ids:
            variables: Dict[str, Any] = {
                "rawQuery": query,
                "count": page_count,
                "querySource": "typed_query",
                "product": "Latest",
            }
            if cursor:
                variables["cursor"] = cursor
            encoded_params = urllib.parse.urlencode(
                {"variables": json.dumps(variables, separators=(",", ":"))}
            )
            url = f"{_TWITTER_API_BASE}/{query_id}/SearchTimeline?{encoded_params}"
            body = json.dumps(
                {"features": features, "queryId": query_id},
                separators=(",", ":"),
            ).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers=_build_json_headers(auth_token, ct0),
                method="POST",
            )
            try:
                resp = http.open_request(req, timeout=timeout)
                try:
                    raw_bytes = _read_http_response_bytes(resp)
                finally:
                    close_fn = getattr(resp, "close", None)
                    if callable(close_fn):
                        close_fn()
                raw_text = raw_bytes.decode("utf-8", errors="replace").strip()
                if not raw_text:
                    return {"success": True, "tweets": [], "cursor": None, "had404": had_404}
                try:
                    data = json.loads(raw_text)
                except ValueError as exc:
                    raise _JsonDecodePayloadError(raw_text[:80], str(exc)) from exc

                if isinstance(data, dict) and data.get("errors"):
                    errs = data["errors"]
                    if isinstance(errs, list) and len(errs) > 0:
                        should_refresh = any(
                            isinstance(e, dict)
                            and isinstance(e.get("extensions"), dict)
                            and e["extensions"].get("code") == "GRAPHQL_VALIDATION_FAILED"
                            for e in errs
                        )
                        msg = ", ".join(
                            str(e.get("message", e)) if isinstance(e, dict) else str(e)
                            for e in errs
                        )
                        return {
                            "success": False,
                            "error": msg,
                            "had404": had_404 or should_refresh,
                        }

                if not isinstance(data, dict):
                    return {"success": True, "tweets": [], "cursor": None, "had404": had_404}

                instructions = (
                    ((data.get("data") or {}).get("search_by_raw_query") or {})
                    .get("search_timeline", {})
                    .get("timeline", {})
                    .get("instructions")
                )
                page_tweets = _parse_tweets_from_instructions(instructions, quote_depth=1)
                next_cursor = _extract_cursor_from_instructions(instructions)
                return {
                    "success": True,
                    "tweets": page_tweets,
                    "cursor": next_cursor,
                    "had404": had_404,
                }
            except urllib.error.HTTPError as exc:
                status = exc.code
                try:
                    err_bytes = _read_http_response_bytes(exc)
                    err_text = err_bytes.decode("utf-8", errors="replace")
                except Exception:
                    err_text = ""
                if status == 404:
                    had_404 = True
                    last_error = f"HTTP {status}"
                    continue
                mismatch = status in (400, 422) and _is_query_id_mismatch(err_text)
                return {
                    "success": False,
                    "error": _scrub_credentials(f"HTTP {status}: {err_text[:200]}"),
                    "had404": had_404 or mismatch,
                }
            except _JsonDecodePayloadError:
                raise
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as exc:
                reason = getattr(exc, "reason", exc)
                last_error = _scrub_credentials(str(reason))
                if "timed out" in last_error.lower():
                    return {
                        "success": False,
                        "error": f"Search timed out after {timeout}s",
                        "had404": False,
                    }
            except Exception as exc:
                last_error = _scrub_credentials(str(exc))

        return {
            "success": False,
            "error": last_error or "Unknown error fetching search results",
            "had404": had_404,
        }

    first = _attempt(_get_search_query_ids())
    if first.get("success"):
        return first
    if first.get("had404"):
        refreshed = _refresh_search_query_id(timeout=timeout)
        if refreshed:
            second = _attempt(_get_search_query_ids())
            if second.get("success"):
                return second
            return {"success": False, "error": second.get("error")}
    return {"success": False, "error": first.get("error")}


def _search_graphql_paged(
    query: str,
    limit: int,
    timeout: int,
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> Dict[str, Any]:
    """Run paged SearchTimeline queries over HTTPS and return Bird-shaped JSON."""
    auth_token, ct0 = _resolve_cookies()
    if not auth_token or not ct0:
        return {
            "error": "No X credentials found (AUTH_TOKEN/CT0 required)",
            "items": [],
        }

    features = _load_search_features()
    page_size = 20
    seen_ids = set()
    tweets: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while len(tweets) < limit:
        if cancel is not None and cancel.is_set():
            return {"error": "bird: research cancelled", "items": []}
        page_timeout = _clamped_bird_timeout(timeout, deadline)
        if page_timeout is None:
            if tweets:
                break
            return {"error": "bird: chain budget exhausted", "items": []}
        page_count = min(page_size, limit - len(tweets))
        page = _fetch_graphql_search_page(
            query=query,
            page_count=page_count,
            cursor=cursor,
            auth_token=auth_token,
            ct0=ct0,
            features=features,
            timeout=page_timeout,
        )
        if not page.get("success"):
            if tweets:
                break
            return {"error": page.get("error") or "Search failed", "items": []}

        page_tweets = page.get("tweets") or []
        added = 0
        for tw in page_tweets:
            tid = tw.get("id")
            if not tid or tid in seen_ids:
                continue
            seen_ids.add(tid)
            tweets.append(tw)
            added += 1
            if len(tweets) >= limit:
                break

        next_cursor = page.get("cursor")
        if not next_cursor or next_cursor == cursor or len(page_tweets) == 0 or added == 0:
            break
        cursor = next_cursor

    return {"items": tweets}


def _invalid_json_error(
    attempts: int,
    decode_error: Optional[str],
    budget_exhausted: bool = False,
) -> Dict[str, Any]:
    noun = "attempt" if attempts == 1 else "attempts"
    skipped = ", retry skipped: chain budget exhausted" if budget_exhausted else ""
    return {
        "error": (
            f"Invalid JSON response after {attempts} {noun}{skipped} "
            f"(likely Twitter anti-bot interstitial): {decode_error}"
        ),
        "items": [],
    }


def _run_bird_search(
    query: str,
    count: int,
    timeout: int,
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> Dict[str, Any]:
    """Run one search, moving to the next browser's X session on rejection."""
    while True:
        started_with = _credentials.get("AUTH_TOKEN")
        response = _run_bird_search_once(query, count, timeout, deadline=deadline, cancel=cancel)
        error = str(response.get("error") or "") if isinstance(response, dict) else ""
        if not error or not _session_suspect(error):
            return response
        if cancel is not None and cancel.is_set():
            return response
        failed_browser = _session_browser
        if deadline is not None and _clamped_bird_timeout(timeout, deadline) is None:
            return _annotate_session_error(response, error, failed_browser)
        wait = -1 if deadline is None else max(0.0, deadline - time.monotonic())
        if not _session_lock.acquire(timeout=wait):
            return _annotate_session_error(response, error, failed_browser)
        try:
            if _credentials.get("AUTH_TOKEN") != started_with:
                switched = True
            else:
                switched = False
                failed_browser = _session_browser
                nxt = (
                    _next_session(deadline=deadline, cancel=cancel)
                    if _next_session is not None else None
                )
                if nxt:
                    auth_token, ct0, browser = nxt
                    set_credentials(auth_token, ct0)
                    _session_browser_update(browser)
                    log.source_log(
                        "X/bird",
                        f"X rejected the {failed_browser} session; retrying with {browser} cookies",
                        tty_only=False,
                    )
                    switched = True
        finally:
            _session_lock.release()
        if switched:
            timeout = _clamped_bird_timeout(timeout, deadline)
            if timeout is None:
                return response
            continue
        return _annotate_session_error(response, error, failed_browser)


def _annotate_session_error(
    response: Dict[str, Any], error: str, failed_browser: Optional[str]
) -> Dict[str, Any]:
    """Name the browser whose X session failed so the report says what to fix."""
    if not failed_browser:
        return response
    if _session_rejected(error):
        return {
            **response,
            "error": (
                f"X session rejected (cookies from {failed_browser}): {error}. "
                f"Log in to x.com again in {failed_browser}, or set FROM_BROWSER "
                "to the browser you use for X."
            ),
        }
    return {
        **response,
        "error": (
            f"{error} (X can return this when the {failed_browser} session "
            f"is expired; if it persists, log in to x.com again in "
            f"{failed_browser} or set FROM_BROWSER to the browser you use for X)"
        ),
    }


def _session_browser_update(browser: str) -> None:
    global _session_browser
    _session_browser = browser


def _run_bird_search_once(
    query: str,
    count: int,
    timeout: int,
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> Dict[str, Any]:
    """Run a single X GraphQL search with interstitial JSON-decode retries."""
    last_decode_error: Optional[str] = None
    attempt_timeout: Optional[int] = timeout

    for attempt in range(MAX_JSON_DECODE_RETRIES):
        if cancel is not None and cancel.is_set():
            return {"error": "bird: research cancelled", "items": []}
        if attempt > 0:
            attempt_timeout = _clamped_bird_timeout(timeout, deadline)
            if attempt_timeout is None:
                return _invalid_json_error(
                    attempt, last_decode_error, budget_exhausted=True,
                )
        try:
            return _search_graphql_paged(
                query=query,
                limit=count,
                timeout=attempt_timeout,
                deadline=deadline,
                cancel=cancel,
            )
        except _JsonDecodePayloadError as exc:
            looks_html = exc.preview.lstrip().lower().startswith(("<!doctype", "<html", "<"))
            attempt_num = attempt + 1
            log_msg = (
                f"Bird search returned non-JSON response "
                f"(looks_html={looks_html}, attempt {attempt_num}/{MAX_JSON_DECODE_RETRIES}, "
                f"first 80 chars: {exc.preview!r})"
            )
            last_decode_error = str(exc)
            if attempt_num < MAX_JSON_DECODE_RETRIES:
                if deadline is not None and (
                    deadline - time.monotonic() < JSON_DECODE_RETRY_DELAY + 1
                ):
                    log.source_log(
                        "X/bird",
                        f"{log_msg}; retry skipped, chain budget exhausted",
                        tty_only=False,
                    )
                    return _invalid_json_error(
                        attempt_num, last_decode_error, budget_exhausted=True,
                    )
                log.source_log(
                    "X/bird",
                    f"{log_msg}; retrying in {JSON_DECODE_RETRY_DELAY:.0f}s",
                    tty_only=False,
                )
                if cancel is not None:
                    cancel.wait(JSON_DECODE_RETRY_DELAY)
                else:
                    time.sleep(JSON_DECODE_RETRY_DELAY)
                continue
            log.source_log("X/bird", log_msg, tty_only=False)
            return _invalid_json_error(attempt_num, last_decode_error)

    return {
        "error": f"Bird search exhausted retries: {last_decode_error}",
        "items": [],
    }


def _clamped_bird_timeout(base: int, deadline: Optional[float]) -> Optional[int]:
    """Per-attempt timeout clamped to the chain's remaining budget."""
    if deadline is None:
        return base
    remaining = deadline - time.monotonic()
    if remaining < 1:
        return None
    return max(1, min(base, int(remaining)))


def _budget_stop(
    response: Dict[str, Any],
    last_clean_response: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Outcome when an optional zero-result retry no longer fits the budget."""
    _log("chain budget exhausted; skipping remaining zero-result retries")
    if last_clean_response is not None:
        return {
            **last_clean_response,
            "warning": "Partial coverage: optional zero-result retries skipped because the search budget was exhausted.",
        }
    return response


def search_x(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> Dict[str, Any]:
    """Search X via direct GraphQL SearchTimeline with automatic retry on 0 results."""
    count = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    cancel_kwargs = {"cancel": cancel} if cancel is not None else {}
    base_timeout = 30 if depth == "quick" else 45 if depth == "default" else 60
    timeout = _clamped_bird_timeout(base_timeout, deadline)
    if timeout is None:
        return {"error": "bird: chain budget exhausted", "items": []}

    core_subject = _extract_core_subject(topic)
    core_words = _plain_query_tokens(core_subject)
    core_topic = " ".join(core_words)
    query = build_topic_query(core_subject, from_date, to_date)
    date_filters = _date_filters(from_date, to_date)

    _log(f"Searching: {query}")
    response = _run_bird_search(query, count, timeout, deadline=deadline, **cancel_kwargs)
    last_clean_response = response if not response.get("error") else None

    items = parse_bird_response(response, query=core_topic)

    if not items and len(core_words) >= 2:
        from .query import extract_compound_terms
        compounds = extract_compound_terms(topic)
        if compounds:
            or_parts = " OR ".join(f'"{t}"' for t in compounds[:3])
            _log(f"0 results for '{core_topic}', retrying with OR groups: {or_parts}")
            query = f"({or_parts}) {date_filters}"
            timeout = _clamped_bird_timeout(base_timeout, deadline)
            if timeout is None:
                return _budget_stop(response, last_clean_response)
            response = _run_bird_search(query, count, timeout, deadline=deadline, **cancel_kwargs)
            if not response.get("error"):
                last_clean_response = response
            items = parse_bird_response(response, query=core_topic)

    if not items and len(core_words) > 2:
        shorter = " ".join(core_words[:2])
        _log(f"0 results for '{core_topic}', retrying with '{shorter}'")
        query = f"{shorter} {date_filters}"
        timeout = _clamped_bird_timeout(base_timeout, deadline)
        if timeout is None:
            return _budget_stop(response, last_clean_response)
        response = _run_bird_search(query, count, timeout, deadline=deadline, **cancel_kwargs)
        if not response.get("error"):
            last_clean_response = response
        items = parse_bird_response(response, query=core_topic)

    if not items and core_words:
        low_signal = {
            "trendiest", "trending", "hottest", "hot", "popular", "viral",
            "best", "top", "latest", "new", "plugin", "plugins",
            "skill", "skills", "tool", "tools",
        }
        candidates = [w for w in core_words if w not in low_signal]
        if candidates:
            anchor = candidates[0]
            strongest = max(candidates, key=len)
            retry_terms = anchor if strongest == anchor else f"{anchor} {strongest}"
            _log(f"0 results for '{core_topic}', retrying anchored on '{retry_terms}'")
            query = f"{retry_terms} {date_filters}"
            timeout = _clamped_bird_timeout(base_timeout, deadline)
            if timeout is None:
                return _budget_stop(response, last_clean_response)
            response = _run_bird_search(query, count, timeout, deadline=deadline, **cancel_kwargs)
            if not response.get("error"):
                last_clean_response = response

    if cancel is not None and cancel.is_set():
        return {**response, "error": "bird: research cancelled"}
    if response.get("error") and last_clean_response is not None:
        _log("Optional retry failed after a clean empty response; preserving no-results outcome")
        return last_clean_response
    return response


def search_handles(
    handles: List[str],
    topic: Optional[str],
    from_date: str,
    count_per: int = 5,
    failure_out: Optional[List[str]] = None,
    *,
    to_date: Optional[str] = None,
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> List[Dict[str, Any]]:
    """Search specific X handles for topic-related content (FROM lane)."""
    if not handles:
        return []
    core_topic = _extract_core_subject(topic) if topic else None
    date_filters = _date_filters(from_date, to_date)

    def _note(msg: str) -> None:
        if failure_out is not None:
            failure_out.append(msg)

    def _search_one_handle(handle: str) -> List[Dict[str, Any]]:
        timeout = _clamped_bird_timeout(15, deadline)
        if timeout is None or (cancel is not None and cancel.is_set()):
            _note("bird handle research cancelled or timed out")
            return []
        clean_handle = handle.lstrip("@")
        query = f"from:{clean_handle} {date_filters}"

        response = _run_bird_search(query, count_per, timeout, deadline=deadline, cancel=cancel)
        err = response.get("error") if isinstance(response, dict) else None
        if err:
            scrubbed = _scrub_credentials(str(err))
            _log(f"Handle search failed for @{clean_handle}: {scrubbed}")
            _note(f"@{clean_handle}: {scrubbed[:160]}")
            return []

        items = parse_bird_response(response, query=core_topic)
        _log(f"Searching: {query} -> {len(items)} results")
        return items

    all_items: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(5, len(handles))) as executor:
        futures = {executor.submit(_search_one_handle, h): h for h in handles}
        for future in as_completed(futures):
            all_items.extend(future.result())

    return all_items


def search_mentions(
    handles: List[str],
    from_date: str,
    count_per: int = 5,
    failure_out: Optional[List[str]] = None,
    *,
    to_date: Optional[str] = None,
    deadline: Optional[float] = None,
    cancel: Any = None,
) -> List[Dict[str, Any]]:
    """Search for tweets ABOUT/TO each handle — the mention lane."""
    if not handles:
        return []
    date_filters = _date_filters(from_date, to_date)

    def _note(msg: str) -> None:
        if failure_out is not None:
            failure_out.append(msg)

    def _search_one(handle: str) -> List[Dict[str, Any]]:
        timeout = _clamped_bird_timeout(15, deadline)
        if timeout is None or (cancel is not None and cancel.is_set()):
            _note("bird mention research cancelled or timed out")
            return []
        clean_handle = handle.lstrip("@")
        query = f"@{clean_handle} {date_filters}"

        response = _run_bird_search(query, count_per, timeout, deadline=deadline, cancel=cancel)
        err = response.get("error") if isinstance(response, dict) else None
        if err:
            scrubbed = _scrub_credentials(str(err))
            _log(f"Mention search failed for @{clean_handle}: {scrubbed}")
            _note(f"@{clean_handle}: {scrubbed[:160]}")
            return []

        items = parse_bird_response(response, query=None)
        hl = clean_handle.lower()

        def _is_own(url: Optional[str]) -> bool:
            u = (url or "").lower()
            return f"x.com/{hl}/status" in u or f"twitter.com/{hl}/status" in u

        about = [it for it in items if not _is_own(it.get("url"))]
        _log(f"Searching: {query} -> {len(about)} mentions")
        return about

    all_items: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(5, len(handles))) as executor:
        futures = {executor.submit(_search_one, h): h for h in handles}
        for future in as_completed(futures):
            all_items.extend(future.result())
    return all_items


def parse_bird_response(response: Any, query: str = "") -> List[Dict[str, Any]]:
    """Parse Bird response to match xai_x output format."""
    items: List[Dict[str, Any]] = []

    if isinstance(response, dict) and response.get("error"):
        _log(f"Bird error: {response['error']}")
        return items

    raw_items = (
        response
        if isinstance(response, list)
        else (
            response.get("items", response.get("tweets", []))
            if isinstance(response, dict)
            else []
        )
    )

    if not isinstance(raw_items, list):
        return items

    for i, tweet in enumerate(raw_items):
        if not isinstance(tweet, dict):
            continue

        url = tweet.get("permanent_url") or tweet.get("url", "")
        if not url and tweet.get("id"):
            author = tweet.get("author", {}) or tweet.get("user", {})
            screen_name = author.get("username") or author.get("screen_name", "")
            if screen_name:
                url = f"https://x.com/{screen_name}/status/{tweet['id']}"

        if not url:
            continue

        parsed_date = None
        created_at = tweet.get("createdAt") or tweet.get("created_at", "")
        if created_at:
            try:
                if len(created_at) > 10 and created_at[10] == "T":
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                parsed_date = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        author = tweet.get("author", {}) or tweet.get("user", {})
        author_handle = (
            author.get("username")
            or author.get("screen_name", "")
            or tweet.get("author_handle", "")
        )

        engagement = {
            "likes": _first_of(tweet.get("likeCount"), tweet.get("like_count"), tweet.get("favorite_count")),
            "reposts": _first_of(tweet.get("retweetCount"), tweet.get("retweet_count")),
            "replies": _first_of(tweet.get("replyCount"), tweet.get("reply_count")),
            "quotes": _first_of(tweet.get("quoteCount"), tweet.get("quote_count")),
        }
        for key in engagement:
            if engagement[key] is not None:
                try:
                    engagement[key] = int(engagement[key])
                except (ValueError, TypeError):
                    engagement[key] = None

        text = str(tweet.get("text", tweet.get("full_text", ""))).strip()[:500]
        item = {
            "id": f"X{i + 1}",
            "text": text,
            "url": url,
            "author_handle": author_handle.lstrip("@"),
            "mentioned_handles": _leading_mentions(text),
            "date": parsed_date,
            "engagement": engagement if any(v is not None for v in engagement.values()) else None,
            "why_relevant": "",
            "relevance": _compute_relevance(query, str(tweet.get("text", ""))) if query else 0.7,
        }

        items.append(item)

    return items
