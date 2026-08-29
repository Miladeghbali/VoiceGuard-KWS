# 🔎 VoiceGuard-KWS

**Privacy-Preserving Voice NSFW Detection using Keyword Spotting, Local Redaction, and LLM Semantic Verification**

VoiceGuard-KWS is a **local-first voice content moderation system** designed to detect potentially NSFW content in audio recordings while minimizing sensitive data exposure.

The system processes audio locally using **Faster-Whisper**, detects suspicious keywords using a lightweight **Keyword Spotting (KWS)** engine, removes sensitive terms locally, and optionally sends only the sanitized transcript to an LLM through **OpenRouter** for semantic verification.

> **Raw audio is never uploaded to OpenRouter by this application.**

---

## ✨ Key Features

* 🎙️ Local audio transcription with Faster-Whisper
* 🔎 Keyword Spotting (KWS)
* 🧹 Local sensitive-word redaction
* 🤖 Optional LLM semantic verification
* 🔐 Privacy-preserving processing pipeline
* 🧩 Configurable keyword dictionary
* 📝 Custom domain-specific keywords
* 🌍 Multiple language support
* ⚡ Lightweight local-first architecture
* 📊 Chunk-level moderation results
* 📄 JSON report generation
* 🧪 Automated unit tests
* 🔄 GitHub Actions CI
* 🔑 Environment-based API key management

---

# 🏗️ Architecture

VoiceGuard-KWS follows a local-first processing architecture:

```text
                    ┌─────────────────┐
                    │   Audio File    │
                    └────────┬────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Faster-Whisper    │
                  │   Local ASR         │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Transcript Chunks  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       KWS           │
                  │ Keyword Spotting    │
                  └──────────┬──────────┘
                             │
                    Suspicious?
                       /       \
                     No         Yes
                     │           │
                     ▼           ▼
                Local Result   Redaction
                                 │
                                 ▼
                           [REDACTED]
                                 │
                                 ▼
                       ┌─────────────────┐
                       │    OpenRouter   │
                       │   Optional LLM  │
                       └────────┬────────┘
                                │
                                ▼
                       Semantic Verification
                                │
                                ▼
                          Final Decision
```

---

# 🔐 Privacy Model

Privacy is one of the main design principles of VoiceGuard-KWS.

### Audio processing

Audio is processed locally using Faster-Whisper.

```text
Audio
  ↓
Local Faster-Whisper
```

The raw audio file is **not sent to OpenRouter**.

### Sensitive content processing

After transcription, the local KWS engine searches for configured sensitive terms.

For example:

```text
Original transcript:

This contains sensitive sexual content.
```

The local redaction stage transforms it into:

```text
Sanitized transcript:

this contains [REDACTED] [REDACTED]
```

Only the sanitized transcript can be sent to the LLM.

### Data flow

```text
                    LOCAL
                     │
                     ▼
                  Audio
                     │
                     ▼
              Faster-Whisper
                     │
                     ▼
                Transcript
                     │
                     ▼
                    KWS
                     │
                     ▼
                 Redaction
                     │
                     ▼
              Sanitized Text
                     │
                     │ OPTIONAL
                     ▼
                OpenRouter
```

Therefore:

> **Raw audio and locally detected sensitive terms are not intentionally sent to the LLM.**

---

# 🧠 How KWS Works

The KWS engine uses a configurable dictionary of sensitive terms.

Each keyword can have a weight.

Example:

```python
DEFAULT_KWS_TERMS = {
    "sexual": 1.8,
    "porn": 2.5,
    "nude": 1.5,
    "explicit": 2.0,
}
```

The detector calculates a local suspicion score.

For example:

```text
Keyword             Weight
--------------------------------
sexual               1.8
porn                 2.5
nude                 1.5
```

If multiple signals appear in the same transcript chunk, the score can increase.

The user can configure the detection threshold through the Streamlit interface.

---

# 🧹 Local Redaction

Redaction happens **before the LLM request**.

Example:

```text
Original:

This is explicit sexual material.
```

After KWS:

```text
Matches:

explicit
sexual
```

After redaction:

```text
This is [REDACTED] [REDACTED] material.
```

The LLM receives:

```text
Sanitized transcript:

This is [REDACTED] [REDACTED] material.
```

The LLM is explicitly instructed not to reconstruct removed words.

---

# 🤖 LLM Semantic Verification

KWS is intentionally lightweight.

Keyword matching alone can produce false positives.

For example:

```text
"sex education"
```

may contain a sensitive keyword without necessarily representing explicit content.

Therefore, VoiceGuard-KWS can optionally use an LLM for semantic verification.

The process is:

```text
KWS
 ↓
Suspicious chunk
 ↓
Local Redaction
 ↓
Sanitized transcript
 ↓
LLM
 ↓
Semantic classification
```

The LLM returns structured information such as:

```json
{
  "is_nsfw": true,
  "confidence": 0.92,
  "categories": [
    "sexual_content"
  ],
  "reason": "The sanitized transcript indicates potentially explicit content."
}
```

---

# 🌍 Supported Languages

The application supports:

```text
auto
en
fa
de
es
fr
ar
```

The underlying transcription quality depends on the selected Faster-Whisper model and audio quality.

Additional languages can be added later.

---

# 📁 Project Structure

```text
VoiceGuard-KWS/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── schemas.py
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   └── transcription.py
│   │
│   ├── kws/
│   │   ├── __init__.py
│   │   ├── dictionary.py
│   │   ├── detector.py
│   │   └── redactor.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── openrouter.py
│   │
│   └── pipeline/
│       ├── __init__.py
│       └── moderation.py
│
├── tests/
│   ├── test_kws.py
│   ├── test_redactor.py
│   └── test_pipeline.py
│
├── docs/
│   ├── architecture.md
│   └── privacy.md
│
└── .github/
    └── workflows/
        └── ci.yml
```

