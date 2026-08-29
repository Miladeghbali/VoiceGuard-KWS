import re

from .dictionary import PHRASE_WEIGHTS
from .detector import normalize_text


REDACTION_TOKEN = "[REDACTED]"


def redact(
    text: str,
    weights: dict[str, float],
):
    """
    Remove locally detected sensitive terms
    before sending transcript to an LLM.
    """

    sanitized = normalize_text(text)

    detected = []

    # -----------------------------
    # Redact sensitive phrases
    # -----------------------------

    for pattern in PHRASE_WEIGHTS:

        def phrase_replacer(match):
            detected.append("phrase")
            return f" {REDACTION_TOKEN} "

        sanitized = re.sub(
            pattern,
            phrase_replacer,
            sanitized,
            flags=re.IGNORECASE,
        )

    # -----------------------------
    # Redact individual keywords
    # -----------------------------

    for term in sorted(
        weights,
        key=len,
        reverse=True,
    ):

        if len(term) >= 6:

            pattern = (
                rf"\b{re.escape(term)}\w*\b"
            )

        else:

            pattern = (
                rf"\b{re.escape(term)}\b"
            )

        def term_replacer(
            match,
            current_term=term,
        ):
            detected.append(
                current_term
            )

            return f" {REDACTION_TOKEN} "

        sanitized = re.sub(
            pattern,
            term_replacer,
            sanitized,
            flags=re.IGNORECASE,
        )

    sanitized = re.sub(
        r"\s+",
        " ",
        sanitized,
    ).strip()

    return (
        sanitized,
        sorted(set(detected)),
    )