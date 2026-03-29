"""Australian bank account number recogniser.

Australian bank account numbers are 6–10 digits. They always appear alongside
a BSB number in practice (payroll, invoicing, direct debit forms). Because
bare 6–10 digit numbers are extremely common in text, this recogniser relies
entirely on context words to achieve a useful confidence score. Without nearby
keywords like "account", "BSB", "bank", or "direct deposit", matches will
score well below the default threshold.

There is no public checksum algorithm for Australian bank account numbers.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

# 6-10 digits, optionally separated by spaces or hyphens
_ACCOUNT_PATTERN = r"\b\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{0,4}\b"

_ACCOUNT_CONTEXT_WORDS = [
    "account",
    "account number",
    "account no",
    "account #",
    "acc",
    "acct",
    "bank account",
    "bsb",
    "direct deposit",
    "direct debit",
    "eft",
    "payment details",
    "remittance",
    "bank details",
]


class AuBankAccountRecognizer(PatternRecognizer):
    """Recogniser for Australian bank account numbers.

    Matches 6–10 digit sequences and relies heavily on context words for
    confidence boosting. Without nearby financial context, these short digit
    sequences will not reach the default confidence threshold — this is
    intentional to avoid false positives on phone numbers, postcodes, and
    other numeric data.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="au_bank_account",
                regex=_ACCOUNT_PATTERN,
                score=0.1,
            )
        ]
        super().__init__(
            supported_entity="AU_BANK_ACCOUNT",
            patterns=patterns,
            context=_ACCOUNT_CONTEXT_WORDS,
            supported_language="en",
            name="AU Bank Account Recognizer",
        )
