"""mcp-pii-guard-au — MCP server for PII detection and sanitisation.

A compliance-first MCP server for regulated industries. Detects and sanitises
personally identifiable information using Microsoft Presidio before text
reaches an LLM or is stored/transmitted.

Supports GDPR, Australian Privacy Act (APPs), SOX, HIPAA, and PCI-DSS entities.
"""

from __future__ import annotations

import sys
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

from mcp.server.fastmcp import FastMCP

from .config import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_LANGUAGE,
    ENTITY_METADATA,
    SERVER_NAME,
    SERVER_VERSION,
)
from .core.audit import configure_audit_logger, log_scan
from .core.detector import create_analyzer, detect
from .core.sanitizer import create_anonymizer, sanitize
from .models import (
    DetectedEntity,
    DetectPiiResult,
    DetokenizeResult,
    EntityInfo,
    SanitizeDocumentResult,
    SanitizeTextResult,
    SupportedEntitiesResult,
)

# In-memory token mapping store, keyed by scan_id.
# Mappings are session-scoped — they are lost when the server process exits.
# This is deliberate: token mappings contain original PII values and should
# not be persisted to disk.
_token_mappings: dict[str, dict[str, str]] = {}


def _check_spacy_model() -> None:
    """Verify that the spaCy model is installed. Exit with a clear message if not."""
    try:
        import spacy

        spacy.load("en_core_web_lg")
    except OSError:
        print(
            "ERROR: spaCy model 'en_core_web_lg' is not installed.\n"
            "Install it with: python -m spacy download en_core_web_lg",
            file=sys.stderr,
        )
        sys.exit(1)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Initialise Presidio engines and audit logger on startup."""
    _check_spacy_model()

    analyzer = create_analyzer()
    anonymizer = create_anonymizer()
    audit_logger = configure_audit_logger()

    yield {
        "analyzer": analyzer,
        "anonymizer": anonymizer,
        "audit_logger": audit_logger,
    }


mcp = FastMCP(
    SERVER_NAME,
    version=SERVER_VERSION,
    lifespan=app_lifespan,
)


@mcp.tool()
def detect_pii(
    text: str,
    language: str = DEFAULT_LANGUAGE,
    entity_types: list[str] | None = None,
    min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
    entity_thresholds: dict[str, float] | None = None,
    audit: bool = True,
) -> dict:
    """Scan text and return all detected PII entities without modifying the text.

    Use this tool when you need to inspect what PII exists in text before deciding
    what to do with it. Returns entity types, positions, and confidence scores.

    Do NOT send text that has already been sanitised — it will find nothing.
    Do NOT use this if you want the text cleaned; use sanitize_text instead.

    Args:
        text: The text to scan for PII.
        language: Language code (default "en").
        entity_types: Optional list of specific entity types to look for.
                      If omitted, scans for all supported types.
        min_confidence: Minimum confidence threshold (0.0–1.0). Default 0.7.
        entity_thresholds: Optional per-entity-type confidence overrides.
            E.g. {"AU_ADDRESS": 0.9, "PERSON": 0.5}. Types not listed use
            min_confidence.
        audit: Whether to write an audit log entry. Default True.
    """
    ctx = mcp.get_context()
    lifespan_state = ctx.request_context.lifespan_context

    scan_id = str(uuid.uuid4())

    try:
        results = detect(
            lifespan_state["analyzer"],
            text,
            language=language,
            entity_types=entity_types,
            min_confidence=min_confidence,
            entity_thresholds=entity_thresholds,
        )

        entities = [
            DetectedEntity(
                type=r.entity_type,
                text=text[r.start : r.end],
                start=r.start,
                end=r.end,
                confidence=round(r.score, 4),
            )
            for r in results
        ]

        result = DetectPiiResult(
            entity_count=len(entities),
            entities=entities,
            has_pii=len(entities) > 0,
            scan_id=scan_id,
        )

        if audit:
            log_scan(
                lifespan_state["audit_logger"],
                scan_id=scan_id,
                tool="detect_pii",
                entity_types_detected=list({e.type for e in entities}),
                entity_count=len(entities),
                text_length=len(text),
                min_confidence=min_confidence,
                language=language,
            )

        return result.model_dump()

    except Exception as e:
        return {"error": str(e), "scan_id": scan_id}


@mcp.tool()
def sanitize_text(
    text: str,
    mode: Literal["redact", "replace", "tokenize"] = "redact",
    entity_types: list[str] | None = None,
    min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
    entity_thresholds: dict[str, float] | None = None,
    audit: bool = True,
) -> dict:
    """Detect and remove PII from text in a single operation. This is the most
    commonly used tool — call it when you need clean text safe to pass to an LLM,
    store in a database, or include in a response.

    Three modes:
    - "redact": replaces PII with [REDACTED:TYPE] labels (safest, default)
    - "replace": replaces PII with Presidio's default type-labelled placeholders
    - "tokenize": replaces PII with stable tokens like {{EMAIL_1}} (useful if you
      need to reference the same entity later without exposing the value).
      Use detokenize_text with the returned scan_id to reverse tokenisation.

    Do NOT send already-sanitised text through this tool again.
    Do NOT use this for structured documents (dicts/JSON) — use sanitize_document.

    Args:
        text: The text to sanitise.
        mode: Sanitisation strategy. Default "redact".
        entity_types: Optional filter for specific entity types.
        min_confidence: Minimum confidence threshold. Default 0.7.
        entity_thresholds: Optional per-entity-type confidence overrides.
            E.g. {"AU_ADDRESS": 0.9, "PERSON": 0.5}. Types not listed use
            min_confidence.
        audit: Whether to write an audit log entry. Default True.
    """
    ctx = mcp.get_context()
    lifespan_state = ctx.request_context.lifespan_context

    scan_id = str(uuid.uuid4())

    try:
        results = detect(
            lifespan_state["analyzer"],
            text,
            entity_types=entity_types,
            min_confidence=min_confidence,
            entity_thresholds=entity_thresholds,
        )

        sanitize_result = sanitize(
            lifespan_state["anonymizer"],
            text,
            results,
            mode=mode,
        )

        # Store token mapping for de-tokenisation if in tokenize mode
        has_mapping = bool(sanitize_result.token_mapping)
        if has_mapping:
            _token_mappings[scan_id] = sanitize_result.token_mapping

        entity_types_found = sorted({r.entity_type for r in results})

        result = SanitizeTextResult(
            original_length=len(text),
            sanitized_text=sanitize_result.text,
            entities_removed=len(results),
            entity_types_found=entity_types_found,
            mode=mode,
            scan_id=scan_id,
            audit_logged=audit,
            has_token_mapping=has_mapping,
        )

        if audit:
            log_scan(
                lifespan_state["audit_logger"],
                scan_id=scan_id,
                tool="sanitize_text",
                entity_types_detected=entity_types_found,
                entity_count=len(results),
                mode=mode,
                text_length=len(text),
                min_confidence=min_confidence,
            )

        return result.model_dump()

    except Exception as e:
        return {"error": str(e), "scan_id": scan_id}


def _sanitize_document_recursive(
    obj: object,
    *,
    lifespan_state: dict,
    mode: Literal["redact", "replace", "tokenize"],
    skip_fields: set[str],
    min_confidence: float,
    entity_thresholds: dict[str, float] | None,
    stats: dict,
) -> object:
    """Recursively walk a document and sanitise all string values."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key in skip_fields:
                result[key] = value
            else:
                result[key] = _sanitize_document_recursive(
                    value,
                    lifespan_state=lifespan_state,
                    mode=mode,
                    skip_fields=skip_fields,
                    min_confidence=min_confidence,
                    entity_thresholds=entity_thresholds,
                    stats=stats,
                )
        return result
    elif isinstance(obj, list):
        return [
            _sanitize_document_recursive(
                item,
                lifespan_state=lifespan_state,
                mode=mode,
                skip_fields=skip_fields,
                min_confidence=min_confidence,
                entity_thresholds=entity_thresholds,
                stats=stats,
            )
            for item in obj
        ]
    elif isinstance(obj, str):
        stats["fields_processed"] += 1

        results = detect(
            lifespan_state["analyzer"],
            obj,
            min_confidence=min_confidence,
            entity_thresholds=entity_thresholds,
        )

        if results:
            stats["fields_sanitized"] += 1
            stats["total_entities_removed"] += len(results)
            for r in results:
                stats["entity_summary"][r.entity_type] += 1

            sanitize_result = sanitize(
                lifespan_state["anonymizer"],
                obj,
                results,
                mode=mode,
            )
            return sanitize_result.text
        return obj
    else:
        # Numbers, booleans, None — pass through unchanged
        return obj


