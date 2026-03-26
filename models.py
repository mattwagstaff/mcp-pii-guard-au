"""Pydantic models for mcp-pii-guard request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    """A single PII entity detected in text."""

    type: str = Field(description="Entity type, e.g. EMAIL_ADDRESS, AU_TFN")
    text: str = Field(description="The matched text span")
    start: int = Field(description="Start character offset in the input text")
    end: int = Field(description="End character offset in the input text")
    confidence: float = Field(description="Presidio confidence score (0.0–1.0)")


class DetectPiiResult(BaseModel):
    """Result of a PII detection scan."""

    entity_count: int
    entities: list[DetectedEntity]
    has_pii: bool
    scan_id: str


class SanitizeTextResult(BaseModel):
    """Result of sanitizing a single text string."""

    original_length: int
    sanitized_text: str
    entities_removed: int
    entity_types_found: list[str]
    mode: Literal["redact", "replace", "tokenize"]
    scan_id: str
    audit_logged: bool


class SanitizeDocumentResult(BaseModel):
    """Result of sanitizing a multi-field document."""

    sanitized_document: dict
    fields_processed: int
    fields_sanitized: int
    total_entities_removed: int
    entity_summary: dict[str, int]
    scan_id: str


class EntityInfo(BaseModel):
    """Metadata about a supported entity type."""

    type: str
    description: str
    frameworks: list[str]
    examples: list[str]


class SupportedEntitiesResult(BaseModel):
    """Full list of supported entity types."""

    entities: list[EntityInfo]
