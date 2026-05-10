from __future__ import annotations

from ai_vendor_monitor.models import SourceConfig
from ai_vendor_monitor.sources import discover_event_page, parse_iso_duration


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def test_parse_youtube_iso_duration():
    assert parse_iso_duration("PT1H02M03S") == 3723
    assert parse_iso_duration("PT15M") == 900
    assert parse_iso_duration("") == 0


def test_event_page_keeps_only_vendor_domain_links(monkeypatch):
    html = """
    <html>
      <head><title>OpenAI DevDay</title></head>
      <body>
        <article><a href="/devday/keynote">Watch the AI keynote recording</a></article>
        <article><a href="https://evil.example/openai">OpenAI keynote mirror</a></article>
        <article><a href="https://openai.com/media/devday-keynote.mp4">Direct keynote media</a></article>
        <article><a href="/devday/register">Learn more about this webinar</a></article>
      </body>
    </html>
    """

    def fake_get(*args, **kwargs):
        return FakeResponse(html)

    monkeypatch.setattr("ai_vendor_monitor.sources.requests.get", fake_get)
    config = {"vendors": [{"name": "OpenAI", "official_domains": ["openai.com"]}]}
    source = SourceConfig(
        name="OpenAI DevDay",
        vendor="OpenAI",
        kind="event_page",
        url="https://openai.com/devday/",
        proof="OpenAI-owned page.",
    )

    candidates = discover_event_page(source, config)
    urls = {candidate.url for candidate in candidates}

    assert "https://openai.com/devday/keynote" in urls
    assert "https://evil.example/openai" not in urls
    assert "https://openai.com/devday/register" not in urls
    assert any(candidate.media_url == "https://openai.com/media/devday-keynote.mp4" for candidate in candidates)
