from src.pipeline.moderation import (
    build_chunks,
)


class FakeSegment:

    def __init__(
        self,
        start,
        end,
        text,
    ):

        self.start = start
        self.end = end
        self.text = text


def test_chunk_creation():

    segments = [

        FakeSegment(
            0,
            2,
            "hello",
        ),

        FakeSegment(
            3,
            5,
            "world",
        ),
    ]

    chunks = build_chunks(
        segments,
        10,
        5,
    )

    assert len(chunks) == 1

    assert (
        "hello"
        in chunks[0].text
    )

    assert (
        "world"
        in chunks[0].text
    )