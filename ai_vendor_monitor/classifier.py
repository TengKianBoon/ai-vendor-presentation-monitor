from __future__ import annotations

from .models import Candidate
from .normalize import normalize_title


DEFAULT_KEEP_KEYWORDS = {
    "aipcon",
    "agent",
    "agentforce",
    "ai",
    "briefing",
    "claude",
    "conference",
    "demo",
    "developer day",
    "devday",
    "dreamforce",
    "event",
    "keynote",
    "langchain",
    "langgraph",
    "launch",
    "model",
    "on-demand",
    "presentation",
    "product",
    "qwen",
    "recording",
    "release",
    "technical",
    "webinar",
}

DEFAULT_REJECT_KEYWORDS = {
    "reaction",
    "rumor",
    "unofficial",
    "fan",
    "mirror",
    "reupload",
    "re-upload",
    "stock analysis",
    "price target",
}

DEFAULT_EVENT_PRESENTATION_KEYWORDS = {
    "aipcon",
    "briefing",
    "conference",
    "demo",
    "developer day",
    "devday",
    "dreamforce",
    "keynote",
    "launch",
    "on-demand",
    "presentation",
    "recording",
    "release",
    "session",
    "summit",
    "talk",
    "technical demo",
    "webinar",
}

GENERIC_EVENT_TITLES = {
    "availability",
    "events",
    "haiku",
    "home",
    "learn more",
    "learn more about this event",
    "learn more about this webinar",
}


def is_key_presentation(candidate: Candidate, config: dict) -> tuple[bool, str]:
    settings = config.get("settings", {})
    if candidate.duration_seconds is not None:
        min_duration = int(settings.get("min_duration_seconds", 300))
        max_duration = int(settings.get("max_duration_seconds", 14400))
        if candidate.duration_seconds < min_duration:
            return False, "too short for a key presentation"
        if candidate.duration_seconds > max_duration:
            return False, "too long for the configured presentation window"

    haystack = normalize_title(f"{candidate.title} {candidate.description}")
    reject_keywords = set(settings.get("reject_keywords", [])) or DEFAULT_REJECT_KEYWORDS
    for keyword in reject_keywords:
        if normalize_title(keyword) in haystack:
            return False, f"matched rejection keyword: {keyword}"

    title_only = normalize_title(candidate.title)
    if candidate.source_type == "event_page":
        if title_only in GENERIC_EVENT_TITLES or title_only.startswith(("learn more", "read more")):
            return False, "generic event-page navigation link"
        event_keywords = set(settings.get("event_presentation_keywords", [])) or DEFAULT_EVENT_PRESENTATION_KEYWORDS
        for keyword in event_keywords:
            if normalize_title(keyword) in haystack:
                return True, f"matched event-presentation keyword: {keyword}"
        return False, "no event/webinar/presentation keyword found"

    keep_keywords = set(settings.get("keep_keywords", [])) or DEFAULT_KEEP_KEYWORDS
    for keyword in keep_keywords:
        if normalize_title(keyword) in haystack:
            return True, f"matched key-presentation keyword: {keyword}"

    return False, "no key-presentation keyword found"
