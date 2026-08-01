"""Spotify catalogue search for curated Music recommendations.

Uses the server-side Client Credentials flow. No Spotify credential is sent to
the browser; the browser only receives public Spotify track URLs for playback
in Spotify's own embedded player.
"""

import threading
import time
from datetime import datetime, timezone

import httpx

from app.config import get_settings

_token = ""
_token_expires_at = 0.0
_token_lock = threading.Lock()


def _access_token() -> str:
    global _token, _token_expires_at
    settings = get_settings()
    if not settings.spotify_configured:
        raise RuntimeError("Spotify credentials are not configured.")
    with _token_lock:
        if _token and time.time() < _token_expires_at:
            return _token
        response = httpx.post(
            "https://accounts.spotify.com/api/token",
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        _token = data["access_token"]
        _token_expires_at = time.time() + int(data.get("expires_in", 3600)) - 60
        return _token


def search_tracks(query: str, max_results: int = 6) -> list[dict]:
    """Search Spotify's public track catalogue in the configured market."""
    settings = get_settings()
    if not settings.spotify_configured:
        return []
    response = httpx.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {_access_token()}"},
        params={
            "q": query, "type": "track", "limit": min(max(max_results, 1), 10),
            "market": settings.spotify_market,
        },
        timeout=15,
    )
    response.raise_for_status()
    tracks = []
    for track in response.json().get("tracks", {}).get("items", []):
        track_id = track.get("id")
        if not track_id:
            continue
        artists = ", ".join(artist["name"] for artist in track.get("artists", []))
        album = track.get("album", {})
        image = next((image.get("url", "") for image in album.get("images", []) if image.get("url")), "")
        tracks.append({
            "track_id": track_id,
            "title": track.get("name", "Untitled track"),
            "description": f"{artists} · {album.get('name', 'Spotify')}",
            "thumbnail_url": image,
            "url": track.get("external_urls", {}).get("spotify", f"https://open.spotify.com/track/{track_id}"),
            "duration_seconds": max(1, int(track.get("duration_ms", 0)) // 1000),
            "published_at": datetime.now(timezone.utc).isoformat(),
        })
    return tracks
