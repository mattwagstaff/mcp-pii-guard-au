"""Australian passport number recogniser.

Australian passport numbers consist of:
- 1 or 2 uppercase letters followed by 7 digits (e.g. N1234567, PA1234567)
- The letter prefix indicates the passport type (P = standard, PA/PB = etc.)

Context words like "passport" near the pattern boost confidence to reduce
false positives on other alphanumeric codes.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

# 1-2 uppercase letters + 7 digits
_PASSPORT_PATTERN = r"\b[A-Z]{1,2}\d{7}\b"

_PASSPORT_CONTEXT_WORDS = [
    "passport",
    "passport number",
    "passport no",
    "passport #",
    "travel document",
    "australian passport",
    "dfat",
    "department of foreign affairs",
]


class AuPassportRecognizer(PatternRecognizer):
    """Recogniser for Australian passport numbers.

    Matches the standard Australian passport format (1–2 letter prefix + 7 digits)
    with context-word boosting. The base score is low to avoid false positives
    on other alphanumeric identifiers.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_passport",
                regex=_PASSPORT_PATTERN,
                score=0.2,
            )
        ]
        super().__init__(
            supported_entity="AU_PASSPORT",
            patterns=patterns,
            context=_PASSPORT_CONTEXT_WORDS,
            supported_language="en",
            name="AU Passport Recognizer",
        )
