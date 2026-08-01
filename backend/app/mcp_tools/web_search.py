"""MCP: Web discovery and preview extraction (spec section 8.2.5).

Media types with no first-party API behind them (Editorial, and anything else
that falls through) are sourced from the open web. Three mechanisms, in the
order they're preferred:

1. a configured search provider (Tavily or Brave), when an API key exists;
2. DuckDuckGo's HTML endpoint, which needs no key — this is the default;
3. publisher RSS/Atom feeds, which are the most reliable source of *recent*
   items and always carry a real publication date.

Whatever the mechanism, a URL is only ever a lead. `extract_page_preview`
then fetches the page and reads its Open Graph tags, and a result is kept
only if that fetch succeeds and yields a usable image. That single rule is
what guarantees the two properties the curator promises: no broken links,
and no item without a preview.

Parsing uses the standard library (`html.parser`, `xml.etree`) so the
dependency set stays as-is.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse
from xml.etree import ElementTree

import httpx

from app.config import get_settings

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0 Safari/537.36 IABTM-Curator/1.0 (+content curation for personal growth)"
)
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


# ─── URL safety ────────────────────────────────────────────────────────────────

def is_public_http_url(url: str) -> bool:
    """Reject anything that isn't a plain public http(s) URL.

    Also keeps server-side fetches away from loopback and link-local
    addresses, since the URLs here come from third-party search results.
    """
    if not url or len(url) > 2048:
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host or host in _BLOCKED_HOSTS:
        return False
    return not (host.endswith(".local") or host.startswith("192.168.") or host.startswith("169.254."))


# ─── Page preview extraction ───────────────────────────────────────────────────

class _MetadataParser(HTMLParser):
    """Collects <meta> properties, <title>, and the first <link rel=image_src>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.link_image = ""
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key and values.get("content") and key not in self.meta:
                self.meta[key] = values["content"].strip()
        elif tag == "title" and not self.title:
            self._in_title = True
        elif tag == "link" and not self.link_image:
            if "image_src" in values.get("rel", "").lower():
                self.link_image = values.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def extract_page_preview(url: str) -> dict | None:
    """Fetch a page and return a verified preview, or None.

    Returning None is the normal outcome for paywalls, dead links, redirect
    loops, and pages with no share image — all of which the curator should
    silently skip rather than surface without a preview.
    """
    settings = get_settings()
    if not is_public_http_url(url):
        return None
    try:
        with httpx.Client(
            timeout=settings.curation_http_timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        ) as client:
            response = client.get(url)
    except httpx.HTTPError:
        return None

    if response.status_code != 200 or "text/html" not in response.headers.get("content-type", "").lower():
        return None

    final_url = str(response.url)
    if not is_public_http_url(final_url):
        return None

    parser = _MetadataParser()
    try:
        # Cap the parse: metadata lives in <head>, and some pages are enormous.
        parser.feed(response.text[:400_000])
    except Exception:
        return None

    image = (
        parser.meta.get("og:image")
        or parser.meta.get("og:image:url")
        or parser.meta.get("twitter:image")
        or parser.meta.get("twitter:image:src")
        or parser.link_image
    )
    image = urljoin(final_url, image) if image else ""
    if not is_public_http_url(image):
        return None

    return {
        "url": final_url,
        "title": unescape(parser.meta.get("og:title") or parser.title.strip())[:300],
        "description": unescape(
            parser.meta.get("og:description") or parser.meta.get("description", "")
        )[:1000],
        "thumbnail_url": image,
        "site_name": parser.meta.get("og:site_name", "") or (urlparse(final_url).hostname or ""),
        "published_at": parse_date(
            parser.meta.get("article:published_time")
            or parser.meta.get("article:modified_time")
            or parser.meta.get("datepublished")
        ),
    }


def extract_previews(urls: list[str]) -> list[dict]:
    """Preview several pages concurrently; network latency dominates here.

    Each preview carries `lead_url`, the URL it was requested by. Redirects
    and canonicalisation mean `url` often differs, and callers need the
    original to match a preview back to where the lead came from.
    """
    settings = get_settings()
    unique = list(dict.fromkeys(url for url in urls if url))
    if not unique:
        return []
    workers = min(settings.curation_max_workers, len(unique))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        previews = list(pool.map(extract_page_preview, unique))
    return [
        {**preview, "lead_url": lead}
        for lead, preview in zip(unique, previews)
        if preview
    ]


# Only these say the resource is genuinely gone. A 403/429/5xx means a bot
# defence or a bad minute at the edge — Flickr, for instance, answers 502 to
# an unrecognised user agent while serving the same page fine in a browser.
# Treating that as a dead link throws away good content and tells the user
# something untrue about it.
_DEAD_STATUSES = {404, 410}


