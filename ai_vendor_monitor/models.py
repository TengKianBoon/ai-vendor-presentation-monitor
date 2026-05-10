from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceConfig:
    name: str
    vendor: str
    kind: str
    url: str | None = None
    handle: str | None = None
    channel_id: str | None = None
    proof: str = ""


@dataclass
class Candidate:
    vendor: str
    title: str
    url: str
    source_type: str
    source_name: str
    source_proof: str
    platform: str = "web"
    platform_id: str = ""
    published_at: str = ""
    description: str = ""
    speakers: list[str] = field(default_factory=list)
    duration_seconds: int | None = None
    media_url: str = ""
    transcript_status: str = "not_checked"
    transcript_confidence: str = "none"
    transcript_path: str = ""
    summary: dict[str, Any] = field(default_factory=dict)
    alternate_urls: list[str] = field(default_factory=list)

    @property
    def dedupe_id(self) -> str:
        if self.platform_id:
            return f"{self.platform}:{self.platform_id}"
        return self.url


@dataclass
class MonitorResult:
    discovered: list[Candidate]
    accepted: list[Candidate]
    new_items: list[Candidate]
    rejected: list[tuple[Candidate, str]]
