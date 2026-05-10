"""Run the AI Vendor Presentation Monitor.

This entrypoint is intentionally small so the workflow is easy to inspect:

    python pipeline.py --dry-run
    python pipeline.py --max-items 25

The monitor discovers official vendor presentation links, deduplicates them,
transcribes only legally/directly available media, writes repo-visible state,
and sends a Gmail digest.
"""

from __future__ import annotations

import sys

from ai_vendor_monitor.cli import main


if __name__ == "__main__":
    sys.exit(main())
