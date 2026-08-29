# VoiceGuard-KWS Architecture

## Processing Pipeline

```text
Audio
  |
  v
Faster-Whisper
  |
  v
Local Transcript
  |
  v
KWS Detection
  |
  +---- No suspicious signal
  |          |
  |          v
  |      Local result
  |
  +---- Suspicious signal
             |
             v
       Local Redaction
             |
             v
        [REDACTED]
             |
             v
      OpenRouter LLM
             |
             v
    Semantic Verification
             |
             v
       Final Result