from src.kws.redactor import (
    redact,
)


def test_sensitive_term_redaction():

    text = (
        "This is explicit sexual content."
    )

    weights = {
        "sexual": 2.0,
    }

    sanitized, detected = redact(
        text,
        weights,
    )

    assert (
        "[REDACTED]"
        in sanitized
    )

    assert (
        "sexual"
        not in sanitized
    )

    assert detected