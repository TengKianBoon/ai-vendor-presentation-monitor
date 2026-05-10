from __future__ import annotations

import datetime as dt
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from .config import official_domains
from .credibility import is_vendor_domain
from .models import Candidate, SourceConfig
from .normalize import canonical_url, clean_text

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
DIRECT_MEDIA_EXTENSIONS = (".mp3", ".m4a", ".wav", ".flac", ".aac", ".mp4", ".mov", ".webm")
LOW_VALUE_LINK_TITLES = {
    "availability",
    "contact us",
    "docs",
    "documentation",
    "events",
    "home",
    "learn more",
    "learn more about this event",
    "learn more about this webinar",
    "log in",
    "pricing",
    "read more",
    "register",
    "sign in",
    "try chatgpt",
    "watch now",
}
LOW_VALUE_TITLE_PHRASES = (
    "log in try",
    "research products business",
    "skip to content",
)


def parse_iso_duration(value: str) -> int:
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not match:
        return 0
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def youtube_get(endpoint: str, params: dict[str, Any], api_key: str) -> dict[str, Any]:
    response = requests.get(f"{YOUTUBE_API}/{endpoint}", params={**params, "key": api_key}, timeout=30)
    response.raise_for_status()
    return response.json()


def resolve_youtube_channel(source: SourceConfig, api_key: str) -> str | None:
    if source.channel_id:
        return source.channel_id
    if not source.handle:
        return None
    handle = source.handle.lstrip("@")
    data = youtube_get("channels", {"part": "id", "forHandle": handle}, api_key)
    items = data.get("items", [])
    if items:
        return items[0]["id"]
    return None


def uploads_playlist(channel_id: str, api_key: str) -> str | None:
    data = youtube_get("channels", {"part": "contentDetails", "id": channel_id}, api_key)
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def playlist_video_ids(playlist_id: str, since: dt.datetime, api_key: str, max_pages: int = 2) -> list[str]:
    video_ids: list[str] = []
    page_token: str | None = None
    for _ in range(max_pages):
        params = {"part": "contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        data = youtube_get("playlistItems", params, api_key)
        for item in data.get("items", []):
            published = item["contentDetails"].get("videoPublishedAt")
            if not published:
                continue
            published_at = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
            if published_at < since:
                return video_ids
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return video_ids


def hydrate_youtube_videos(video_ids: list[str], api_key: str) -> list[dict[str, Any]]:
    hydrated: list[dict[str, Any]] = []
    for index in range(0, len(video_ids), 50):
        batch = video_ids[index : index + 50]
        data = youtube_get("videos", {"part": "snippet,contentDetails", "id": ",".join(batch)}, api_key)
        hydrated.extend(data.get("items", []))
    return hydrated


def discover_youtube(source: SourceConfig, api_key: str, since: dt.datetime) -> list[Candidate]:
    channel_id = resolve_youtube_channel(source, api_key)
    if not channel_id:
        print(f"[WARN] Could not resolve YouTube channel for {source.name}", file=sys.stderr)
        return []
    playlist = uploads_playlist(channel_id, api_key)
    if not playlist:
        return []
    video_ids = playlist_video_ids(playlist, since, api_key)
    candidates: list[Candidate] = []
    for item in hydrate_youtube_videos(video_ids, api_key):
        snippet = item["snippet"]
        video_id = item["id"]
        candidates.append(
            Candidate(
                vendor=source.vendor,
                title=clean_text(unescape(snippet.get("title", ""))),
                url=f"https://www.youtube.com/watch?v={video_id}",
                source_type="youtube",
                source_name=source.name,
                source_proof=source.proof,
                platform="youtube",
                platform_id=video_id,
                published_at=snippet.get("publishedAt", ""),
                description=clean_text(snippet.get("description", "")),
                duration_seconds=parse_iso_duration(item.get("contentDetails", {}).get("duration", "")),
                transcript_status="unavailable",
                transcript_confidence="none",
            )
        )
    return candidates


def nearby_text(link) -> str:
    pieces = [link.get_text(" ", strip=True)]
    for parent in link.parents:
        if getattr(parent, "name", "") in {"li", "article", "section", "div"}:
            pieces.append(parent.get_text(" ", strip=True))
            break
    return clean_text(" ".join(pieces))


def direct_media_url(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return any(path.endswith(ext) for ext in DIRECT_MEDIA_EXTENSIONS)


def low_value_event_link_title(title: str) -> bool:
    normalized = clean_text(title).lower()
    if normalized in LOW_VALUE_LINK_TITLES:
        return True
    if normalized.startswith(("learn more", "read more", "register now")):
        return True
    return any(phrase in normalized for phrase in LOW_VALUE_TITLE_PHRASES)


def discover_event_page(source: SourceConfig, config: dict[str, Any]) -> list[Candidate]:
    if not source.url:
        return []
    response = requests.get(source.url, timeout=30, headers={"User-Agent": "ai-vendor-monitor/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    page_title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else source.name)
    domains = official_domains(config, source.vendor)
    candidates: list[Candidate] = []
    seen_urls: set[str] = set()

    page_candidate = Candidate(
        vendor=source.vendor,
        title=page_title,
        url=canonical_url(source.url),
        source_type="event_page",
        source_name=source.name,
        source_proof=source.proof,
        description=clean_text(soup.get_text(" ", strip=True)[:1500]),
    )
    candidates.append(page_candidate)
    seen_urls.add(page_candidate.url)

    for link in soup.find_all("a", href=True):
        absolute = canonical_url(urljoin(source.url, link["href"]))
        if absolute in seen_urls:
            continue
        if not is_vendor_domain(absolute, domains):
            continue
        text = nearby_text(link)
        if not text:
            continue
        media_url = absolute if direct_media_url(absolute) else ""
        title = clean_text(link.get_text(" ", strip=True) or text[:120])
        if low_value_event_link_title(title) and not media_url:
            continue
        candidates.append(
            Candidate(
                vendor=source.vendor,
                title=title,
                url=absolute,
                source_type="event_page",
                source_name=source.name,
                source_proof=source.proof,
                description=text[:1500],
                media_url=media_url,
            )
        )
        seen_urls.add(absolute)
    return candidates


def discover_all(
    sources: list[SourceConfig],
    config: dict[str, Any],
    youtube_api_key: str | None,
    since: dt.datetime,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for source in sources:
        try:
            if source.kind == "youtube":
                if not youtube_api_key:
                    print(f"[INFO] Skipping {source.name}: YOUTUBE_API_KEY not set")
                    continue
                candidates.extend(discover_youtube(source, youtube_api_key, since))
            elif source.kind == "event_page":
                candidates.extend(discover_event_page(source, config))
        except requests.RequestException as exc:
            print(f"[WARN] Source failed: {source.name}: {exc}", file=sys.stderr)
    return candidates