@mcp.tool()
def sanitize_document(
    document: dict,
    mode: Literal["redact", "replace", "tokenize"] = "redact",
    skip_fields: list[str] | None = None,
    min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
    entity_thresholds: dict[str, float] | None = None,
    audit: bool = True,
) -> dict:
    """Sanitise all string fields in a JSON document (dict) recursively. Use this
    for structured data like CRM records, customer objects, form submissions, or
    any multi-field object where PII might appear in multiple places.

    Walks every nested string value and applies PII detection and sanitisation.
    Non-string values (numbers, booleans, nulls) are passed through unchanged.

    Do NOT use this for plain text — use sanitize_text instead.
    Do NOT send documents with binary data or encoded content.

    Args:
        document: A JSON-serialisable dict to sanitise.
        mode: Sanitisation strategy. Default "redact".
        skip_fields: Field names to skip (e.g. ["id", "created_at"]).
        min_confidence: Minimum confidence threshold. Default 0.7.
        entity_thresholds: Optional per-entity-type confidence overrides.
            E.g. {"AU_ADDRESS": 0.9, "PERSON": 0.5}. Types not listed use
            min_confidence.
        audit: Whether to write an audit log entry. Default True.
    """
    ctx = mcp.get_context()
    lifespan_state = ctx.request_context.lifespan_context

    scan_id = str(uuid.uuid4())

    try:
        stats: dict = {
            "fields_processed": 0,
            "fields_sanitized": 0,
            "total_entities_removed": 0,
            "entity_summary": Counter(),
        }

        sanitized_doc = _sanitize_document_recursive(
            document,
            lifespan_state=lifespan_state,
            mode=mode,
            skip_fields=set(skip_fields) if skip_fields else set(),
            min_confidence=min_confidence,
            entity_thresholds=entity_thresholds,
            stats=stats,
        )

        result = SanitizeDocumentResult(
            sanitized_document=sanitized_doc,
            fields_processed=stats["fields_processed"],
            fields_sanitized=stats["fields_sanitized"],
            total_entities_removed=stats["total_entities_removed"],
            entity_summary=dict(stats["entity_summary"]),
            scan_id=scan_id,
        )

        if audit:
            log_scan(
                lifespan_state["audit_logger"],
                scan_id=scan_id,
                tool="sanitize_document",
                entity_types_detected=list(stats["entity_summary"].keys()),
                entity_count=stats["total_entities_removed"],
                mode=mode,
                min_confidence=min_confidence,
            )

        return result.model_dump()

    except Exception as e:
        return {"error": str(e), "scan_id": scan_id}


