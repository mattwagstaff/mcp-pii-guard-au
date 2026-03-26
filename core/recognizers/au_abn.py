"""Australian Business Number (ABN) recognizer.

ABNs are 11-digit numbers validated with the following algorithm:
1. Subtract 1 from the first digit.
2. Multiply each digit by its weight: [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19].
3. Sum the products.
4. The ABN is valid if the sum is divisible by 89.

Context words like "ABN" or "business number" near the pattern boost confidence.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

_ABN_PATTERN = r"\b\d{2}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}\b"

_ABN_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

_ABN_CONTEXT_WORDS = [
    "abn",
    "australian business number",
    "business number",
    "business no",
    "business #",
    "ato",
    "registered business",
    "gst",
    "bas",
]


def _validate_abn(digits: str) -> bool:
    """Validate an ABN using the official algorithm."""
    if len(digits) != 11:
        return False

    int_digits = [int(d) for d in digits]
    # Step 1: subtract 1 from the first digit
    int_digits[0] -= 1

    total = sum(d * w for d, w in zip(int_digits, _ABN_WEIGHTS))
    return total % 89 == 0


class AuAbnRecognizer(PatternRecognizer):
    """Recognizer for Australian Business Numbers.

    Uses pattern matching with the official ABN validation algorithm and
    context-word boosting. The checksum alone is highly selective (only ~1 in 89
    11-digit numbers pass), and context words like "ABN" further reduce false positives.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_abn",
                regex=_ABN_PATTERN,
                score=0.4,
            )
        ]
        super().__init__(
            supported_entity="AU_ABN",
            patterns=patterns,
            context=_ABN_CONTEXT_WORDS,
            supported_language="en",
            name="AU ABN Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the ABN checksum."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_abn(digits):
            return True
        return False
