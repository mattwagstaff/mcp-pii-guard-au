"""Australian Tax File Number (TFN) recogniser.

TFNs are 8 or 9 digit numbers validated with a weighted checksum algorithm.
The weights for a 9-digit TFN are [1, 4, 3, 7, 5, 8, 6, 9, 10].
The weighted sum must be divisible by 11 with no remainder.

Context words like "TFN" or "tax file number" near the pattern boost confidence
to reduce false positives on bare digit sequences.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# Matches 8 or 9 digits with optional spaces/hyphens between groups of 3
_TFN_PATTERN = r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{2,3}\b"

_TFN_WEIGHTS_9 = [1, 4, 3, 7, 5, 8, 6, 9, 10]
_TFN_WEIGHTS_8 = [10, 7, 8, 4, 6, 3, 5, 1]  # legacy 8-digit

_TFN_CONTEXT_WORDS = [
    "tfn",
    "tax file number",
    "tax file no",
    "tax file #",
    "tax number",
    "ato",
    "australian taxation",
]


def _validate_tfn(digits: str) -> bool:
    """Validate a TFN using the weighted checksum algorithm."""
    if len(digits) == 9:
        weights = _TFN_WEIGHTS_9
    elif len(digits) == 8:
        weights = _TFN_WEIGHTS_8
    else:
        return False

    total = sum(int(d) * w for d, w in zip(digits, weights))
    return total % 11 == 0


class AuTfnRecognizer(PatternRecognizer):
    """Recogniser for Australian Tax File Numbers.

    Uses pattern matching with checksum validation and context-word boosting.
    A bare 9-digit number matching the checksum scores ~0.4. With nearby context
    words like "TFN" or "tax file number", the score is boosted above the default
    0.7 confidence threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_tfn",
                regex=_TFN_PATTERN,
                score=0.4,
            )
        ]
        super().__init__(
            supported_entity="AU_TFN",
            patterns=patterns,
            context=_TFN_CONTEXT_WORDS,
            supported_language="en",
            name="AU TFN Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the TFN checksum. Returns True to boost score, False to discard."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_tfn(digits):
            return True
        return False
