"""New Zealand IRD (Inland Revenue Department) number recogniser.

IRD numbers are 8 or 9 digit numbers validated with a mod-11 checksum algorithm.
The primary weights for an 8-digit IRD are [3, 2, 7, 6, 5, 4, 3, 2].
If the primary check fails, secondary weights [7, 4, 3, 2, 5, 2, 7, 6, 3, 2]
are used for 9-digit numbers.

The weighted sum modulo 11 must produce a valid check digit.

Context words like "IRD" or "inland revenue" near the pattern boost confidence
to reduce false positives on bare digit sequences.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# Matches 8 or 9 digits with optional spaces/hyphens
_IRD_PATTERN = r"\b\d{2,3}[\s\-]?\d{3}[\s\-]?\d{3}\b"

_IRD_WEIGHTS_8 = [3, 2, 7, 6, 5, 4, 3, 2]
_IRD_WEIGHTS_9 = [7, 4, 3, 2, 5, 2, 7, 6, 3, 2]

_IRD_CONTEXT_WORDS = [
    "ird",
    "ird number",
    "ird no",
    "ird #",
    "inland revenue",
    "inland revenue department",
    "tax number",
    "gst number",
    "nz tax",
    "new zealand tax",
    "ir number",
]


def _validate_ird(digits: str) -> bool:
    """Validate an IRD number using the mod-11 checksum algorithm."""
    if len(digits) == 8:
        weights = _IRD_WEIGHTS_8
    elif len(digits) == 9:
        weights = _IRD_WEIGHTS_9
    else:
        return False

    # IRD numbers must be in the valid range
    number = int(digits)
    if number < 10_000_000 or number > 150_000_000:
        return False

    total = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total % 11
    return remainder == 0


class NzIrdRecognizer(PatternRecognizer):
    """Recogniser for New Zealand IRD (Inland Revenue Department) numbers.

    Uses pattern matching with checksum validation and context-word boosting.
    A bare 8–9 digit number matching the checksum scores ~0.4. With nearby context
    words like "IRD" or "inland revenue", the score is boosted above the default
    0.7 confidence threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="nz_ird",
                regex=_IRD_PATTERN,
                score=0.4,
            )
        ]
        super().__init__(
            supported_entity="NZ_IRD",
            patterns=patterns,
            context=_IRD_CONTEXT_WORDS,
            supported_language="en",
            name="NZ IRD Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the IRD checksum. Returns True to boost score, False to discard."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_ird(digits):
            return True
        return False
