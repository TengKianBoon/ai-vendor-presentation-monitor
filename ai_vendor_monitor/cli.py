from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

from .config import DEFAULT_CONFIG, load_config
from .digest import render_html, render_text, write_digest
from .emailer import send_gmail
from .monitor import run_discovery
from .storage import append_items, ensure_state_files
from .summarizer import summarize
from .transcripts import maybe_transcribe


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor official AI vendor presentations.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Discover and print only; do not email or write state.")
    parser.add_argument("--no-email", action="store_true", help="Write state/digest but skip Gmail delivery.")
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument("--max-items", type=int, default=25)
    args = parser.parse_args()

    os.chdir(Path(__file__).resolve().parents[1])
    ensure_state_files()
    config = load_config(args.config)
    lookback_days = args.lookback_days or int(config.get("settings", {}).get("lookback_days", 2))
    run_date = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).date()

    result = run_discovery(config, os.environ.get("YOUTUBE_API_KEY"), lookback_days)
    items = result.new_items[: args.max_items]

    print(f"[INFO] Discovered: {len(result.discovered)}")
    print(f"[INFO] Accepted official key presentations: {len(result.accepted)}")
    print(f"[INFO] New after dedupe: {len(items)}")
    if args.dry_run:
        for item in items:
            print(f"- [{item.vendor}] {item.title} :: {item.url}")
        return 0

    for item in items:
        maybe_transcribe(item, config, run_date)
        summarize(item)

    text_path, html_path = write_digest(items, run_date)
    append_items(items)

    if args.no_email:
        print(f"[OK] Digest written: {text_path} and {html_path}")
        return 0

    subject = f"AI Vendor Presentation Monitor - {run_date.isoformat()} ({len(items)} new)"
    send_gmail(subject, render_text(items, run_date), render_html(items, run_date))
    print(f"[OK] Gmail sent. Digest written: {text_path} and {html_path}")
    return 0
