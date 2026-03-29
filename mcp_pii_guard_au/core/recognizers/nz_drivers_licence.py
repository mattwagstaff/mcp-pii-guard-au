"""New Zealand drivers licence number recogniser.

NZ drivers licence numbers are 2 letters followed by 6 digits (e.g. AB123456).
There is no publicly documented checksum algorithm.

Because this format overlaps with other alphanumeric identifiers, the recogniser
relies on context words like "licence", "driver", or "NZTA" for confidence
boosting. Without nearby context, matches will score below the default 0.7
confidence threshold.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

# NZ licence format: 2 letters + 6 digits
_NZ_LICENCE_PATTERN = r"\b[A-Z]{2}\d{6}\b"

_NZ_LICENCE_CONTEXT_WORDS = [
    "licence",
    "license",
    "driver licence",
    "drivers licence",
    "driver's licence",
    "driving licence",
    "licence number",
    "licence no",
    "licence #",
    "nzta",
    "nz transport agency",
    "waka kotahi",
    "new zealand transport",
    "driver identification",
]


class NzDriversLicenceRecognizer(PatternRecognizer):
    """Recogniser for New Zealand drivers licence numbers.

    Matches 2-letter + 6-digit patterns. Due to overlap with other identifier
    formats (including NSW drivers licence), this recogniser depends on context
    words to achieve a useful confidence score. Without nearby keywords like
    "licence" or "NZTA", matches will score below the default threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="nz_drivers_licence",
                regex=_NZ_LICENCE_PATTERN,
                score=0.2,
            )
        ]
        super().__init__(
            supported_entity="NZ_DRIVERS_LICENCE",
            patterns=patterns,
            context=_NZ_LICENCE_CONTEXT_WORDS,
            supported_language="en",
            name="NZ Drivers Licence Recognizer",
        )
