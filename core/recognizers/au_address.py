"""Australian address recogniser.

Detects Australian street addresses using a combination of patterns:
1. Street number + street name + street type + optional suburb/state/postcode
2. PO Box / GPO Box patterns
3. State abbreviation + 4-digit postcode as a trailing anchor

Australian postcodes:
  0200–0299  ACT
  0800–0999  NT
  1000–1999  NSW (PO Boxes)
  2000–2599  NSW
  2600–2618  ACT
  2619–2899  NSW
  2900–2920  ACT
  3000–3999  VIC
  4000–4999  QLD
  5000–5799  SA
  6000–6797  WA
  7000–7999  TAS

Street types cover standard Australian abbreviations (St, Rd, Ave, Dr, Cres,
Pl, Ct, Ln, Tce, Hwy, Bvd, Cl, Pde, Cct, etc.).

Context words boost confidence but are less critical here because the
structural patterns (number + name + type + state + postcode) are already
quite specific.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

# Common Australian street type abbreviations and full forms
_STREET_TYPES = (
    r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Boulevard|Bvd|Blvd|"
    r"Crescent|Cres|Cr|Place|Pl|Court|Ct|Lane|Ln|Terrace|Tce|"
    r"Highway|Hwy|Parade|Pde|Circuit|Cct|Close|Cl|Way|"
    r"Grove|Gr|Rise|Outlook|View|Walk|Square|Sq)"
)

# Australian state/territory abbreviations
_STATES = r"(?:NSW|VIC|QLD|SA|WA|TAS|NT|ACT)"

# 4-digit Australian postcode
_POSTCODE = r"\d{4}"

# Full street address: number + street name + street type + optional suburb, state, postcode
# e.g. "123 Pitt Street, Sydney NSW 2000"  or  "45 Smith St Sydney 2000"
_STREET_ADDRESS_PATTERN = (
    r"\b\d{1,5}(?:[\/\-]\d{1,5})?\s+"           # street number, optional unit (e.g. 3/45)
    r"[A-Z][a-zA-Z\s\-']{1,40}\s+"              # street name
    + _STREET_TYPES +                             # street type
    r"(?:\s*,?\s+[A-Z][a-zA-Z\s\-']{1,30})?"    # optional suburb
    r"(?:\s+(?:" + _STATES + r"))?"              # optional state
    r"(?:\s+" + _POSTCODE + r")?"                # optional postcode
)

# PO Box pattern: "PO Box 1234, Suburb STATE 0000"
_PO_BOX_PATTERN = (
    r"\b(?:PO|GPO|P\.?O\.?)\s*Box\s+\d{1,6}"
    r"(?:\s*,?\s+[A-Z][a-zA-Z\s\-']{1,30})?"
    r"(?:\s+(?:" + _STATES + r"))?"
    r"(?:\s+" + _POSTCODE + r")?"
)

# State + postcode anchor: "NSW 2000", "VIC 3000"
_STATE_POSTCODE_PATTERN = r"\b" + _STATES + r"\s+" + _POSTCODE + r"\b"

_ADDRESS_CONTEXT_WORDS = [
    "address",
    "street",
    "road",
    "avenue",
    "suburb",
    "postcode",
    "postal",
    "residential",
    "delivery",
    "mailing",
    "billing",
    "shipping",
    "home address",
    "work address",
    "business address",
    "unit",
    "apartment",
    "level",
    "floor",
    "suite",
]


class AuAddressRecognizer(PatternRecognizer):
    """Recogniser for Australian street and postal addresses.

    Uses multiple patterns to catch full street addresses (e.g.
    "123 Pitt Street, Sydney NSW 2000"), PO Box addresses, and
    state + postcode fragments. Street addresses score highest due
    to their structural specificity; state+postcode fragments score
    lowest and rely on context words for confidence.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_street_address",
                regex=_STREET_ADDRESS_PATTERN,
                score=0.55,
            ),
            Pattern(
                name="au_po_box",
                regex=_PO_BOX_PATTERN,
                score=0.6,
            ),
            Pattern(
                name="au_state_postcode",
                regex=_STATE_POSTCODE_PATTERN,
                score=0.2,
            ),
        ]
        super().__init__(
            supported_entity="AU_ADDRESS",
            patterns=patterns,
            context=_ADDRESS_CONTEXT_WORDS,
            supported_language="en",
            name="AU Address Recognizer",
        )
