import difflib
import re

from .dictionary import (
    PHRASE_WEIGHTS,
    TERM_ALIASES,
)


def normalize_text(text: str) -> str:
    """
    Normalize transcript text and common obfuscations.
    """

    normalized = text.lower()

    normalized = normalized.replace(
        "’",
        "'",
    )

    normalized = re.sub(
        r"[^\w\s\*'-]",
        " ",
        normalized,
        flags=re.UNICODE,
    )

    for alias, replacement in TERM_ALIASES.items():
        normalized = normalized.replace(
            alias,
            replacement,
        )

    # Conservative leetspeak normalization

    normalized = re.sub(
        r"(?<=[a-z])0(?=[a-z])",
        "o",
        normalized,
    )

    normalized = re.sub(
        r"(?<=[a-z])1(?=[a-z])",
        "i",
        normalized,
    )

    normalized = re.sub(
        r"(?<=[a-z])3(?=[a-z])",
        "e",
        normalized,
    )

    return re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()


def find_matches(
    text: str,
    terms,
):
    """
    Detect KWS terms and conservative fuzzy matches.
    """

    normalized = normalize_text(text)

    tokens = normalized.split()

    matches = []

    for term in terms:

        term = term.lower().strip()

        if not term:
            continue

        # Stem-like terms such as:
        # masturbat -> masturbate / masturbation

        if len(term) >= 6:

            pattern = (
                rf"\b{re.escape(term)}\w*\b"
            )

        else:

            pattern = (
                rf"\b{re.escape(term)}\b"
            )

        if re.search(
            pattern,
            normalized,
        ):
            matches.append(term)

            continue

        # Fuzzy matching for ASR mistakes

        if len(term) >= 5:

            for token in tokens:

                if len(token) < 4:
                    continue

                ratio = difflib.SequenceMatcher(
                    None,
                    token,
                    term,
                ).ratio()

                if ratio >= 0.90:

                    matches.append(
                        "~" + term
                    )

                    break

    # Phrase detection

    for pattern in PHRASE_WEIGHTS:

        if re.search(
            pattern,
            normalized,
        ):
            matches.append("phrase")

    return sorted(set(matches))


def score_text(
    text: str,
    weights: dict[str, float],
):
    """
    Calculate KWS suspicion score.
    """

    normalized = normalize_text(text)

    if not normalized:
        return 0.0, []

    matches = find_matches(
        normalized,
        weights,
    )

    score = 0.0

    for match in matches:

        term = match.lstrip("~")

        score += weights.get(
            term,
            0.0,
        )

    # Phrase score

    for pattern, weight in PHRASE_WEIGHTS.items():

        if re.search(
            pattern,
            normalized,
        ):
            score += weight

    # Multiple signals increase confidence

    if len(matches) >= 2:

        score += min(
            2.0,
            0.5 * (len(matches) - 1),
        )

    return (
        round(score, 2),
        matches,
    )