# apps/sales-os/engine/website_signals.py
"""Website-Text (hoeflich, SSRF-gehaertet, mit Cache) und woertliche Signale fuer den Fit-Score."""
from __future__ import annotations

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


def website_text(url: str, cache_dir: Path, opener=None, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> str | None:
    """Startseitentext oder None (robots.txt verbietet, Fehler, kein Text). Ein Cache-File je Domain."""
    norm = _normalize(url)
    if not norm:
        return None
    url, domain = norm
    path = _cache_path(cache_dir, domain)
    if path.exists():
        return path.read_text(encoding="utf-8")
    opener = opener or build_public_opener()
    start = clock()

    def get(target: str) -> bytes | None:
        """Eine Anfrage unter Rate-Limit und Gesamtbudget; HTTP-Fehler als None, andere Fehler propagieren."""
        last = _last_request[0]
        if last is not None and clock() - last < MIN_INTERVAL:
            sleep(MIN_INTERVAL - (clock() - last))
        remaining = TOTAL_SECONDS - (clock() - start)
        if remaining <= 0:
            raise TimeoutError("website_text: 20 s Budget erschoepft")
        _last_request[0] = clock()
        req = urllib.request.Request(target, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.8"})
        try:
            with opener.open(req, timeout=remaining) as resp:
                status = getattr(resp, "status", 200)
                if status >= 400:
                    raise urllib.error.HTTPError(target, status, "error", None, None)
                return resp.read(MAX_BYTES + 1)[:MAX_BYTES]
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                return None
            raise

    try:
        origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
        robots = urllib.robotparser.RobotFileParser()
        raw = get(origin + "/robots.txt")
        if raw is None:
            robots.parse([])  # 4xx: alles erlaubt
        else:
            robots.parse(raw.decode("utf-8", "replace").splitlines())
        if not robots.can_fetch(USER_AGENT, url):
            return None
        body = get(url)
    except (OSError, TimeoutError, ValueError):
        return None
    if not body:
        return None
    text = html_to_text(body.decode("utf-8", "replace"))
    if not text:
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
