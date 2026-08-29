from src.kws.detector import (
    normalize_text,
    score_text,
)

from src.kws.dictionary import (
    DEFAULT_KWS_TERMS,
)


def test_alias_normalization():

    assert (
        normalize_text("f*ck")
        == "fuck"
    )


def test_keyword_detection():

    score, matches = score_text(
        "explicit sexual content",
        DEFAULT_KWS_TERMS,
    )

    assert score > 0

    assert matches