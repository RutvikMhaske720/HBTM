"""MCP: Open Library search — the source behind curated Print.

Keyless, and every hit resolves to a stable `openlibrary.org/works/...` page.
Only editions with a cover image are returned: a book with no cover has no
preview, and the curator does not surface previewless items.
"""

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.mcp_tools.web_search import USER_AGENT

SEARCH_URL = "https://openlibrary.org/search.json"
FIELDS = "key,title,author_name,first_publish_year,cover_i,subject,ebook_access"


def search_books(query: str, max_results: int = 10, subject: str = "") -> list[dict]:
    """Search Open Library, preferring a subject heading over free text.

    Two things about this index shape the approach:

    * `subject=` is dramatically better than `q=` here. Searching the subject
      heading "study skills" returns *Make It Stick* and *How to Study*; the
      same intent as free text returns *Macbeth* and *Heart of Darkness*,
      because `q` is title-weighted and a goal phrased in natural language
      matches almost nothing.
    * Neither `sort=new` nor `sort=rating` helps. The first orders by when the
      catalogue record was created, surfacing obscure recent uploads; the
      second is raw popularity, which puts *The Hunger Games* at the top of a
      search about learning. Relevance order is what serves a reader.
    """
    settings = get_settings()
    common = {
        "limit": min(max(max_results, 1) * 3, 40),  # over-fetch; many lack covers
        "fields": FIELDS,
        "lang": "eng",
    }
    attempts = []
    if subject:
        attempts.append({"subject": subject, **common})
    attempts.append({"q": _searchable(query), **common})

    docs: list[dict] = []
    for params in attempts:
        try:
            response = httpx.get(
                SEARCH_URL,
                params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=settings.curation_http_timeout + 5,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            continue
        docs = response.json().get("docs", [])
        if docs:
            break

    books = []
    for doc in docs:
        cover_id = doc.get("cover_i")
        key = doc.get("key", "")
        if not cover_id or not key.startswith("/works/"):
            continue
        authors = ", ".join(doc.get("author_name", [])[:3]) or "Unknown author"
        year = doc.get("first_publish_year")
        subjects = ", ".join(doc.get("subject", [])[:6])
        books.append({
            "work_id": key.strip("/").replace("/", "-"),
            "title": (doc.get("title") or "Untitled").strip()[:300],
            "description": " · ".join(part for part in [authors, str(year) if year else "", subjects] if part)[:500],
            "thumbnail_url": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg",
            "url": f"https://openlibrary.org{key}",
            "published_at": _published_at(year),
        })
        if len(books) >= max_results:
            break
    return books


_STOPWORDS = {
    "the", "and", "for", "with", "your", "from", "that", "this", "have", "how",
    "one", "into", "about", "guide", "based", "evidence", "month", "finish",
}


def _searchable(query: str) -> str:
    """Trim a natural-language query down to terms a book index can match."""
    words = [
        word for word in query.lower().replace("-", " ").split()
        if len(word) > 3 and word not in _STOPWORDS
    ]
    return " ".join(words[:6]) or query.strip()


def _published_at(year: int | None) -> str:
    """Books have a publication year at best; treat it as 1 January."""
    if not year or year < 1000 or year > datetime.now(timezone.utc).year:
        return ""
    return datetime(year, 1, 1, tzinfo=timezone.utc).isoformat()
