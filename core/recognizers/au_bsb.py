"""Australian BSB (Bank-State-Branch) number recogniser.

BSB numbers are 6-digit codes formatted as XXX-XXX that identify a bank branch.
The first two digits indicate the financial institution:

  01 = ANZ (SA/WA)     03 = Westpac          06 = CBA
  08 = NAB             11-19 = Various banks  21-27 = Various banks
  30-39 = Bankwest, HSBC, etc.
  48-49 = Macquarie    50-59 = Various credit unions
  61-69 = Bendigo, Bank of Queensland, etc.
  70-79 = Various      80-89 = Credit unions, Cuscal
  90-99 = Various

Context words like "BSB", "bank", or "branch" near the pattern boost confidence.
"""

from __future__ import annotations

import re

from presidio_analyzer import Pattern, PatternRecognizer

# 6 digits with optional hyphen: XXX-XXX or XXXXXX
_BSB_PATTERN = r"\b\d{3}[\-\s]?\d{3}\b"

# Valid first-two-digit prefixes for Australian BSBs
_VALID_BSB_PREFIXES = {
    "01", "03", "06", "08",
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "21", "22", "23", "24", "25", "26", "27",
    "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
    "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "90", "91", "92", "93", "94", "95", "96", "97", "98", "99",
}

_BSB_CONTEXT_WORDS = [
    "bsb",
    "bsb number",
    "bsb no",
    "bank",
    "bank details",
    "branch",
    "branch number",
    "bank account",
    "direct deposit",
    "direct debit",
    "eft",
    "electronic funds transfer",
    "remittance",
    "payment details",
]


def _validate_bsb(digits: str) -> bool:
    """Validate a BSB prefix against known Australian bank prefixes."""
    if len(digits) != 6:
        return False
    prefix = digits[:2]
    return prefix in _VALID_BSB_PREFIXES


class AuBsbRecognizer(PatternRecognizer):
    """Recogniser for Australian BSB (Bank-State-Branch) numbers.

    Matches 6-digit codes formatted as XXX-XXX, validates the first two digits
    against known Australian financial institution prefixes, and uses context
    words like "BSB", "bank details", and "direct deposit" for confidence
    boosting.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_bsb",
                regex=_BSB_PATTERN,
                score=0.2,
            )
        ]
        super().__init__(
            supported_entity="AU_BSB",
            patterns=patterns,
            context=_BSB_CONTEXT_WORDS,
            supported_language="en",
            name="AU BSB Recognizer",
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        """Validate the BSB prefix against known bank prefixes."""
        digits = re.sub(r"\D", "", pattern_text)
        if _validate_bsb(digits):
            return True
        return False
