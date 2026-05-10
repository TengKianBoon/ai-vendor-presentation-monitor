from __future__ import annotations

import datetime as dt
import html
from pathlib import Path

from .models import Candidate


def item_text(item: Candidate) -> str:
    summary = item.summary or {}
    lines = [
        f"{item.vendor}: {item.title}",
        f"Source: {item.url}",
        f"Proof: {item.source_proof}",
        f"Speakers: {', '.join(item.speakers) if item.speakers else 'not detected'}",
        f"Transcript: {item.transcript_status}",
        f"TL;DR: {summary.get('tldr', '')}",
        f"Why it matters: {summary.get('why_it_matters', '')}",
    ]
    for label, key in [
        ("Key announcements", "key_announcements"),
        ("Technical implications", "technical_implications"),
        ("Enterprise implications", "enterprise_implications"),
    ]:
        values = summary.get(key, []) or []
        if values:
            lines.append(f"{label}:")
            lines.extend(f"- {value}" for value in values)
    if item.transcript_path:
        lines.append(f"Transcript file: {item.transcript_path}")
    return "\n".join(lines)


def render_text(items: list[Candidate], run_date: dt.date) -> str:
    if not items:
        return f"AI Vendor Presentation Monitor - {run_date.isoformat()}\n\nNo new official vendor presentations found."
    blocks = [f"AI Vendor Presentation Monitor - {run_date.isoformat()}", f"{len(items)} new item(s)"]
    blocks.extend(item_text(item) for item in items)
    return "\n\n---\n\n".join(blocks)


def render_html(items: list[Candidate], run_date: dt.date) -> str:
    body = [
        "<!doctype html><html><body style=\"font-family:Arial,sans-serif;color:#1f2937;line-height:1.5;\">",
        f"<h1>AI Vendor Presentation Monitor</h1><p>{run_date.isoformat()} &middot; {len(items)} new item(s)</p>",
    ]
    if not items:
        body.append("<p>No new official vendor presentations found.</p>")
    for item in items:
        summary = item.summary or {}
        body.append("<hr>")
        body.append(f"<p><strong>{html.escape(item.vendor)}</strong></p>")
        body.append(f"<h2><a href=\"{html.escape(item.url)}\">{html.escape(item.title)}</a></h2>")
        body.append(f"<p><strong>Source proof:</strong> {html.escape(item.source_proof)}</p>")
        if item.speakers:
            body.append(f"<p><strong>Speakers:</strong> {html.escape(', '.join(item.speakers))}</p>")
        body.append(f"<p><strong>Transcript:</strong> {html.escape(item.transcript_status)}</p>")
        body.append(f"<p><strong>TL;DR:</strong> {html.escape(summary.get('tldr', ''))}</p>")
        body.append(f"<p><strong>Why it matters:</strong> {html.escape(summary.get('why_it_matters', ''))}</p>")
        for label, key in [
            ("Key announcements", "key_announcements"),
            ("Technical implications", "technical_implications"),
            ("Enterprise implications", "enterprise_implications"),
        ]:
            values = summary.get(key, []) or []
            if values:
                body.append(f"<p><strong>{label}</strong></p><ul>")
                body.extend(f"<li>{html.escape(str(value))}</li>" for value in values)
                body.append("</ul>")
        if item.transcript_path:
            body.append(f"<p><strong>Transcript file:</strong> <code>{html.escape(item.transcript_path)}</code></p>")
    body.append(
        "<hr><p style=\"font-size:12px;color:#6b7280;\">Official/vendor-only sources. "
        "YouTube items are linked, not downloaded.</p></body></html>"
    )
    return "\n".join(body)


def write_digest(items: list[Candidate], run_date: dt.date) -> tuple[Path, Path]:
    out_dir = Path("exports/digests")
    out_dir.mkdir(parents=True, exist_ok=True)
    text_path = out_dir / f"{run_date.isoformat()}.txt"
    html_path = out_dir / f"{run_date.isoformat()}.html"
    text_path.write_text(render_text(items, run_date), encoding="utf-8")
    html_path.write_text(render_html(items, run_date), encoding="utf-8")
    return text_path, html_path
