from __future__ import annotations

from urllib.parse import urlsplit

from .config import official_domains
from .models import Candidate


def host_matches_domain(host: str, domain: str) -> bool:
    host = host.lower()
    domain = domain.lower().lstrip(".")
    return host == domain or host.endswith(f".{domain}")


def is_vendor_domain(url: str, domains: set[str]) -> bool:
    host = urlsplit(url).netloc.lower()
    return any(host_matches_domain(host, domain) for domain in domains)


def verify_candidate(candidate: Candidate, config: dict) -> tuple[bool, str]:
    if candidate.source_type == "youtube":
        return True, "official YouTube source from allowlist"

    domains = official_domains(config, candidate.vendor)
    if is_vendor_domain(candidate.url, domains):
        return True, "vendor-owned domain"

    return False, "source URL is not on an approved vendor domain"
