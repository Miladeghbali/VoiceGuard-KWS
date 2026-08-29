
---


```markdown
# Privacy

VoiceGuard-KWS follows a local-first architecture.

## Audio

Audio is processed locally using Faster-Whisper.

Raw audio is never sent to OpenRouter by this application.

## Keyword Detection

KWS runs locally against the generated transcript.

## Redaction

Sensitive terms detected by the local KWS stage are replaced with:

[REDACTED]

before semantic verification.

## LLM

Only sanitized transcript chunks may be sent to OpenRouter.

The application does not intentionally send:

- Raw audio
- Original sensitive terms detected by KWS

## API Keys

API keys should be stored in:

- Environment variables
- Streamlit secrets

Never commit `.env` or secret values to GitHub.