from __future__ import annotations

from rapidfuzz import fuzz

from .models import Candidate
from .normalize import canonical_url, normalize_title


def is_duplicate(
    candidate: Candidate,
    existing: list[dict],
    pending: list[Candidate],
    threshold: int = 92,
) -> tuple[bool, str]:
    candidate_url = canonical_url(candidate.url)
    candidate_id = candidate.dedupe_id
    candidate_title = normalize_title(candidate.title)

    for item in existing:
        if candidate_id and candidate_id == item.get("dedupe_id"):
            return True, "same platform/source id"
        if candidate_url == canonical_url(item.get("url", "")):
            return True, "same canonical URL"
        if item.get("vendor") == candidate.vendor:
            score = fuzz.token_sort_ratio(candidate_title, normalize_title(item.get("title", "")))
            if score >= threshold:
                return True, f"similar title already stored ({score})"

    for item in pending:
        if candidate_id and candidate_id == item.dedupe_id:
            return True, "same platform/source id in current run"
        if candidate_url == canonical_url(item.url):
            return True, "same canonical URL in current run"
        if item.vendor == candidate.vendor:
            score = fuzz.token_sort_ratio(candidate_title, normalize_title(item.title))
            if score >= threshold:
                item.alternate_urls.append(candidate.url)
                return True, f"similar title in current run ({score})"

    return False, ""
