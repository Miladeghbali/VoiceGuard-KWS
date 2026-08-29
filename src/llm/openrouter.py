import json
import os
import re
from typing import Any

import requests
import streamlit as st


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_api_key() -> str:
    """
    Read OpenRouter API key from Streamlit secrets
    or environment variables.
    """

    try:
        secret_value = st.secrets.get(
            "OPENROUTER_API_KEY",
            "",
        )
    except Exception:
        secret_value = ""

    return str(
        secret_value
        or os.getenv(
            "OPENROUTER_API_KEY",
            "",
        )
    ).strip()


def extract_json(content: Any) -> dict[str, Any]:
    """
    Safely extract a JSON object from an LLM response.
    """

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        )

    raw = str(content or "").strip()

    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    match = re.search(
        r"\{.*\}",
        raw,
        flags=re.DOTALL,
    )

    if match:
        raw = match.group(0)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON: {exc}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "LLM returned non-object JSON"
        )

    return result


def review(
    sanitized_text: str,
    model: str,
    api_key: str,
    referer: str = "",
) -> dict[str, Any]:
    """
    Send ONLY sanitized transcript to OpenRouter.

    Sensitive terms have already been replaced
    locally with [REDACTED].
    """

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured."
        )

    if not model.strip():
        raise ValueError(
            "OpenRouter model is not configured."
        )

    system_prompt = """
You are a strict content-safety classifier.

The transcript has already been processed by a local
Keyword Spotting and redaction stage.

Sensitive terms may appear as [REDACTED].

Do NOT reconstruct, guess, infer, or output removed words.

Classify whether the sanitized transcript indicates
adult or sexually explicit content.

Profanity without sexual meaning is not sufficient.

Return ONLY valid JSON using exactly this structure:

{
  "is_nsfw": true,
  "confidence": 0.0,
  "categories": [],
  "reason": "short explanation"
}
""".strip()

    payload: dict[str, Any] = {
        "model": model.strip(),
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    "Sanitized transcript:\n"
                    + sanitized_text
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 180,
        "response_format": {
            "type": "json_object"
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": "VoiceGuard-KWS",
    }

    if referer.strip():
        headers["HTTP-Referer"] = referer.strip()

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if response.status_code == 400:
        payload.pop(
            "response_format",
            None,
        )

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=90,
        )

    response.raise_for_status()

    body = response.json()

    try:
        content = (
            body["choices"][0]
            ["message"]
            ["content"]
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            f"Unexpected OpenRouter response: {body}"
        ) from exc

    result = extract_json(content)

    result["is_nsfw"] = bool(
        result.get(
            "is_nsfw",
            False,
        )
    )

    try:
        result["confidence"] = max(
            0.0,
            min(
                1.0,
                float(
                    result.get(
                        "confidence",
                        0.0,
                    )
                ),
            ),
        )
    except (TypeError, ValueError):
        result["confidence"] = 0.0

    if not isinstance(
        result.get("categories"),
        list,
    ):
        result["categories"] = []

    result["reason"] = str(
        result.get(
            "reason",
            "",
        )
    ).strip()

    return result