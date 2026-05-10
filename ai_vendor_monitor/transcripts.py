from __future__ import annotations

import datetime as dt
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import requests

from .config import official_domains
from .credibility import is_vendor_domain
from .models import Candidate
from .normalize import slugify

GROQ_TRANSCRIPTION_API = "https://api.groq.com/openai/v1/audio/transcriptions"
DEEPGRAM_API = "https://api.deepgram.com/v1/listen"


def is_legal_direct_media(candidate: Candidate, config: dict) -> bool:
    if not candidate.media_url:
        return False
    domains = official_domains(config, candidate.vendor)
    return is_vendor_domain(candidate.media_url, domains)


def download_media(url: str, max_mb: int) -> Path:
    suffix = Path(urlsplit(url).path).suffix or ".media"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    path = Path(handle.name)
    handle.close()
    max_bytes = max_mb * 1024 * 1024
    downloaded = 0
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with path.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    path.unlink(missing_ok=True)
                    raise ValueError(f"media file is larger than {max_mb} MB")
                output.write(chunk)
    return path


def transcribe_with_groq(path: Path, api_key: str) -> str:
    with path.open("rb") as handle:
        response = requests.post(
            GROQ_TRANSCRIPTION_API,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (path.name, handle, "application/octet-stream")},
            data={"model": "whisper-large-v3-turbo", "response_format": "text", "temperature": "0"},
            timeout=600,
        )
    response.raise_for_status()
    return response.text.strip()


def transcribe_with_deepgram(path: Path, api_key: str) -> str:
    params = {"model": "nova-3", "smart_format": "true", "diarize": "true"}
    with path.open("rb") as handle:
        response = requests.post(
            DEEPGRAM_API,
            params=params,
            headers={"Authorization": f"Token {api_key}", "Content-Type": "application/octet-stream"},
            data=handle,
            timeout=600,
        )
    response.raise_for_status()
    payload = response.json()
    alternatives = payload.get("results", {}).get("channels", [{}])[0].get("alternatives", [])
    if alternatives:
        return alternatives[0].get("transcript", "").strip()
    return ""


def maybe_transcribe(candidate: Candidate, config: dict, run_date: dt.date) -> None:
    if not is_legal_direct_media(candidate, config):
        if candidate.source_type == "youtube":
            candidate.transcript_status = "youtube_link_only_no_legal_download"
        else:
            candidate.transcript_status = "unavailable_no_legal_direct_media"
        candidate.transcript_confidence = "none"
        return

    groq_key = os.environ.get("GROQ_API_KEY")
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY")
    if not groq_key and not deepgram_key:
        candidate.transcript_status = "legal_media_found_but_no_transcription_key"
        candidate.transcript_confidence = "none"
        return

    media_path: Path | None = None
    try:
        max_mb = int(config.get("settings", {}).get("max_media_download_mb", 250))
        media_path = download_media(candidate.media_url, max_mb)
        transcript = ""
        provider = ""
        if groq_key:
            try:
                transcript = transcribe_with_groq(media_path, groq_key)
                provider = "groq-whisper-large-v3-turbo"
            except requests.RequestException:
                transcript = ""
        if not transcript and deepgram_key:
            transcript = transcribe_with_deepgram(media_path, deepgram_key)
            provider = "deepgram-nova-3"

        if not transcript:
            candidate.transcript_status = "transcription_failed"
            candidate.transcript_confidence = "none"
            return

        transcript_dir = Path("data/transcripts") / run_date.isoformat()
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_file = transcript_dir / f"{slugify(candidate.vendor)}-{slugify(candidate.title)}.txt"
        transcript_file.write_text(
            f"Title: {candidate.title}\n"
            f"Vendor: {candidate.vendor}\n"
            f"Source: {candidate.url}\n"
            f"Media: {candidate.media_url}\n"
            f"Provider: {provider}\n\n"
            f"{transcript}\n",
            encoding="utf-8",
        )
        candidate.transcript_path = transcript_file.as_posix()
        candidate.transcript_status = "available"
        candidate.transcript_confidence = "machine"
    finally:
        if media_path:
            media_path.unlink(missing_ok=True)
