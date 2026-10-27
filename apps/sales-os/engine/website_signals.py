# apps/sales-os/engine/website_signals.py
"""Website-Text (hoeflich, SSRF-gehaertet, mit Cache) und woertliche Signale fuer den Fit-Score."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

from bounce_rescue_agent import build_public_opener
from lead_quality import NEGATIVE_RE, POSITIVE_RE

USER_AGENT = "HSB-SalesOS-Research/1.0 (+https://hsb-boden.com)"
MAX_BYTES = 2 * 1024 * 1024
TOTAL_SECONDS = 20.0
MIN_INTERVAL = 1.0
TRANSIENT_TTL_SECONDS = 7 * 24 * 3600
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "website_cache"

_SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript"}
_last_request = [None]  # Zeitpunkt der letzten Anfrage (Rate-Limit 1/s, prozessweit)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def html_to_text(markup: str) -> str:
    parser = _TextExtractor()
    parser.feed(markup)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def _normalize(url: str) -> tuple[str, str] | None:
    url = (url or "").strip()
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not host:
        return None
    host = host[4:] if host.startswith("www.") else host
    return url, host


def _cache_path(cache_dir: Path, domain: str) -> Path:
    return Path(cache_dir) / (re.sub(r"[^a-z0-9.-]", "_", domain) + ".txt")


def cached_website_text(url: str, cache_dir: Path) -> str | None:
    """Nur Cache, kein Netz."""
    norm = _normalize(url)
    if not norm:
        return None
    path = _cache_path(cache_dir, norm[1])
    return path.read_text(encoding="utf-8") if path.exists() else None


class _Skip(Exception):
    def __init__(self, reason: str, permanent: bool, code: int | None = None):
        super().__init__(reason)
        self.reason, self.permanent, self.code = reason, permanent, code


def _skip_path(cache_dir: Path, domain: str) -> Path:
    return _cache_path(cache_dir, domain).with_suffix(".skip")


def skip_state(url: str, cache_dir: Path, wall: Callable[[], float] = time.time) -> dict | None:
    """Aktiver Negativ-Marker (dauerhaft oder transient innerhalb der TTL) oder None. Zaehlt nie als Text-Treffer."""
    norm = _normalize(url)
    if not norm:
        return None
    path = _skip_path(cache_dir, norm[1])
    if not path.exists():
        return None
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    if info.get("permanent") or wall() - float(info.get("ts", 0)) < TRANSIENT_TTL_SECONDS:
        return info
    return None


def _write_skip(cache_dir: Path, domain: str, reason: str, permanent: bool, wall: Callable[[], float]) -> None:
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    _skip_path(cache_dir, domain).write_text(
        json.dumps({"reason": reason, "permanent": permanent, "ts": wall()}), encoding="utf-8")


def _bare_host(url: str) -> str:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def website_text(url: str, cache_dir: Path, opener=None, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, wall: Callable[[], float] = time.time) -> str | None:
    """Startseitentext oder None. Ein Cache-File je Domain; Misserfolge als `<domain>.skip` (Grund, Zeit).

    Dauerhaft: robots, 4xx, non_text, empty, cross_host_redirect. Transient (7 Tage TTL): Timeout, 5xx, Netzfehler.
    """
    norm = _normalize(url)
    if not norm:
        return None
    url, domain = norm
    path = _cache_path(cache_dir, domain)
    if path.exists():
        return path.read_text(encoding="utf-8")
    if skip_state(url, cache_dir, wall):
        return None
    opener = opener or build_public_opener()
    start = clock()
    deadline = start + TOTAL_SECONDS

    def get(target: str, check: Callable[[str], None] | None = None, textual: bool = True) -> bytes:
        last = _last_request[0]
        if last is not None and clock() - last < MIN_INTERVAL:
            sleep(MIN_INTERVAL - (clock() - last))
        remaining = deadline - clock()
        if remaining <= 0:
            raise _Skip("timeout", False)
        _last_request[0] = clock()
        req = urllib.request.Request(target, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.8"})
        try:
            with opener.open(req, timeout=remaining) as resp:
                status = getattr(resp, "status", 200)
                if status >= 400:
                    raise urllib.error.HTTPError(target, status, "error", None, None)
                if check:
                    check(getattr(resp, "geturl", lambda: target)())
                headers = getattr(resp, "headers", None)
                ctype = (headers.get("Content-Type", "") if headers else "").lower()
                if textual and "text/html" not in ctype and "text/plain" not in ctype:
                    raise _Skip("non_text", True)
                read_chunk = getattr(resp, "read1", resp.read)
                chunks: list[bytes] = []
                size = 0
                while True:
                    if clock() > deadline:
                        raise _Skip("timeout", False)
                    chunk = read_chunk(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > MAX_BYTES:
                        break
                return b"".join(chunks)[:MAX_BYTES]
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise _Skip("http_4xx", True, exc.code)
            raise _Skip(f"http_{exc.code}", False)
        except (OSError, TimeoutError, ValueError) as exc:
            raise _Skip(type(exc).__name__, False)

    try:
        origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
        robots = urllib.robotparser.RobotFileParser()
        try:
            robots.parse(get(origin + "/robots.txt", textual=False).decode("utf-8", "replace").splitlines())
        except _Skip as exc:
            if exc.code in (401, 403):
                raise _Skip("robots", True)
            if exc.code is None:
                raise
            robots.parse([])  # uebrige 4xx: keine robots.txt, alles erlaubt
        if not robots.can_fetch(USER_AGENT, url):
            raise _Skip("robots", True)

        def check(final: str) -> None:
            if _bare_host(final) != _bare_host(url):
                raise _Skip("cross_host_redirect", True)
            if final != url and not robots.can_fetch(USER_AGENT, final):
                raise _Skip("robots", True)

        body = get(url, check)
    except _Skip as exc:
        _write_skip(cache_dir, domain, exc.reason, exc.permanent, wall)
        return None
    text = html_to_text(body.decode("utf-8", "replace")) if body else ""
    if not text:
        _write_skip(cache_dir, domain, "empty", True, wall)
        return None
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def _snippet(text: str, start: int, end: int, radius: int = 80) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return text[a:b].strip()


def website_signals(text: str) -> dict:
    """Positive/negative Schluesselwoerter plus woertliche Fundstellen (Teilstrings des Textes)."""
    out = {"positive": [], "negative": [], "quotes": []}
    for key, rx in (("positive", POSITIVE_RE), ("negative", NEGATIVE_RE)):
        for m in rx.finditer(text or ""):
            word = m.group(1).lower()
            if word not in out[key]:
                out[key].append(word)
                out["quotes"].append(_snippet(text, m.start(), m.end()))
    return out
