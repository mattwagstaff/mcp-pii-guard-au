"""Configuration constants and defaults for mcp-pii-guard-au."""

from __future__ import annotations

import os
from typing import Final

SERVER_NAME: Final[str] = "mcp-pii-guard-au"
SERVER_VERSION: Final[str] = "0.1.0"

DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.7
DEFAULT_LANGUAGE: Final[str] = "en"

AUDIT_LOG_PATH: Final[str] = os.environ.get(
    "PII_GUARD_AUDIT_LOG", "./logs/pii_guard_audit.jsonl"
)

# Standard Presidio entity types
STANDARD_ENTITIES: Final[list[str]] = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "URL",
    "DATE_TIME",
    "LOCATION",
    "MEDICAL_LICENSE",
    "US_SSN",
    "US_PASSPORT",
    "US_BANK_NUMBER",
]

# Custom Australian entity types
CUSTOM_ENTITIES: Final[list[str]] = [
    "AU_TFN",
    "AU_MEDICARE",
    "AU_ABN",
    "AU_ACN",
    "AU_DRIVERS_LICENCE",
    "AU_PASSPORT",
    "AU_BSB",
    "AU_BANK_ACCOUNT",
    "AU_ADDRESS",
    "CENTRELINK_CRN",
]

DEFAULT_ENTITY_TYPES: Final[list[str]] = STANDARD_ENTITIES + CUSTOM_ENTITIES

# Entity metadata for list_supported_entities
ENTITY_METADATA: Final[dict[str, dict]] = {
    # --- Australian custom entities ---
    "AU_TFN": {
        "description": "Australian Tax File Number (8 or 9 digit with weighted mod-11 checksum)",
        "frameworks": ["APPs", "TAA"],
        "examples": ["123 456 782"],
    },
    "AU_MEDICARE": {
        "description": "Australian Medicare card number (10-digit with weighted mod-10 checksum)",
        "frameworks": ["APPs", "HIPAA"],
        "examples": ["2123 45670 1"],
    },
    "AU_ABN": {
        "description": "Australian Business Number (11-digit with mod-89 checksum)",
        "frameworks": ["APPs", "ATO"],
        "examples": ["51 824 753 556"],
    },
    "AU_ACN": {
        "description": "Australian Company Number (9-digit with modulus-10 checksum)",
        "frameworks": ["APPs", "ASIC"],
        "examples": ["005 499 981"],
    },
    "AU_DRIVERS_LICENCE": {
        "description": "Australian drivers licence number (format varies by state — NSW, VIC, QLD, SA, WA, TAS, NT, ACT)",
        "frameworks": ["APPs"],
        "examples": ["AB123456", "12345678"],
    },
    "AU_PASSPORT": {
        "description": "Australian passport number (1–2 letter prefix + 7 digits)",
        "frameworks": ["APPs", "DFAT"],
        "examples": ["PA1234567", "N1234567"],
    },
    "AU_BSB": {
        "description": "Australian BSB (Bank-State-Branch) number (6-digit bank branch identifier)",
        "frameworks": ["APPs", "PCI-DSS"],
        "examples": ["062-000", "033-123"],
    },
    "AU_BANK_ACCOUNT": {
        "description": "Australian bank account number (6–10 digits, typically paired with a BSB)",
        "frameworks": ["APPs", "PCI-DSS"],
        "examples": ["1234 5678", "123456789"],
    },
    "AU_ADDRESS": {
        "description": "Australian street or postal address (street number + name + type + suburb/state/postcode, or PO Box)",
        "frameworks": ["APPs", "GDPR"],
        "examples": ["123 Pitt Street, Sydney NSW 2000", "PO Box 456, Melbourne VIC 3001"],
    },
    "CENTRELINK_CRN": {
        "description": "Centrelink Customer Reference Number (9 digits + check letter, issued by Services Australia)",
        "frameworks": ["APPs", "Social Security Act"],
        "examples": ["123 456 789A"],
    },
    # --- Standard Presidio entities ---
    "PERSON": {
        "description": "Person names — first, last, or full names",
        "frameworks": ["GDPR", "APPs", "HIPAA", "SOX"],
        "examples": ["Jane Smith", "Dr. John Doe"],
    },
    "EMAIL_ADDRESS": {
        "description": "Email addresses in any standard format",
        "frameworks": ["GDPR", "APPs", "HIPAA"],
        "examples": ["user@domain.com"],
    },
    "PHONE_NUMBER": {
        "description": "Phone numbers in local or international formats (includes Australian mobile and landline)",
        "frameworks": ["GDPR", "APPs", "HIPAA"],
        "examples": ["+61 2 9876 5432", "0412 345 678"],
    },
    "CREDIT_CARD": {
        "description": "Credit or debit card numbers (Visa, MasterCard, Amex, etc.)",
        "frameworks": ["PCI-DSS", "GDPR", "APPs"],
        "examples": ["4111 1111 1111 1111"],
    },
    "IBAN_CODE": {
        "description": "International Bank Account Numbers",
        "frameworks": ["GDPR", "PCI-DSS", "SOX"],
        "examples": ["DE89 3704 0044 0532 0130 00"],
    },
    "IP_ADDRESS": {
        "description": "IPv4 and IPv6 addresses",
        "frameworks": ["GDPR"],
        "examples": ["192.168.1.1", "2001:0db8::1"],
    },
    "URL": {
        "description": "URLs and web addresses that may contain PII in paths or parameters",
        "frameworks": ["GDPR"],
        "examples": ["https://example.com/profile/john"],
    },
    "DATE_TIME": {
        "description": "Dates and times that may be personally identifying (e.g. date of birth)",
        "frameworks": ["GDPR", "HIPAA", "APPs"],
        "examples": ["15/03/1990", "March 15, 1990"],
    },
    "LOCATION": {
        "description": "Physical addresses, cities, and geographic locations (generic NLP — see AU_ADDRESS for Australian-specific detection)",
        "frameworks": ["GDPR", "APPs", "HIPAA"],
        "examples": ["Sydney", "Melbourne CBD"],
    },
    "MEDICAL_LICENSE": {
        "description": "Medical licence or registration numbers",
        "frameworks": ["HIPAA"],
        "examples": ["MD12345"],
    },
    "US_SSN": {
        "description": "US Social Security Numbers",
        "frameworks": ["SOX", "HIPAA"],
        "examples": ["123-45-6789"],
    },
    "US_PASSPORT": {
        "description": "US passport numbers",
        "frameworks": ["GDPR", "SOX"],
        "examples": ["A12345678"],
    },
    "US_BANK_NUMBER": {
        "description": "US bank account numbers",
        "frameworks": ["SOX", "PCI-DSS"],
        "examples": ["1234567890"],
    },
}
