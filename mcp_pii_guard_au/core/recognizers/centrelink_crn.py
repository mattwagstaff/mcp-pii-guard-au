"""Centrelink Customer Reference Number (CRN) recogniser.

CRNs are issued by Services Australia (formerly Centrelink) and consist of
9 digits followed by a single letter suffix (e.g. 123 456 789A). The letter
is a check character derived from the digits.

The check letter algorithm:
1. Multiply each of the 9 digits by weights [1, 2, 3, 4, 5, 6, 7, 8, 9].
2. Sum the products.
3. The remainder when divided by 26 maps to a letter (0=A, 1=B, ..., 25=Z).
4. The check letter must match the suffix.

Context words like "CRN", "Centrelink", or "Services Australia" near the
pattern boost confidence.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# 9 digits + 1 letter, with optional spaces
_CRN_PATTERN = r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?[A-Za-z]\b"

_CRN_WEIGHTS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

_CRN_CONTEXT_WORDS = [
    "crn",
    "customer reference number",
    "customer reference no",
    "centrelink",
    "services australia",
    "mygovid",
    "mygov",
    "welfare",
    "social services",
    "family tax benefit",
    "jobseeker",
    "youth allowance",
    "austudy",
    "pension",
    "carer payment",
]


def _validate_crn(digits: str, check_letter: str) -> bool:
    """Validate a CRN using the weighted checksum + letter algorithm."""
    if len(digits) != 9:
        return False

    weighted_sum = sum(int(digits[i]) * _CRN_WEIGHTS[i] for i in range(9))
    expected_index = weighted_sum % 26
    expected_letter = chr(ord("A") + expected_index)
    return check_letter.upper() == expected_letter


class CentrelinkCrnRecognizer(PatternRecognizer):
    """Recogniser for Centrelink Customer Reference Numbers (CRN).

    Matches 9-digit + letter sequences and validates using the weighted
    checksum algorithm. Context words like "CRN", "Centrelink", and
    "Services Australia" boost confidence.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="centrelink_crn",
                regex=_CRN_PATTERN,
                score=0.35,
            )
        ]
        super().__init__(
            supported_entity="CENTRELINK_CRN",
            patterns=patterns,
            context=_CRN_CONTEXT_WORDS,
            supported_language="en",
            name="Centrelink CRN Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the CRN check letter."""
        clean = re.sub(r"[\s\-]", "", pattern_text)
        if len(clean) < 2:
            return False
        digits = clean[:-1]
        check_letter = clean[-1]
        if not digits.isdigit() or not check_letter.isalpha():
            return False
        if _validate_crn(digits, check_letter):
            return True
        return False
