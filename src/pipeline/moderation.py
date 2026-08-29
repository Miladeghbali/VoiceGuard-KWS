import json
import os
import tempfile

from dataclasses import asdict, dataclass
from pathlib import Path

import streamlit as st

from src.audio.transcription import (
    transcribe_audio,
)

from src.kws.dictionary import (
    DEFAULT_KWS_TERMS,
)

from src.kws.detector import (
    normalize_text,
    score_text,
)

from src.kws.redactor import (
    redact,
)

from src.llm.openrouter import (
    get_api_key,
    review,
)


@dataclass
class TranscriptChunk:

    index: int

    start: float

    end: float

    text: str

    kws_score: float = 0.0

    kws_matches: list | None = None

    kws_suspicious: bool = False

    sanitized_text: str = ""

    openrouter_reviewed: bool = False

    openrouter_result: dict | None = None


def build_chunks(
    segments,
    chunk_seconds: int,
    duration: float,
):
    """
    Group ASR segments into fixed time windows.
    """

    buckets = {}

    for segment in segments:

        text = str(
            getattr(
                segment,
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        start = float(
            getattr(
                segment,
                "start",
                0.0,
            )
        )

        bucket = int(
            start // chunk_seconds
        )

        buckets.setdefault(
            bucket,
            [],
        ).append(segment)

    chunks = []

    for index, bucket in enumerate(
        sorted(buckets)
    ):

        items = buckets[bucket]

        start = min(
            float(
                getattr(
                    item,
                    "start",
                    0.0,
                )
            )
            for item in items
        )

        end = max(
            float(
                getattr(
                    item,
                    "end",
                    start,
                )
            )
            for item in items
        )

        if duration:

            end = min(
                end,
                duration,
            )

        text = " ".join(
            str(
                getattr(
                    item,
                    "text",
                    "",
                )
            ).strip()
            for item in items
        )

        chunks.append(
            TranscriptChunk(
                index=index,
                start=start,
                end=max(
                    start,
                    end,
                ),
                text=text,
            )
        )

    return chunks


def run_app():

    st.set_page_config(
        page_title="VoiceGuard-KWS",
        page_icon="🔎",
        layout="wide",
    )

    st.title(
        "🔎 VoiceGuard-KWS"
    )

    st.caption(
        "Audio → Local ASR → KWS → "
        "Redaction → Optional LLM"
    )

    # ==========================================
    # Sidebar
    # ==========================================

    with st.sidebar:

        st.header(
            "Detection Settings"
        )

        model_size = st.selectbox(
            "Whisper model",
            [
                "tiny",
                "base",
                "small",
                "medium",
            ],
            index=1,
        )

        device = st.selectbox(
            "Device",
            [
                "cpu",
                "cuda",
            ],
        )

        compute_type = st.selectbox(
            "Compute type",
            [
                "int8",
                "float16",
                "float32",
            ],
            index=(
                0
                if device == "cpu"
                else 1
            ),
        )

        language = st.selectbox(
            "Language",
            [
                "auto",
                "en",
                "fa",
                "de",
                "es",
                "fr",
                "ar",
            ],
        )

        chunk_seconds = st.slider(
            "Chunk size (seconds)",
            5,
            30,
            12,
        )

        local_threshold = st.slider(
            "KWS threshold",
            0.5,
            8.0,
            2.0,
            0.5,
        )

        max_reviews = st.slider(
            "Maximum LLM reviews",
            0,
            30,
            10,
        )

        st.divider()

        st.header(
            "OpenRouter"
        )

        openrouter_model = st.text_input(
            "Model",
            value=os.getenv(
                "OPENROUTER_MODEL",
                "openai/gpt-4o-mini",
            ),
        )

        openrouter_key = (
            get_api_key()
        )

        if openrouter_key:

            st.success(
                "API key loaded"
            )

        else:

            st.info(
                "Local-only mode"
            )

        referer = st.text_input(
            "HTTP-Referer",
            value=os.getenv(
                "OPENROUTER_REFERER",
                "",
            ),
        )

        custom_terms = st.text_area(
            "Extra KWS terms",
            placeholder=(
                "term1, term2, term3"
            ),
        )

    # ==========================================
    # Audio upload
    # ==========================================

    uploaded = st.file_uploader(
        "Upload audio",
        type=[
            "wav",
            "mp3",
            "m4a",
            "flac",
            "ogg",
            "webm",
        ],
    )

    if not uploaded:

        st.info(
            "Upload an audio file to begin."
        )

        return

    audio_bytes = (
        uploaded.getvalue()
    )

    st.audio(
        audio_bytes,
        format=(
            uploaded.type
            or "audio/wav"
        ),
    )

    analyze = st.button(
        "Analyze voice",
        type="primary",
        use_container_width=True,
    )

    if not analyze:

        return

    # ==========================================
    # KWS dictionary
    # ==========================================

    terms = dict(
        DEFAULT_KWS_TERMS
    )

    for term in custom_terms.split(","):

        normalized_term = (
            normalize_text(term)
        )

        if normalized_term:

            terms[
                normalized_term
            ] = max(
                terms.get(
                    normalized_term,
                    0.0,
                ),
                2.0,
            )

    # ==========================================
    # Save temporary audio
    # ==========================================

    temp_path = None

    try:

        suffix = (
            Path(
                uploaded.name
            ).suffix
            or ".audio"
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as handle:

            handle.write(
                audio_bytes
            )

            temp_path = handle.name

        # ======================================
        # LOCAL TRANSCRIPTION
        # ======================================

        with st.status(
            "Transcribing locally..."
        ):

            (
                segments,
                duration,
                detected_language,
            ) = transcribe_audio(
                temp_path,
                model_size,
                device,
                compute_type,
                language,
            )

    except Exception as exc:

        st.error(
            "Local transcription failed: "
            f"{exc}"
        )

        return

    finally:

        if temp_path:

            try:

                os.unlink(
                    temp_path
                )

            except OSError:

                pass

    # ==========================================
    # Build chunks
    # ==========================================

    chunks = build_chunks(
        segments,
        chunk_seconds,
        duration,
    )

    # ==========================================
    # KWS + REDACTION
    # ==========================================

    for chunk in chunks:

        # KWS detection

        (
            chunk.kws_score,
            chunk.kws_matches,
        ) = score_text(
            chunk.text,
            terms,
        )

        chunk.kws_suspicious = (
            chunk.kws_score
            >= local_threshold
        )

        # IMPORTANT:
        # Redaction happens locally
        # BEFORE the LLM request.

        (
            chunk.sanitized_text,
            _,
        ) = redact(
            chunk.text,
            terms,
        )

    suspicious = [
        chunk
        for chunk in chunks
        if chunk.kws_suspicious
    ]

    # ==========================================
    # LLM semantic verification
    # ==========================================

    review_count = min(
        len(suspicious),
        max_reviews,
    )

    if (
        openrouter_key
        and review_count
    ):

        progress = st.progress(
            0,
            text=(
                "Reviewing sanitized "
                "transcript chunks..."
            ),
        )

        for position, chunk in enumerate(
            suspicious[:review_count],
            start=1,
        ):

            try:

                chunk.openrouter_result = (
                    review(
                        chunk.sanitized_text,
                        openrouter_model.strip(),
                        openrouter_key,
                        referer=referer,
                    )
                )

                chunk.openrouter_reviewed = True

            except Exception as exc:

                chunk.openrouter_result = {
                    "is_nsfw": False,
                    "confidence": 0.0,
                    "categories": [
                        "error"
                    ],
                    "reason": str(exc),
                }

                chunk.openrouter_reviewed = True

            progress.progress(
                position / review_count,
                text=(
                    f"Reviewed "
                    f"{position}/"
                    f"{review_count}"
                ),
            )

        progress.empty()

    # ==========================================
    # Final decision
    # ==========================================

    if (
        openrouter_key
        and review_count
    ):

        final_flagged = sum(
            chunk.kws_suspicious
            and (
                not chunk.openrouter_reviewed
                or not chunk.openrouter_result
                or "error"
                in (
                    chunk.openrouter_result
                    .get(
                        "categories",
                        [],
                    )
                )
                or bool(
                    chunk.openrouter_result
                    .get(
                        "is_nsfw",
                        False,
                    )
                )
            )
            for chunk in chunks
        )

    else:

        final_flagged = len(
            suspicious
        )

    # ==========================================
    # Summary
    # ==========================================

    st.subheader(
        "Summary"
    )

    columns = st.columns(5)

    columns[0].metric(
        "Language",
        detected_language,
    )

    columns[1].metric(
        "Duration",
        f"{duration:.1f}s",
    )

    columns[2].metric(
        "Chunks",
        len(chunks),
    )

    columns[3].metric(
        "KWS flagged",
        len(suspicious),
    )

    columns[4].metric(
        "Final flagged",
        final_flagged,
    )

    # ==========================================
    # Transcript
    # ==========================================

    with st.expander(
        "Full local transcript"
    ):

        st.write(
            " ".join(
                chunk.text
                for chunk in chunks
            )
            or "No speech detected."
        )

    # ==========================================
    # Results
    # ==========================================

    st.subheader(
        "Chunk Details"
    )

    rows = []

    for chunk in chunks:

        review_result = (
            chunk.openrouter_result
            or {}
        )

        rows.append(
            {
                "Chunk":
                    chunk.index + 1,

                "Time":
                    f"{chunk.start:.1f}"
                    f"-"
                    f"{chunk.end:.1f}",

                "KWS Score":
                    chunk.kws_score,

                "KWS Matches":
                    ", ".join(
                        chunk.kws_matches
                        or []
                    ),

                "LLM":
                    (
                        "NSFW"
                        if review_result.get(
                            "is_nsfw"
                        )
                        else (
                            "Reviewed"
                            if chunk.openrouter_reviewed
                            else "Not sent"
                        )
                    ),

                "Original":
                    chunk.text,

                "Sanitized":
                    chunk.sanitized_text,
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    # ==========================================
    # Privacy information
    # ==========================================

    st.info(
        "Privacy: raw audio is processed locally. "
        "Only sanitized transcript chunks can be "
        "sent to OpenRouter. Locally detected "
        "sensitive terms are replaced with "
        "[REDACTED] before the LLM request."
    )

    # ==========================================
    # JSON report
    # ==========================================

    report = {

        "app":
            "VoiceGuard-KWS",

        "detected_language":
            detected_language,

        "duration_seconds":
            duration,

        "local_model":
            model_size,

        "chunk_seconds":
            chunk_seconds,

        "kws_threshold":
            local_threshold,

        "openrouter_model":
            (
                openrouter_model
                if openrouter_key
                else None
            ),

        "chunks":
            [
                asdict(chunk)
                for chunk in chunks
            ],

        "privacy": {

            "audio_uploaded_to_openrouter":
                False,

            "raw_sensitive_terms_sent":
                False,

        },
    }

    st.download_button(
        "Download JSON report",

        data=json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),

        file_name=(
            "voiceguard_report.json"
        ),

        mime="application/json",
    )