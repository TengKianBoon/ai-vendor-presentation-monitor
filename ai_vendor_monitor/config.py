from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import SourceConfig


DEFAULT_CONFIG = Path("config/vendors.yml")


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    data.setdefault("settings", {})
    data.setdefault("vendors", [])
    return data


def official_domains(config: dict[str, Any], vendor: str | None = None) -> set[str]:
    domains: set[str] = set()
    for vendor_cfg in config.get("vendors", []):
        if vendor and vendor_cfg.get("name") != vendor:
            continue
        for domain in vendor_cfg.get("official_domains", []):
            domains.add(domain.lower().lstrip("."))
    return domains


def vendor_aliases(config: dict[str, Any], vendor: str) -> list[str]:
    for vendor_cfg in config.get("vendors", []):
        if vendor_cfg.get("name") == vendor:
            return [vendor, *vendor_cfg.get("aliases", [])]
    return [vendor]


def vendor_speakers(config: dict[str, Any], vendor: str) -> list[str]:
    for vendor_cfg in config.get("vendors", []):
        if vendor_cfg.get("name") == vendor:
            return vendor_cfg.get("verified_speakers", [])
    return []


def source_configs(config: dict[str, Any]) -> list[SourceConfig]:
    sources: list[SourceConfig] = []
    for vendor_cfg in config.get("vendors", []):
        vendor = vendor_cfg["name"]
        for channel in vendor_cfg.get("youtube_channels", []):
            sources.append(
                SourceConfig(
                    name=channel.get("name", f"{vendor} YouTube"),
                    vendor=vendor,
                    kind="youtube",
                    handle=channel.get("handle"),
                    channel_id=channel.get("channel_id"),
                    proof=channel.get("proof", "Official YouTube channel allowlisted in config."),
                )
            )
        for page in vendor_cfg.get("event_pages", []):
            sources.append(
                SourceConfig(
                    name=page.get("name", f"{vendor} event page"),
                    vendor=vendor,
                    kind="event_page",
                    url=page["url"],
                    proof=page.get("proof", "Vendor-owned event or webinar page."),
                )
            )
    return sources
