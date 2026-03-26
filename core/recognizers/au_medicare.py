"""Australian Medicare card number recogniser.

Medicare numbers are 10 digits (plus an optional issue number digit, totalling 11
on the physical card). The first 8 digits are validated with a weighted checksum.
The 9th digit is a check digit. The 10th digit is the individual reference
number (IRN, 1-9).

Weights for digits 1-8: [1, 3, 7, 9, 1, 3, 7, 9].
The check digit (position 9) = (sum of weighted digits) mod 10.

Context words like "medicare" or "medicare card" near the pattern boost confidence.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# 10 digits, optional spaces/hyphens, with optional trailing issue number
_MEDICARE_PATTERN = r"\b\d{4}[\s\-]?\d{5}[\s\-]?\d{1}\b"

_MEDICARE_WEIGHTS = [1, 3, 7, 9, 1, 3, 7, 9]

_MEDICARE_CONTEXT_WORDS = [
    "medicare",
    "medicare card",
    "medicare number",
    "medicare no",
    "medicare #",
    "health card",
    "services australia",
]


def _validate_medicare(digits: str) -> bool:
    """Validate a Medicare number using the weighted checksum."""
    if len(digits) not in (10, 11):
        return False

    # First digit must be 2-6
    if digits[0] not in "23456":
        return False

    weighted_sum = sum(int(digits[i]) * _MEDICARE_WEIGHTS[i] for i in range(8))
    check_digit = weighted_sum % 10
    return check_digit == int(digits[8])


class AuMedicareRecognizer(PatternRecognizer):
    """Recogniser for Australian Medicare card numbers.

    Uses pattern matching with checksum validation and context-word boosting.
    The first digit must be 2-6, and the 9th digit must match the weighted
    checksum of digits 1-8.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_medicare",
                regex=_MEDICARE_PATTERN,
                score=0.4,
            )
        ]
        super().__init__(
            supported_entity="AU_MEDICARE",
            patterns=patterns,
            context=_MEDICARE_CONTEXT_WORDS,
            supported_language="en",
            name="AU Medicare Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the Medicare checksum."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_medicare(digits):
            return True
        return False
