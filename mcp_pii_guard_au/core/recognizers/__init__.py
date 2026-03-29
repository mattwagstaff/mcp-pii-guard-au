"""Custom Australian and New Zealand PII recognisers for Presidio."""

from .au_abn import AuAbnRecognizer
from .au_acn import AuAcnRecognizer
from .au_address import AuAddressRecognizer
from .au_bank_account import AuBankAccountRecognizer
from .au_bsb import AuBsbRecognizer
from .au_drivers_licence import AuDriversLicenceRecognizer
from .au_medicare import AuMedicareRecognizer
from .au_passport import AuPassportRecognizer
from .au_phone import AuPhoneRecognizer
from .au_tfn import AuTfnRecognizer
from .centrelink_crn import CentrelinkCrnRecognizer
from .nz_drivers_licence import NzDriversLicenceRecognizer
from .nz_ird import NzIrdRecognizer
from .nz_nhi import NzNhiRecognizer

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
    "AuPhoneRecognizer",
    "CentrelinkCrnRecognizer",
    "NzIrdRecognizer",
    "NzNhiRecognizer",
    "NzDriversLicenceRecognizer",
]
