"""Presidio anonymizer wrapper with multiple redaction modes."""

from __future__ import annotations

from typing import Literal

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


def create_anonymizer() -> AnonymizerEngine:
    """Create a Presidio AnonymizerEngine instance."""
    return AnonymizerEngine()


def _build_redact_operators(results: list[RecognizerResult]) -> dict[str, OperatorConfig]:
    """Build operator config for redact mode: [REDACTED:TYPE]."""
    operators: dict[str, OperatorConfig] = {}
    for result in results:
        entity_type = result.entity_type
        short_type = entity_type.replace("_ADDRESS", "").replace("_NUMBER", "")
        operators[entity_type] = OperatorConfig(
            "replace", {"new_value": f"[REDACTED:{short_type}]"}
        )
    return operators


def _build_replace_operators(results: list[RecognizerResult]) -> dict[str, OperatorConfig]:
    """Build operator config for replace mode using Presidio's faker-based operators.

    Falls back to type-labelled placeholders (e.g. <PERSON>, <EMAIL_ADDRESS>)
    if the faker operator is unavailable.
    """
    operators: dict[str, OperatorConfig] = {}
    try:
        # Attempt to use Presidio's built-in fake data generation
        from presidio_anonymizer.operators import OperatorsFactory

        available = OperatorsFactory.get_anonymizers()
        if "custom" in available or "fake" in available:
            for result in results:
                operators[result.entity_type] = OperatorConfig("fake")
            return operators
    except (ImportError, AttributeError):
        pass

    # Fallback: use Presidio's default <TYPE> replacement (no custom operators
    # means Presidio applies its built-in replace with the entity type label)
    return operators


def _build_tokenize_operators(
    results: list[RecognizerResult],
) -> dict[str, OperatorConfig]:
    """Build operator config for tokenize mode: {{TYPE_N}} with per-type counters.

    Presidio applies operators per entity type uniformly — all instances of the
    same type get the same replacement string. For multiple instances of one type,
    we use Presidio's hash operator to produce unique deterministic tokens per value.
    For single-instance types, we use a readable {{TYPE_1}} label.
    """
    # Count instances per type
    type_counts: dict[str, int] = {}
    for result in results:
        type_counts[result.entity_type] = type_counts.get(result.entity_type, 0) + 1

    operators: dict[str, OperatorConfig] = {}
    for entity_type, count in type_counts.items():
        if count == 1:
            # Single instance: readable token
            operators[entity_type] = OperatorConfig(
                "replace", {"new_value": f"{{{{{entity_type}_1}}}}"}
            )
        else:
            # Multiple instances: use hash for unique-per-value tokens.
            # Presidio's hash operator produces a deterministic hash of each value,
            # so identical values get the same token and different values differ.
            try:
                operators[entity_type] = OperatorConfig(
                    "hash", {"hash_type": "sha256"}
                )
            except Exception:
                # Fallback if hash operator unavailable
                operators[entity_type] = OperatorConfig(
                    "replace", {"new_value": f"{{{{{entity_type}}}}}"}
                )

    return operators


def sanitize(
    anonymizer: AnonymizerEngine,
    text: str,
    results: list[RecognizerResult],
    mode: Literal["redact", "replace", "tokenize"] = "redact",
) -> str:
    """Sanitize text by applying the chosen anonymization mode.

    Args:
        anonymizer: Configured Presidio AnonymizerEngine.
        text: Original text to sanitize.
        results: Detection results from the analyzer.
        mode: Anonymization strategy — redact, replace, or tokenize.

    Returns:
        Sanitized text string.
    """
    if not results:
        return text

    if mode == "redact":
        operators = _build_redact_operators(results)
    elif mode == "replace":
        operators = _build_replace_operators(results)
    elif mode == "tokenize":
        operators = _build_tokenize_operators(results)
    else:
        operators = {}

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators if operators else None,
    )

    return anonymized.text
