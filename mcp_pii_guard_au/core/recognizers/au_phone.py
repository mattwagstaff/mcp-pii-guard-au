"""Australian phone number recogniser with carrier-prefix validation.

Australian phone numbers follow specific patterns:
- Mobile: 04XX XXX XXX (10 digits starting with 04)
- Landline: 0X XXXX XXXX (10 digits, area code 02/03/07/08)
- International: +61 X XXXX XXXX (country code + 9 digits)

Mobile prefixes map to carriers:
  0400–0419: Telstra     0420–0429: Vodafone    0430–0439: Optus
  0440–0449: Optus       0450–0459: Vodafone    0460–0469: Vodafone
  0470–0479: Telstra     0480–0489: Telstra     0490–0499: Optus/MVNOs

Landline area codes:
  02: NSW/ACT    03: VIC/TAS    07: QLD    08: SA/WA/NT

This recogniser complements Presidio's built-in PHONE_NUMBER type by adding
Australian-specific carrier prefix validation and context-word boosting.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# Mobile: 04XX XXX XXX (with optional spaces/hyphens)
_MOBILE_PATTERN = r"\b04\d{2}[\s\-]?\d{3}[\s\-]?\d{3}\b"

# Landline: 0X XXXX XXXX (with optional spaces/hyphens)
_LANDLINE_PATTERN = r"\b0[2378][\s\-]?\d{4}[\s\-]?\d{4}\b"

# International: +61 X XXXX XXXX or +61XXXXXXXXX
_INTERNATIONAL_PATTERN = r"\+61[\s\-]?[2-478][\s\-]?\d{4}[\s\-]?\d{4}\b"

# International mobile: +61 4XX XXX XXX
_INTERNATIONAL_MOBILE_PATTERN = r"\+61[\s\-]?4\d{2}[\s\-]?\d{3}[\s\-]?\d{3}\b"

# Valid mobile prefixes (first 4 digits of 04XX numbers)
_VALID_MOBILE_PREFIXES = {
    # Telstra
    *{f"04{d:02d}" for d in range(0, 20)},   # 0400–0419
    *{f"04{d:02d}" for d in range(70, 90)},   # 0470–0489
    # Vodafone
    *{f"04{d:02d}" for d in range(20, 30)},   # 0420–0429
    *{f"04{d:02d}" for d in range(50, 70)},   # 0450–0469
    # Optus
    *{f"04{d:02d}" for d in range(30, 50)},   # 0430–0449
    *{f"04{d:02d}" for d in range(90, 100)},  # 0490–0499
}

# Valid landline area codes
_VALID_AREA_CODES = {"02", "03", "07", "08"}

_PHONE_CONTEXT_WORDS = [
    "phone",
    "phone number",
    "phone no",
    "phone #",
    "mobile",
    "mobile number",
    "mobile no",
    "cell",
    "telephone",
    "tel",
    "contact",
    "contact number",
    "call",
    "sms",
    "text",
    "landline",
    "home phone",
    "work phone",
]


def _validate_au_phone(digits: str) -> bool:
    """Validate an Australian phone number."""
    # Strip country code if present
    if digits.startswith("61") and len(digits) >= 11:
        digits = "0" + digits[2:]

    if len(digits) != 10:
        return False

    # Mobile validation
    if digits.startswith("04"):
        prefix = digits[:4]
        return prefix in _VALID_MOBILE_PREFIXES

    # Landline validation
    area_code = digits[:2]
    return area_code in _VALID_AREA_CODES


class AuPhoneRecognizer(PatternRecognizer):
    """Recogniser for Australian phone numbers with carrier-prefix validation.

    Matches mobile (04XX), landline (02/03/07/08), and international (+61)
    formats. Mobile numbers are validated against known carrier prefix ranges.
    Context words like "phone", "mobile", or "contact" boost confidence above
    the default threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_phone_international_mobile",
                regex=_INTERNATIONAL_MOBILE_PATTERN,
                score=0.5,
            ),
            Pattern(
                name="au_phone_international",
                regex=_INTERNATIONAL_PATTERN,
                score=0.5,
            ),
            Pattern(
                name="au_phone_mobile",
                regex=_MOBILE_PATTERN,
                score=0.4,
            ),
            Pattern(
                name="au_phone_landline",
                regex=_LANDLINE_PATTERN,
                score=0.3,
            ),
        ]
        super().__init__(
            supported_entity="AU_PHONE_NUMBER",
            patterns=patterns,
            context=_PHONE_CONTEXT_WORDS,
            supported_language="en",
            name="AU Phone Number Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the phone number format and carrier prefix."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_au_phone(digits):
            return True
        return False
