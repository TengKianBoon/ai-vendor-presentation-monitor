from __future__ import annotations

import datetime as dt

from ai_vendor_monitor.classifier import is_key_presentation
from ai_vendor_monitor.credibility import verify_candidate
from ai_vendor_monitor.dedupe import is_duplicate
from ai_vendor_monitor.digest import render_text
from ai_vendor_monitor.models import Candidate
from ai_vendor_monitor.monitor import detect_speakers
from ai_vendor_monitor.summarizer import summarize


def test_vendor_domain_is_required_for_event_pages():
    config = {
        "vendors": [{"name": "OpenAI", "official_domains": ["openai.com"]}],
        "settings": {},
    }
    official = Candidate(
        vendor="OpenAI",
        title="OpenAI DevDay keynote",
        url="https://openai.com/devday/",
        source_type="event_page",
        source_name="OpenAI DevDay",
        source_proof="OpenAI-owned page.",
    )
    unofficial = Candidate(
        vendor="OpenAI",
        title="OpenAI DevDay mirror",
        url="https://example.com/openai-devday",
        source_type="event_page",
        source_name="Mirror",
        source_proof="Not official.",
    )

    assert verify_candidate(official, config) == (True, "vendor-owned domain")
    assert verify_candidate(unofficial, config) == (False, "source URL is not on an approved vendor domain")


def test_youtube_allowlist_source_is_credible_without_download_permission():
    candidate = Candidate(
        vendor="Anthropic",
        title="Claude product launch",
        url="https://www.youtube.com/watch?v=abc123",
        source_type="youtube",
        source_name="Anthropic YouTube",
        source_proof="Official Anthropic channel.",
        platform="youtube",
        platform_id="abc123",
        transcript_status="unavailable",
    )

    assert verify_candidate(candidate, {"vendors": []}) == (True, "official YouTube source from allowlist")


def test_classifier_accepts_key_presentations_and_rejects_noise():
    config = {"settings": {"min_duration_seconds": 300, "max_duration_seconds": 14400}}
    keynote = Candidate(
        vendor="Salesforce",
        title="Dreamforce AI keynote and Agentforce product demo",
        url="https://www.salesforce.com/plus/dreamforce/",
        source_type="event_page",
        source_name="Dreamforce",
        source_proof="Official.",
        duration_seconds=3600,
    )
    reaction = Candidate(
        vendor="Salesforce",
        title="Unofficial reaction to Dreamforce keynote",
        url="https://www.salesforce.com/plus/dreamforce/reaction",
        source_type="event_page",
        source_name="Dreamforce",
        source_proof="Official.",
        duration_seconds=3600,
    )
    short = Candidate(
        vendor="Salesforce",
        title="Dreamforce AI keynote clip",
        url="https://www.salesforce.com/plus/dreamforce/clip",
        source_type="event_page",
        source_name="Dreamforce",
        source_proof="Official.",
        duration_seconds=60,
    )

    assert is_key_presentation(keynote, config)[0] is True
    assert is_key_presentation(reaction, config)[0] is False
    assert is_key_presentation(short, config)[0] is False


def test_event_page_requires_presentation_signal_not_product_navigation():
    config = {"settings": {"min_duration_seconds": 300, "max_duration_seconds": 14400}}
    nav_link = Candidate(
        vendor="Anthropic",
        title="Claude's Constitution",
        url="https://www.anthropic.com/claudes-constitution",
        source_type="event_page",
        source_name="Anthropic Events",
        source_proof="Official.",
        description="Claude safety and policy page.",
    )
    webinar = Candidate(
        vendor="Anthropic",
        title="Inside Claude Code",
        url="https://www.anthropic.com/events/inside-claude-code",
        source_type="event_page",
        source_name="Anthropic Events",
        source_proof="Official.",
        description="A technical webinar with Anthropic engineers.",
    )

    assert is_key_presentation(nav_link, config)[0] is False
    assert is_key_presentation(webinar, config)[0] is True


def test_dedupe_uses_platform_id_url_and_fuzzy_title():
    existing = [
        {
            "vendor": "OpenAI",
            "title": "OpenAI DevDay keynote: new agent platform",
            "url": "https://openai.com/devday?utm_source=newsletter",
            "dedupe_id": "youtube:abc123",
        }
    ]
    same_id = Candidate(
        vendor="OpenAI",
        title="Different title",
        url="https://www.youtube.com/watch?v=abc123",
        source_type="youtube",
        source_name="OpenAI YouTube",
        source_proof="Official.",
        platform="youtube",
        platform_id="abc123",
    )
    similar_title = Candidate(
        vendor="OpenAI",
        title="OpenAI DevDay keynote new agent platform",
        url="https://openai.com/devday/",
        source_type="event_page",
        source_name="OpenAI DevDay",
        source_proof="Official.",
    )

    assert is_duplicate(same_id, existing, [])[0] is True
    assert is_duplicate(similar_title, existing, [])[0] is True


def test_digest_labels_unavailable_transcripts_clearly():
    candidate = Candidate(
        vendor="LangChain",
        title="LangChain agents webinar",
        url="https://www.langchain.com/events/agents",
        source_type="event_page",
        source_name="LangChain Events",
        source_proof="LangChain-owned events page.",
        transcript_status="unavailable",
    )
    summarize(candidate)
    digest = render_text([candidate], dt.date(2026, 5, 10))

    assert "transcript is unavailable" in digest.lower()
    assert "LangChain agents webinar" in digest


def test_detect_speakers_from_vendor_allowlist():
    config = {
        "vendors": [
            {
                "name": "OpenAI",
                "verified_speakers": ["Sam Altman", "Greg Brockman"],
            }
        ]
    }
    candidate = Candidate(
        vendor="OpenAI",
        title="OpenAI DevDay keynote with Sam Altman",
        url="https://openai.com/devday/",
        source_type="event_page",
        source_name="OpenAI DevDay",
        source_proof="Official.",
        description="Greg Brockman demos the agent platform.",
    )

    assert detect_speakers(candidate, config) == ["Sam Altman", "Greg Brockman"]
