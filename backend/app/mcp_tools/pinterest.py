"""Pinterest board ingestion for visual Art recommendations.

Pinterest's API is account/board based rather than a public image-search API.
This client reads Pins from the configured board and keeps credentials on the
server. An explicitly supplied access token is preferred; otherwise it obtains
an app token with the configured client credentials.
"""

from datetime import datetime, timezone

import httpx

from app.config import get_settings

API_BASE = "https://api.pinterest.com/v5"


def _access_token() -> str:
    settings = get_settings()
    if settings.pinterest_access_token:
        return settings.pinterest_access_token
    if not (settings.pinterest_client_id and settings.pinterest_client_secret):
        raise RuntimeError("Pinterest credentials are not configured.")
    response = httpx.post(
        f"{API_BASE}/oauth/token",
        auth=(settings.pinterest_client_id, settings.pinterest_client_secret),
        data={"grant_type": "client_credentials", "scope": "boards:read,pins:read"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_board_pins(limit: int = 25) -> list[dict]:
    """Return normalised Pins from the configured Pinterest board."""
    settings = get_settings()
    if not settings.pinterest_configured:
        return []

    response = httpx.get(
        f"{API_BASE}/boards/{settings.pinterest_board_id}/pins",
        headers={"Authorization": f"Bearer {_access_token()}"},
        params={"page_size": min(max(limit, 1), 100)},
        timeout=15,
    )
    response.raise_for_status()
    pins = []
    for pin in response.json().get("items", []):
        images = pin.get("media", {}).get("images", {})
        image = images.get("1200x", {}).get("url") or images.get("600x", {}).get("url")
        if not image and images:
            image = next(iter(images.values())).get("url", "")
        pin_id = str(pin.get("id", ""))
        if not pin_id:
            continue
        pins.append({
            "pin_id": pin_id,
            "title": pin.get("title") or pin.get("description") or "Pinterest inspiration",
            "description": pin.get("description") or "Curated from your Pinterest board.",
            "image_url": image or "",
            "url": f"https://www.pinterest.com/pin/{pin_id}/",
            "published_at": pin.get("created_at") or datetime.now(timezone.utc).isoformat(),
        })
    return pins
