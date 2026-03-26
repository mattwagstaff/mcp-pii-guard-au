"""Australian drivers licence number recogniser.

Licence formats vary by state/territory:
- NSW: 2 letters + 6 digits (e.g. AB123456) — most common modern format
- VIC: 1–10 digits
- QLD: 8 digits
- SA: 6 alphanumeric characters (e.g. A12345 or 123456)
- WA: 7 digits
- TAS: 5–7 alphanumeric
- NT: 5–7 digits
- ACT: 1–10 digits

Because these formats overlap heavily with other number types (phone numbers,
postcodes, generic IDs), this recogniser relies heavily on context words. The
base pattern score is deliberately low (0.2) — without nearby context like
"licence", "driver", or a state name, matches will fall below the default
0.7 confidence threshold and be filtered out.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

# NSW format: 2 letters + 6 digits
_NSW_PATTERN = r"\b[A-Z]{2}\d{6}\b"
# QLD format: 8 digits
_QLD_PATTERN = r"\b\d{8}\b"
# WA format: 7 digits
_WA_PATTERN = r"\b\d{7}\b"

_LICENCE_CONTEXT_WORDS = [
    "licence",
    "license",
    "driver licence",
    "drivers licence",
    "driver's licence",
    "driving licence",
    "licence number",
    "licence no",
    "licence #",
    "rms",
    "roads and maritime",
    "vicroads",
    "transport and main roads",
    "department of transport",
    "service nsw",
    "service sa",
    "myrta",
]


class AuDriversLicenceRecognizer(PatternRecognizer):
    """Recogniser for Australian drivers licence numbers.

    Covers the most common formats across Australian states. Due to the wide
    variation in formats and high overlap with other number types, this
    recogniser depends heavily on context words to achieve a useful confidence
    score. Without nearby keywords like "licence" or "driver", matches will
    score below the default threshold.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_licence_nsw",
                regex=_NSW_PATTERN,
                score=0.25,
            ),
            Pattern(
                name="au_licence_qld",
                regex=_QLD_PATTERN,
                score=0.15,
            ),
            Pattern(
                name="au_licence_wa",
                regex=_WA_PATTERN,
                score=0.15,
            ),
        ]
        super().__init__(
            supported_entity="AU_DRIVERS_LICENCE",
            patterns=patterns,
            context=_LICENCE_CONTEXT_WORDS,
            supported_language="en",
            name="AU Drivers Licence Recognizer",
        )
