# Security

Do not commit real API keys, Gmail app passwords, transcripts, or private digest history.

For production use, store secrets only in GitHub repository secrets:

- `YOUTUBE_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `DIGEST_TO_EMAIL`
- optional `GROQ_API_KEY`
- optional `DEEPGRAM_API_KEY`
- optional `OPENAI_API_KEY`

This showcase repository is intentionally configured with test-only CI.
