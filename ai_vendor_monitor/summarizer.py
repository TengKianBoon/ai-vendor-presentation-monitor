from __future__ import annotations

import json
import os
from pathlib import Path

import requests

from .models import Candidate

OPENAI_CHAT_COMPLETIONS = "https://api.openai.com/v1/chat/completions"


def unavailable_summary(candidate: Candidate) -> dict:
    status_notes = {
        "youtube_link_only_no_legal_download": (
            "Official YouTube link found; the monitor links it but does not download/rip YouTube media."
        ),
        "unavailable_no_legal_direct_media": (
            "Official source found; transcript is unavailable because no legal/direct vendor media file was found."
        ),
        "legal_media_found_but_no_transcription_key": (
            "Legal/direct vendor media was found, but no Groq or Deepgram transcription key is configured."
        ),
        "transcription_failed": "Legal/direct vendor media was found, but transcription failed.",
    }
    note = status_notes.get(
        candidate.transcript_status,
        "Official source found; transcript is unavailable from a legal/direct source.",
    )
    metadata = " ".join(candidate.description.split())[:280]
    return {
        "status": "transcript_unavailable",
        "tldr": note,
        "why_it_matters": "This is from an approved official vendor source and may be worth manual review.",
        "key_announcements": [f"Metadata note: {metadata}"] if metadata else [],
        "technical_implications": [],
        "enterprise_implications": [],
        "source_links": [candidate.url],
    }


def local_transcript_summary(candidate: Candidate, transcript: str) -> dict:
    preview = " ".join(transcript.split())[:500]
    return {
        "status": "local_summary",
        "tldr": preview or "Transcript captured, but no summary model was configured.",
        "why_it_matters": "Transcript captured from a legal/direct vendor media source.",
        "key_announcements": [],
        "technical_implications": [],
        "enterprise_implications": [],
        "source_links": [candidate.url],
    }


def openai_summary(candidate: Candidate, transcript: str, api_key: str) -> dict:
    model = os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4.1-mini")
    prompt = {
        "title": candidate.title,
        "vendor": candidate.vendor,
        "source": candidate.url,
        "transcript": transcript[:80_000],
    }
    response = requests.post(
        OPENAI_CHAT_COMPLETIONS,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Summarize AI vendor presentations for an executive daily digest. "
                        "Return strict JSON with keys: tldr, why_it_matters, "
                        "key_announcements, technical_implications, enterprise_implications."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        },
        timeout=120,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"].strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    parsed = json.loads(text)
    parsed["status"] = "summarized"
    parsed["source_links"] = [candidate.url]
    return parsed


def summarize(candidate: Candidate) -> None:
    if candidate.transcript_status != "available" or not candidate.transcript_path:
        candidate.summary = unavailable_summary(candidate)
        return

    transcript = Path(candidate.transcript_path).read_text(encoding="utf-8")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        candidate.summary = local_transcript_summary(candidate, transcript)
        return
    try:
        candidate.summary = openai_summary(candidate, transcript, api_key)
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        candidate.summary = local_transcript_summary(candidate, transcript)
