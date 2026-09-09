# AI Vendor Presentation Monitor

An automated Python pipeline that monitors official AI vendor presentation sources, filters for credible/key presentations, deduplicates repeated links, and prepares a daily digest.

This public repository is a sanitized portfolio version. It contains no secrets, no personal digest history, and no production schedule.

## Why I built it

I needed to know what the major AI vendors actually announce, without drowning in reaction videos and second-hand commentary. The interesting problem was never the scraping — it was deciding what this tool is **not** allowed to do.

**The decisions that shaped it:**

- **Official sources only.** Vendor domains and allowlisted official channels. Reposts, reaction videos, fan mirrors and stock-analysis commentary are rejected by policy, not filtered by hope.
- **No media ripping.** The monitor links to videos and never downloads them. Transcription runs only where a vendor publishes a direct media file I am entitled to process.
- **A sanitised public version.** This repository carries no secrets, no digest history and no production schedule. The private setup stays private.

I set the source policy and the legal boundary before any collection logic existed. The implementation was AI-assisted, against acceptance criteria I wrote.

## What It Shows

- Config-driven source monitoring for AI vendors.
- Official-source filtering for vendor domains and allowlisted YouTube channels.
- Key-presentation classification for keynotes, launches, demos, webinars, and conference talks.
- Duplicate detection using platform IDs, canonical URLs, and fuzzy title matching.
- Transcript safety boundary: links YouTube videos but does not rip/download YouTube media.
- Optional legal-media transcription using Groq or Deepgram when a direct vendor-owned media file exists.
- Optional summarization with OpenAI when transcripts are available.
- Gmail digest delivery in the private production setup.
- Tests and GitHub Actions CI.

## Architecture

```mermaid
flowchart LR
    A["Vendor config"] --> B["Discovery"]
    B --> C["Credibility filter"]
    C --> D["Key presentation classifier"]
    D --> E["Deduplication"]
    E --> F["Transcript handling"]
    F --> G["Summary builder"]
    G --> H["Digest output"]
    H --> I["Email delivery"]
    E --> J["State file"]
```

## Source Policy

The monitor is intentionally conservative:

- Accepts official vendor domains.
- Accepts allowlisted official YouTube channels.
- Rejects reposts, reaction videos, fan mirrors, stock-analysis commentary, and unverified sources.
- Does not rip YouTube audio/video.
- Transcribes only when a legal direct vendor-owned media file is available.

## Vendors In The Sample Config

- OpenAI
- Anthropic / Claude
- DeepSeek
- Qwen / Alibaba Cloud
- Kimi / Moonshot AI
- MiniMax / Hailuo AI
- n8n
- LangChain
- Palantir
- Salesforce

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add API keys to `.env` only for local testing. Never commit `.env`.

## Run

Dry run, no email and no state writing:

```bash
python pipeline.py --dry-run --max-items 10
```

Write local digest/state but skip Gmail:

```bash
python pipeline.py --no-email --max-items 10
```

Run tests:

```bash
pytest -q
```

## GitHub Actions

This showcase repository includes a safe CI workflow at:

```text
.github/workflows/tests.yml
```

The private production version uses a daily workflow with repository secrets for YouTube and Gmail. A non-running example is included at:

```text
examples/daily-digest.workflow.example.yml
```

## Example Output

See:

```text
examples/sample-digest.md
examples/sample-items.jsonl
```

## Privacy And Safety

This public version intentionally excludes:

- Gmail address
- Gmail app password
- API keys
- Production digest history
- Transcripts
- Private repository secrets

## Future Improvements

- Add source-specific connectors for more official event hubs.
- Add a small dashboard for browsing saved presentations.
- Add Slack/Telegram digest delivery.
- Improve transcript capture when vendors publish official caption/transcript files.
- Add stronger speaker extraction and title normalization.
# AI Vendor Presentation Monitor

An automated Python pipeline that monitors official AI vendor presentation sources, filters for credible/key presentations, deduplicates repeated links, and prepares a daily digest.

This public repository is a sanitized portfolio version. It contains no secrets, no personal digest history, and no production schedule.

## What It Shows

- Config-driven source monitoring for AI vendors.
- Official-source filtering for vendor domains and allowlisted YouTube channels.
- Key-presentation classification for keynotes, launches, demos, webinars, and conference talks.
- Duplicate detection using platform IDs, canonical URLs, and fuzzy title matching.
- Transcript safety boundary: links YouTube videos but does not rip/download YouTube media.
- Optional legal-media transcription using Groq or Deepgram when a direct vendor-owned media file exists.
- Optional summarization with OpenAI when transcripts are available.
- Gmail digest delivery in the private production setup.
- Tests and GitHub Actions CI.

## Architecture

```mermaid
flowchart LR
    A["Vendor config"] --> B["Discovery"]
    B --> C["Credibility filter"]
    C --> D["Key presentation classifier"]
    D --> E["Deduplication"]
    E --> F["Transcript handling"]
    F --> G["Summary builder"]
    G --> H["Digest output"]
    H --> I["Email delivery"]
    E --> J["State file"]
```

## Source Policy

The monitor is intentionally conservative:

- Accepts official vendor domains.
- Accepts allowlisted official YouTube channels.
- Rejects reposts, reaction videos, fan mirrors, stock-analysis commentary, and unverified sources.
- Does not rip YouTube audio/video.
- Transcribes only when a legal direct vendor-owned media file is available.

## Vendors In The Sample Config

- OpenAI
- Anthropic / Claude
- DeepSeek
- Qwen / Alibaba Cloud
- Kimi / Moonshot AI
- MiniMax / Hailuo AI
- n8n
- LangChain
- Palantir
- Salesforce

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add API keys to `.env` only for local testing. Never commit `.env`.

## Run

Dry run, no email and no state writing:

```bash
python pipeline.py --dry-run --max-items 10
```

Write local digest/state but skip Gmail:

```bash
python pipeline.py --no-email --max-items 10
```

Run tests:

```bash
pytest -q
```

## GitHub Actions

This showcase repository includes a safe CI workflow at:

```text
.github/workflows/tests.yml
```

The private production version uses a daily workflow with repository secrets for YouTube and Gmail. A non-running example is included at:

```text
examples/daily-digest.workflow.example.yml
```

## Example Output

See:

```text
examples/sample-digest.md
examples/sample-items.jsonl
```

## Privacy And Safety

This public version intentionally excludes:

- Gmail address
- Gmail app password
- API keys
- Production digest history
- Transcripts
- Private repository secrets

## Future Improvements

- Add source-specific connectors for more official event hubs.
- Add a small dashboard for browsing saved presentations.
- Add Slack/Telegram digest delivery.
- Improve transcript capture when vendors publish official caption/transcript files.
- Add stronger speaker extraction and title normalization.