def check_url(url: str) -> str:
    """Classify a URL as ``ok``, ``blocked``, or ``dead``.

    Three states rather than a boolean, because "we could not verify this"
    and "this does not exist" call for different decisions: the curator
    rejects the second and accepts the first.
    """
    settings = get_settings()
    if not is_public_http_url(url):
        return "dead"
    try:
        with httpx.Client(
            timeout=settings.curation_http_timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.head(url)
            # Plenty of CDNs and image hosts don't implement HEAD.
            if response.status_code in (403, 405, 501):
                response = client.get(url, headers={"Range": "bytes=0-2048"})
    except httpx.HTTPError:
        # DNS failure, refused connection, TLS failure: nothing is there.
        return "dead"
    if response.status_code in _DEAD_STATUSES:
        return "dead"
    return "ok" if response.status_code < 400 else "blocked"


def check_urls(urls: list[str]) -> dict[str, str]:
    """Classify many URLs concurrently, returning `{url: state}`."""
    settings = get_settings()
    unique = list(dict.fromkeys(url for url in urls if url))
    if not unique:
        return {}
    workers = min(settings.curation_max_workers, len(unique))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(zip(unique, pool.map(check_url, unique)))


def verify_url(url: str) -> bool:
    """True unless the URL is definitively gone."""
    return check_url(url) != "dead"


# ─── Search ────────────────────────────────────────────────────────────────────

class _DuckDuckGoParser(HTMLParser):
    """Pulls result links and snippets out of DuckDuckGo's HTML endpoint."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict] = []
        self._mode = ""
        self._href = ""
        self._buffer = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        values = {key.lower(): (value or "") for key, value in attrs}
        classes = values.get("class", "")
        if "result__a" in classes:
            self._mode, self._href, self._buffer = "title", values.get("href", ""), ""
        elif "result__snippet" in classes:
            self._mode, self._buffer = "snippet", ""

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._mode:
            return
        text = " ".join(self._buffer.split())
        if self._mode == "title":
            url = _decode_duckduckgo_href(self._href)
            if url:
                self.results.append({"url": url, "title": text, "snippet": ""})
        elif self._mode == "snippet" and self.results:
            self.results[-1]["snippet"] = text
        self._mode, self._buffer = "", ""

    def handle_data(self, data: str) -> None:
        if self._mode:
            self._buffer += data


def _decode_duckduckgo_href(href: str) -> str:
    """Unwrap DuckDuckGo's `/l/?uddg=<encoded target>` redirect links."""
    if not href:
        return ""
    if href.startswith("//"):
        href = f"https:{href}"
    parsed = urlparse(href)
    if "duckduckgo.com" in (parsed.hostname or "") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return target if is_public_http_url(target) else ""
    return href if is_public_http_url(href) else ""


# Maps "within N days" onto the coarse freshness buckets these engines accept.
_FRESHNESS_BUCKETS = [(2, "d"), (10, "w"), (45, "m"), (400, "y")]


def _freshness_code(recency_days: int | None) -> str:
    if not recency_days:
        return ""
    return next((code for limit, code in _FRESHNESS_BUCKETS if recency_days <= limit), "y")


def duckduckgo_search(query: str, max_results: int = 10, recency_days: int | None = None) -> list[dict]:
    """Keyless web search by scraping DuckDuckGo's HTML endpoint."""
    settings = get_settings()
    params = {"q": query, "kl": "wt-wt"}
    code = _freshness_code(recency_days)
    if code:
        params["df"] = code
    try:
        response = httpx.post(
            "https://html.duckduckgo.com/html/",
            data=params,
            timeout=settings.curation_http_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
                "Referer": "https://duckduckgo.com/",
            },
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    parser = _DuckDuckGoParser()
    try:
        parser.feed(response.text)
    except Exception:
        return []
    return parser.results[:max_results]


def provider_search(query: str, max_results: int = 10, recency_days: int | None = None) -> list[dict]:
    """Tavily or Brave, when an API key is configured."""
    settings = get_settings()
    if not settings.web_search_configured:
        return []
    provider = settings.web_search_provider.lower()
    limit = min(max(max_results, 1), 20)
    timeout = settings.curation_http_timeout + 5
    try:
        if provider == "tavily":
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.web_search_api_key,
                    "query": query,
                    "max_results": limit,
                    "search_depth": "basic",
                    **({"days": recency_days} if recency_days else {}),
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return [
                {"url": item.get("url", ""), "title": item.get("title", ""), "snippet": item.get("content", "")}
                for item in response.json().get("results", [])
            ]
        if provider == "brave":
            brave_freshness = {"d": "pd", "w": "pw", "m": "pm", "y": "py"}.get(_freshness_code(recency_days), "")
            response = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": limit, **({"freshness": brave_freshness} if brave_freshness else {})},
                headers={"Accept": "application/json", "X-Subscription-Token": settings.web_search_api_key},
                timeout=timeout,
            )
            response.raise_for_status()
            return [
                {"url": item.get("url", ""), "title": item.get("title", ""), "snippet": item.get("description", "")}
                for item in response.json().get("web", {}).get("results", [])
            ]
    except httpx.HTTPError:
        return []
    return []


