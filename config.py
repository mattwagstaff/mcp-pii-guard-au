"""Configuration constants and defaults for mcp-pii-guard."""

from __future__ import annotations

import os
from typing import Final

SERVER_NAME: Final[str] = "mcp-pii-guard"
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
]

DEFAULT_ENTITY_TYPES: Final[list[str]] = STANDARD_ENTITIES + CUSTOM_ENTITIES

# Entity metadata for list_supported_entities
ENTITY_METADATA: Final[dict[str, dict]] = {
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
        "description": "Phone numbers in local or international formats",
        "frameworks": ["GDPR", "APPs", "HIPAA"],
        "examples": ["+61 2 9876 5432", "(02) 9876 5432"],
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
        "description": "Physical addresses, cities, and geographic locations",
        "frameworks": ["GDPR", "APPs", "HIPAA"],
        "examples": ["123 Pitt Street, Sydney NSW 2000"],
    },
    "MEDICAL_LICENSE": {
        "description": "Medical license or registration numbers",
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
    "AU_TFN": {
        "description": "Australian Tax File Number (8 or 9 digit with checksum validation)",
        "frameworks": ["APPs", "TAA"],
        "examples": ["123 456 782"],
    },
    "AU_MEDICARE": {
        "description": "Australian Medicare card number (10-digit with checksum validation)",
        "frameworks": ["APPs", "HIPAA"],
        "examples": ["2123 45670 1"],
    },
    "AU_ABN": {
        "description": "Australian Business Number (11-digit with ABN validation algorithm)",
        "frameworks": ["APPs", "ATO"],
        "examples": ["51 824 753 556"],
    },
}
