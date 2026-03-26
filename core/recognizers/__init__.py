"""Custom Australian PII recognisers for Presidio."""

from core.recognizers.au_abn import AuAbnRecognizer
from core.recognizers.au_acn import AuAcnRecognizer
from core.recognizers.au_address import AuAddressRecognizer
from core.recognizers.au_bank_account import AuBankAccountRecognizer
from core.recognizers.au_bsb import AuBsbRecognizer
from core.recognizers.au_drivers_licence import AuDriversLicenceRecognizer
from core.recognizers.au_medicare import AuMedicareRecognizer
from core.recognizers.au_passport import AuPassportRecognizer
from core.recognizers.au_tfn import AuTfnRecognizer
from core.recognizers.centrelink_crn import CentrelinkCrnRecognizer

__all__ = [
    "AuTfnRecognizer",
    "AuMedicareRecognizer",
    "AuAbnRecognizer",
    "AuAcnRecognizer",
    "AuDriversLicenceRecognizer",
    "AuPassportRecognizer",
    "AuBsbRecognizer",
    "AuBankAccountRecognizer",
    "AuAddressRecognizer",
    "CentrelinkCrnRecognizer",
]