def web_search(query: str, max_results: int = 10, recency_days: int | None = None) -> list[dict]:
    """Search leads for `query`, preferring a configured provider."""
    results = provider_search(query, max_results, recency_days)
    if not results:
        results = duckduckgo_search(query, max_results, recency_days)
    return [result for result in results if is_public_http_url(result.get("url", ""))]


# ─── Feeds ─────────────────────────────────────────────────────────────────────

def fetch_feed(feed_url: str, limit: int = 15) -> list[dict]:
    """Read an RSS or Atom feed into `{url, title, snippet, published_at}` entries.

    Feeds are the only source here that reliably reports a real publication
    date, which is what makes "latest" meaningful rather than guessed.
    """
    settings = get_settings()
    try:
        response = httpx.get(
            feed_url,
            timeout=settings.curation_http_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            },
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
    except (httpx.HTTPError, ElementTree.ParseError):
        return []

    entries: list[dict] = []
    for item in root.iter():
        if item.tag.split("}")[-1] not in ("item", "entry"):
            continue
        link = _feed_link(item)
        if not is_public_http_url(link):
            continue
        entries.append({
            "url": link,
            "title": unescape((_feed_text(item, "title") or "").strip())[:300],
            "snippet": unescape(
                (_feed_text(item, "description") or _feed_text(item, "summary") or "").strip()
            )[:500],
            "published_at": parse_date(
                _feed_text(item, "pubDate") or _feed_text(item, "published") or _feed_text(item, "updated")
            ),
        })
        if len(entries) >= limit:
            break
    return entries


def fetch_feeds(feed_urls: list[str], limit_per_feed: int = 10) -> list[dict]:
    """Read several feeds concurrently and flatten the entries."""
    settings = get_settings()
    if not feed_urls:
        return []
    workers = min(settings.curation_max_workers, len(feed_urls))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        batches = list(pool.map(lambda url: fetch_feed(url, limit_per_feed), feed_urls))
    return [entry for batch in batches for entry in batch]


_SEARCH_STOPWORDS = {
    "the", "and", "for", "with", "your", "from", "that", "this", "have", "how",
    "one", "into", "about", "guide", "based", "evidence", "month", "finish",
    "best", "some", "more", "what", "when", "will", "make",
}


def keyword_query(query: str, max_words: int = 4) -> str:
    """Reduce a natural-language query to keywords a site search can match.

    WordPress search is an AND over the terms given, so passing a whole
    sentence — "learning techniques deep reading and study skills evidence
    based guide" — matches no post at all. The few most substantial words
    match the right ones.
    """
    words = [
        word.strip(".,:;!?\"'")
        for word in query.lower().replace("-", " ").split()
    ]
    keywords = [word for word in words if len(word) > 3 and word not in _SEARCH_STOPWORDS]
    return " ".join(keywords[:max_words]) or query.strip()


def search_site_feeds(hosts: list[str], query: str, limit_per_site: int = 6) -> list[dict]:
    """Query publishers directly through their own search feeds.

    Most editorial sites on WordPress expose `?s=<query>&feed=rss2`, which
    returns that site's search results as RSS. That makes it possible to run a
    *keyword* search across curated publishers without a search API key and
    without scraping an engine that captcha-gates automated traffic — which,
    on many networks, is all of them.

    Unsupported sites answer with HTML or an empty channel; both come back as
    no entries, so an unusable host costs one request and nothing else.
    """
    if not hosts or not query.strip():
        return []
    encoded = quote_plus(keyword_query(query))
    urls = [f"https://{host}/?s={encoded}&feed=rss2" for host in hosts]
    return fetch_feeds(urls, limit_per_feed=limit_per_site)


def _feed_text(element, name: str) -> str:
    for child in element:
        if child.tag.split("}")[-1] == name and child.text:
            return child.text
    return ""


def _feed_link(element) -> str:
    for child in element:
        if child.tag.split("}")[-1] != "link":
            continue
        # RSS puts the URL in the element text; Atom puts it in @href.
        href = (child.get("href") or "").strip()
        if href and child.get("rel", "alternate") == "alternate":
            return href
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def parse_date(raw: str | None) -> str:
    """Normalise a feed/meta date to an ISO-8601 UTC string; '' when unknown."""
    if not raw:
        return ""
    text = raw.strip()
    try:
        return parsedate_to_datetime(text).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except ValueError:
        return ""


def extract_article(url: str) -> str:
    preview = extract_page_preview(url)
    return preview["description"] if preview else ""
