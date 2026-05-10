from __future__ import annotations

import datetime as dt

from .classifier import is_key_presentation
from .config import source_configs, vendor_speakers
from .credibility import verify_candidate
from .dedupe import is_duplicate
from .models import Candidate, MonitorResult
from .sources import discover_all
from .storage import load_items


def utc_since(days: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)


def select_new_items(
    candidates: list[Candidate],
    config: dict,
    existing: list[dict],
) -> MonitorResult:
    accepted: list[Candidate] = []
    new_items: list[Candidate] = []
    rejected: list[tuple[Candidate, str]] = []
    threshold = int(config.get("settings", {}).get("fuzzy_title_threshold", 92))

    for candidate in candidates:
        candidate.speakers = detect_speakers(candidate, config)
        credible, credibility_reason = verify_candidate(candidate, config)
        if not credible:
            rejected.append((candidate, credibility_reason))
            continue
        key, key_reason = is_key_presentation(candidate, config)
        if not key:
            rejected.append((candidate, key_reason))
            continue
        accepted.append(candidate)
        duplicate, duplicate_reason = is_duplicate(candidate, existing, new_items, threshold=threshold)
        if duplicate:
            rejected.append((candidate, duplicate_reason))
            continue
        new_items.append(candidate)

    return MonitorResult(discovered=candidates, accepted=accepted, new_items=new_items, rejected=rejected)


def detect_speakers(candidate: Candidate, config: dict) -> list[str]:
    haystack = f"{candidate.title}\n{candidate.description}".lower()
    detected: list[str] = []
    for speaker in vendor_speakers(config, candidate.vendor):
        if speaker.lower() in haystack:
            detected.append(speaker)
    return detected


def run_discovery(config: dict, youtube_api_key: str | None, lookback_days: int) -> MonitorResult:
    candidates = discover_all(source_configs(config), config, youtube_api_key, utc_since(lookback_days))
    return select_new_items(candidates, config, load_items())
