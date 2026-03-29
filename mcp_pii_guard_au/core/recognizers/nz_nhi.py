"""New Zealand NHI (National Health Index) number recogniser.

NHI numbers uniquely identify individuals within New Zealand's health system.
The traditional format is 3 letters + 4 digits (e.g. ABC1234), where the last
digit is a check digit calculated using a mod-11 algorithm.

Letters are assigned numeric values: A=1, B=2, ..., Z=26 (I and O are excluded
from valid NHI numbers to avoid confusion with 1 and 0).

The 2022+ format uses 3 letters + 2 digits + 2 letters, but the traditional
format remains the most common in existing records.

Context words like "NHI" or "national health index" near the pattern boost
confidence to reduce false positives.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# Traditional format: 3 letters + 4 digits
_NHI_PATTERN = r"\b[A-HJ-NP-Z]{3}\d{4}\b"

# Letter-to-number mapping (I and O excluded)
_NHI_ALPHA_VALUES = {
    chr(c): i for i, c in enumerate(range(ord("A"), ord("Z") + 1), start=1)
    if chr(c) not in ("I", "O")
}

_NHI_CONTEXT_WORDS = [
    "nhi",
    "nhi number",
    "nhi no",
    "nhi #",
    "national health index",
    "health index",
    "health number",
    "patient number",
    "patient id",
    "nz health",
    "new zealand health",
    "ministry of health",
    "te whatu ora",
    "health nz",
]


def _validate_nhi(text: str) -> bool:
    """Validate an NHI number using the mod-11 check digit algorithm."""
    text = text.upper().strip()

    if len(text) != 7:
        return False

    letters = text[:3]
    digits = text[3:]

    # Letters must not contain I or O
    if any(c in ("I", "O") for c in letters):
        return False

    # Calculate check digit
    # Letters at positions 1-3, digits at positions 4-6, check digit at position 7
    total = 0
    for i, c in enumerate(letters):
        if c not in _NHI_ALPHA_VALUES:
            return False
        total += _NHI_ALPHA_VALUES[c] * (7 - i)

    for i, d in enumerate(digits[:3]):
        total += int(d) * (4 - i)

    remainder = total % 11

    # Check digit is 11 - remainder, mapped to 0 if result is 10
    # A remainder of 0 is invalid
    if remainder == 0:
        return False

    check = 11 - remainder
    if check == 10:
        check = 0

    return check == int(digits[3])


class NzNhiRecognizer(PatternRecognizer):
    """Recogniser for New Zealand NHI (National Health Index) numbers.

    Uses pattern matching with check digit validation and context-word boosting.
    The pattern requires 3 letters (excluding I and O) followed by 4 digits.
    With nearby context words like "NHI" or "health index", the score is boosted
    above the default 0.7 confidence threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="nz_nhi",
                regex=_NHI_PATTERN,
                score=0.4,
            )
        ]
        super().__init__(
            supported_entity="NZ_NHI",
            patterns=patterns,
            context=_NHI_CONTEXT_WORDS,
            supported_language="en",
            name="NZ NHI Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the NHI check digit. Returns True to boost score, False to discard."""
        cleaned = re.sub(r"\s", "", pattern_text)
        if _validate_nhi(cleaned):
            return True
        return False
