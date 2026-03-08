"""
HTTP client helpers with connection pooling, retries and response size limits.
"""
from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_USER_AGENT = "HoloRSSReader/1.0 (+https://github.com/helebest/holo-rss-reader)"


@dataclass
class HTTPResult:
    ok: bool
    status_code: Optional[int] = None
    text: str = ""
    data: Optional[Any] = None
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    error_kind: Optional[str] = None


def make_timeout(connect_timeout_sec: int, read_timeout_sec: int) -> Tuple[int, int]:
    return (max(1, int(connect_timeout_sec)), max(1, int(read_timeout_sec)))


def build_session(retries: int = 3, pool_connections: int = 20, pool_maxsize: int = 20) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=max(0, int(retries)),
        read=max(0, int(retries)),
        connect=max(0, int(retries)),
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_connections, pool_maxsize=pool_maxsize)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _decode_body(raw_bytes: bytes, encoding: str) -> str:
    try:
        return raw_bytes.decode(encoding, errors="replace")
    except LookupError:
        return raw_bytes.decode("utf-8", errors="replace")


def _detect_encoding_from_body(raw_bytes: bytes) -> Optional[str]:
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw_bytes.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    if raw_bytes.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    if raw_bytes.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw_bytes.startswith(b"\xfe\xff"):
        return "utf-16-be"

    head = raw_bytes[:4096].decode("ascii", errors="ignore")

    xml_match = re.search(r"<\?xml[^>]*encoding=[\"']\s*([^\"']+)", head, re.IGNORECASE)
    if xml_match:
        return xml_match.group(1).strip()

    meta_match = re.search(r"<meta[^>]+charset=[\"']?\s*([^\"'\s/>]+)", head, re.IGNORECASE)
    if meta_match:
        return meta_match.group(1).strip()

    return None


def _resolve_encoding(response: requests.Response, raw_bytes: bytes) -> str:
    return response.encoding or _detect_encoding_from_body(raw_bytes) or "utf-8"


def fetch_text(
    url: str,
    *,
    session: Optional[requests.Session] = None,
    timeout: Tuple[int, int] = (5, 20),
    max_bytes: int = 2 * 1024 * 1024,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPResult:
    req_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        req_headers.update(headers)

    own_session = session is None
    sess = session or build_session()

    try:
        response = sess.get(url, stream=True, timeout=timeout, headers=req_headers)
        status_code = response.status_code
        response_headers = {k.lower(): v for k, v in response.headers.items()}

        if status_code == 304:
            response.close()
            return HTTPResult(ok=True, status_code=304, headers=response_headers)

        if status_code >= 400:
            err = f"HTTP {status_code}"
            response.close()
            return HTTPResult(
                ok=False,
                status_code=status_code,
                headers=response_headers,
                error=err,
                error_kind="network",
            )

        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                response.close()
                return HTTPResult(
                    ok=False,
                    status_code=status_code,
                    headers=response_headers,
                    error=f"Response exceeds max size ({max_bytes} bytes)",
                    error_kind="network",
                )
            chunks.append(chunk)

        body = b"".join(chunks)
        encoding = _resolve_encoding(response, body)
        response.close()
        return HTTPResult(
            ok=True,
            status_code=status_code,
            text=_decode_body(body, encoding),
            headers=response_headers,
        )
    except requests.RequestException as exc:
        return HTTPResult(ok=False, error=f"Network error: {exc}", error_kind="network")
    finally:
        if own_session:
            sess.close()


def fetch_json(
    url: str,
    *,
    session: Optional[requests.Session] = None,
    timeout: Tuple[int, int] = (5, 20),
    max_bytes: int = 2 * 1024 * 1024,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPResult:
    result = fetch_text(url, session=session, timeout=timeout, max_bytes=max_bytes, headers=headers)
    if not result.ok:
        return result

    try:
        result.data = json.loads(result.text)
        return result
    except json.JSONDecodeError as exc:
        return HTTPResult(
            ok=False,
            status_code=result.status_code,
            headers=result.headers,
            error=f"JSON parse error: {exc}",
            error_kind="parse",
        )
