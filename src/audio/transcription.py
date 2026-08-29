from typing import Any

import streamlit as st


@st.cache_resource(show_spinner=False)
def load_whisper_model(
    model_size: str,
    device: str,
    compute_type: str,
) -> Any:
    """
    Load and cache Faster-Whisper model.
    """

    from faster_whisper import WhisperModel

    return WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
    )


def transcribe_audio(
    audio_path: str,
    model_size: str,
    device: str,
    compute_type: str,
    language: str,
):
    """
    Transcribe audio locally using Faster-Whisper.

    Raw audio is never sent to OpenRouter.
    """

    model = load_whisper_model(
        model_size,
        device,
        compute_type,
    )

    segments, info = model.transcribe(
        audio_path,
        language=None if language == "auto" else language,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    segment_list = list(segments)

    duration = float(
        getattr(info, "duration", 0.0) or 0.0
    )

    if duration <= 0 and segment_list:
        duration = max(
            float(getattr(segment, "end", 0.0))
            for segment in segment_list
        )

    detected_language = str(
        getattr(info, "language", "unknown")
        or "unknown"
    )

    return (
        segment_list,
        duration,
        detected_language,
    )