---

# 🧩 Main Components

## `audio/transcription.py`

Responsible for:

* Loading Faster-Whisper
* Local speech-to-text
* Language detection
* Audio duration detection

---

## `kws/dictionary.py`

Contains:

* Default sensitive keywords
* Keyword weights
* Phrase patterns
* Common obfuscation aliases

---

## `kws/detector.py`

Responsible for:

* Text normalization
* Keyword detection
* Fuzzy matching
* Suspicion scoring

---

## `kws/redactor.py`

Responsible for:

* Removing locally detected sensitive terms
* Replacing them with `[REDACTED]`
* Preparing safe text for the LLM

---

## `llm/openrouter.py`

Responsible for:

* OpenRouter API communication
* Semantic verification
* JSON response parsing
* API error handling

Only sanitized transcript text should reach this layer.

---

## `pipeline/moderation.py`

Orchestrates the complete pipeline:

```text
Audio
 ↓
Transcription
 ↓
Chunking
 ↓
KWS
 ↓
Redaction
 ↓
LLM Verification
 ↓
Final Result
```

---

## `schemas.py`

Contains structured data models shared between components.

Main models:

```text
KWSResult
RedactionResult
LLMResult
TranscriptChunk
ModerationReport
```

This keeps the architecture clean and prevents different modules from defining duplicate data structures.

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/Miladeghbali/VoiceGuard-KWS.git
```

```bash
cd VoiceGuard-KWS
```

---

## 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 OpenRouter Configuration

OpenRouter is optional.

The application can operate in **local-only mode** without an API key.

If you want semantic LLM verification, create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_REFERER=
```

> Never commit `.env` to GitHub.

The `.gitignore` file already excludes it.

---

# ▶️ Run the Application

Start Streamlit:

```bash
streamlit run app.py
```

Then open the Streamlit URL shown in the terminal.

---

# 🧪 Run Tests

Run:

```bash
pytest -q
```

The tests cover:

* KWS normalization
* Keyword detection
* Redaction
* Transcript chunk creation

---

# 🔄 Continuous Integration

The project includes GitHub Actions:

```text
.github/
└── workflows/
    └── ci.yml
```

Every push or pull request can automatically:

```text
Checkout repository
        ↓
Install Python
        ↓
Install dependencies
        ↓
Run pytest
        ↓
PASS / FAIL
```

This helps prevent broken code from being merged into the project.

---

# 📊 Example Processing

Suppose the local ASR produces:

```text
The transcript contains potentially sensitive content.
```

The KWS engine analyzes the transcript:

```text
KWS Score: 4.3

Detected signals:
- sensitive_term
- phrase
```

Then redaction produces:

```text
The transcript contains [REDACTED] content.
```

The LLM receives only:

```text
The transcript contains [REDACTED] content.
```

The final result combines:

```text
Local KWS
+
Optional LLM semantic verification
```

---

# ⚙️ Configuration

The Streamlit sidebar allows configuration of:

### Whisper model

```text
tiny
base
small
medium
```

Larger models generally provide better transcription quality but require more computational resources.

### Device

```text
CPU
CUDA
```

### Compute type

```text
int8
float16
float32
```

### Chunk size

Controls how transcript segments are grouped before KWS and LLM processing.

### KWS threshold

Controls how easily a transcript chunk becomes suspicious.

### Maximum LLM reviews

Limits the number of suspicious chunks sent to the semantic verification stage.

---

# 🎯 Design Goals

VoiceGuard-KWS was designed around the following principles:

1. **Privacy First**
2. **Local Processing**
3. **Minimal External Data Exposure**
4. **Modular Architecture**
5. **Configurable Detection**
6. **Explainable Local Signals**
7. **Optional AI Verification**
8. **Automated Testing**
9. **Clean GitHub Structure**
10. **Future Extensibility**

---

# 🔮 Future Improvements

Possible future versions can include:

* Multilingual KWS dictionaries
* Persian-specific keyword normalization
* Better ASR error correction
* Audio-level acoustic detection
* Real-time microphone monitoring
* WebSocket streaming
* ONNX-based local models
* Transformer-based local moderation
* Batch audio processing
* Docker deployment
* REST API
* Authentication
* PostgreSQL result storage
* Redis caching
* Prometheus metrics
* Model benchmarking
* Precision/Recall evaluation
* ROC-AUC evaluation
* Configurable moderation policies
* Plugin-based detection modules

---

# ⚠️ Limitations

VoiceGuard-KWS is a moderation prototype and should not be considered a perfect content classification system.

Possible errors include:

* ASR transcription errors
* False positives from ambiguous words
* False negatives for content not represented in the KWS dictionary
* Language-specific variations
* Context-dependent meanings
* LLM classification errors

KWS should therefore be considered a **triage mechanism**, while the optional LLM provides additional semantic context.

---

# 🔐 Security Notes

Never commit:

```text
.env
API keys
access tokens
private credentials
audio recordings
personal user data
```

Use environment variables or Streamlit secrets for sensitive configuration.

---

# 📜 License

This project is licensed under the MIT License.

See:

```text
LICENSE
```

for details.

---

# 👨‍💻 Author

**Milad Eghbali**

GitHub:

https://github.com/Miladeghbali

---

# ⭐ Project Summary

VoiceGuard-KWS combines:

```text
Local Speech Recognition
        +
Keyword Spotting
        +
Local Redaction
        +
Optional LLM Verification
        +
Privacy-Preserving Architecture
```

The key architectural principle is:

> **Detect locally → Remove sensitive terms locally → Send only sanitized text for semantic verification.**

This approach reduces unnecessary exposure of sensitive audio and transcript content while still allowing an LLM to provide contextual moderation.
