"""Structured compliance audit logger.

Writes append-only JSONL entries for every PII scan operation.
Never logs original text or detected entity values — metadata only.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from ..config import AUDIT_LOG_PATH


def configure_audit_logger() -> structlog.stdlib.BoundLogger:
    """Configure and return the audit logger that writes to the JSONL file.

    Creates the log directory if it does not exist.
    """
    log_path = Path(AUDIT_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler for JSONL output
    import logging

    file_handler = logging.FileHandler(str(log_path), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Configure structlog for JSON output
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=file_handler.stream),
        cache_logger_on_first_use=False,
    )

    return structlog.get_logger("pii_guard_audit")


def log_scan(
    logger: structlog.stdlib.BoundLogger,
    *,
    scan_id: str,
    tool: str,
    entity_types_detected: list[str],
    entity_count: int,
    mode: str | None = None,
    text_length: int | None = None,
    min_confidence: float,
    language: str = "en",
) -> None:
    """Write a single audit log entry. Never includes PII values."""
    event_data: dict = {
        "scan_id": scan_id,
        "tool": tool,
        "entity_types_detected": entity_types_detected,
        "entity_count": entity_count,
        "min_confidence": min_confidence,
        "language": language,
    }
    if mode is not None:
        event_data["mode"] = mode
    if text_length is not None:
        event_data["text_length"] = text_length

    logger.info("pii_scan", **event_data)
