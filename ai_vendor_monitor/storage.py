from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .models import Candidate


ITEMS_FILE = Path("data/items.jsonl")


def ensure_state_files() -> None:
    ITEMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    Path("data/transcripts").mkdir(parents=True, exist_ok=True)
    Path("exports/digests").mkdir(parents=True, exist_ok=True)
    if not ITEMS_FILE.exists():
        ITEMS_FILE.write_text("", encoding="utf-8")


def load_items(path: Path = ITEMS_FILE) -> list[dict]:
    if not path.exists():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def append_items(items: Iterable[Candidate], path: Path = ITEMS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            payload = asdict(item)
            payload["dedupe_id"] = item.dedupe_id
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
