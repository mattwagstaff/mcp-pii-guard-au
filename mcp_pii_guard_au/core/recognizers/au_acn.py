"""Australian Company Number (ACN) recogniser.

ACNs are 9-digit numbers validated with a modulus-10 checksum:
1. Multiply digits 1–8 by weights [8, 7, 6, 5, 4, 3, 2, 1].
2. Sum the products.
3. Check digit = (10 - (sum % 10)) % 10.
4. The check digit must equal the 9th digit.

Context words like "ACN" or "company number" near the pattern boost confidence.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

_ACN_PATTERN = r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}\b"

_ACN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 1]

_ACN_CONTEXT_WORDS = [
    "acn",
    "australian company number",
    "company number",
    "company no",
    "asic",
    "registered company",
    "pty ltd",
    "proprietary limited",
]


def _validate_acn(digits: str) -> bool:
    """Validate an ACN using the modulus-10 checksum."""
    if len(digits) != 9:
        return False

    weighted_sum = sum(int(digits[i]) * _ACN_WEIGHTS[i] for i in range(8))
    check_digit = (10 - (weighted_sum % 10)) % 10
    return check_digit == int(digits[8])


class AuAcnRecognizer(PatternRecognizer):
    """Recogniser for Australian Company Numbers.

    Uses pattern matching with modulus-10 checksum validation and context-word
    boosting. The checksum is selective (~1 in 10 nine-digit numbers pass),
    and context words like "ACN" or "ASIC" further reduce false positives.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_acn",
                regex=_ACN_PATTERN,
                score=0.3,
            )
        ]
        super().__init__(
            supported_entity="AU_ACN",
            patterns=patterns,
            context=_ACN_CONTEXT_WORDS,
            supported_language="en",
            name="AU ACN Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the ACN checksum."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_acn(digits):
            return True
        return False