@mcp.tool()
def detokenize_text(
    text: str,
    scan_id: str,
    audit: bool = True,
) -> dict:
    """Reverse tokenisation by replacing tokens with their original values.

    After calling sanitize_text with mode="tokenize", the returned scan_id can be
    used here to reverse the tokens back to original PII values. This is useful
    for workflows where PII must be temporarily hidden but later restored —
    for example, processing text through an LLM and then reinserting names or
    addresses into the final output.

    Token mappings are session-scoped — they exist only while the server process
    is running and are never persisted to disk. If the server restarts, all
    mappings are lost. This is a deliberate security design: original PII values
    are never written to storage.

    Do NOT call this with a scan_id from a redact or replace operation — those
    modes are irreversible by design.

    Args:
        text: The tokenised text containing tokens like {{EMAIL_ADDRESS_1}}.
        scan_id: The scan_id returned by the original sanitize_text call.
        audit: Whether to write an audit log entry. Default True.
    """
    ctx = mcp.get_context()
    lifespan_state = ctx.request_context.lifespan_context

    try:
        mapping = _token_mappings.get(scan_id)
        if mapping is None:
            return {
                "error": (
                    f"No token mapping found for scan_id '{scan_id}'. "
                    "Either the scan_id is incorrect, the original sanitize_text "
                    "call did not use mode='tokenize', or the server has restarted "
                    "since the original call (mappings are session-scoped)."
                ),
                "scan_id": scan_id,
            }

        restored = text
        tokens_reversed = 0
        for token, original_value in mapping.items():
            if token in restored:
                restored = restored.replace(token, original_value)
                tokens_reversed += 1

        result = DetokenizeResult(
            original_text=restored,
            tokens_reversed=tokens_reversed,
            scan_id=scan_id,
        )

        if audit:
            log_scan(
                lifespan_state["audit_logger"],
                scan_id=scan_id,
                tool="detokenize_text",
                entity_types_detected=list({
                    # Extract entity type from token like {{EMAIL_ADDRESS_1}}
                    t.strip("{}").rsplit("_", 1)[0]
                    for t in mapping
                }),
                entity_count=tokens_reversed,
                min_confidence=0.0,
            )

        return result.model_dump()

    except Exception as e:
        return {"error": str(e), "scan_id": scan_id}


@mcp.tool()
def list_supported_entities() -> dict:
    """Return the full list of PII entity types this server can detect, with
    descriptions, relevant compliance frameworks, and examples.

    Use this tool FIRST when you need to understand what kinds of PII can be
    detected before calling detect_pii or sanitize_text. Useful for building
    entity_types filter lists.

    This tool takes no arguments and always returns the same result.
    """
    entities = [
        EntityInfo(
            type=entity_type,
            description=meta["description"],
            frameworks=meta["frameworks"],
            examples=meta["examples"],
        )
        for entity_type, meta in ENTITY_METADATA.items()
    ]

    return SupportedEntitiesResult(entities=entities).model_dump()


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
