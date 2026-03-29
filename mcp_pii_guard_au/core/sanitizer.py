"""Presidio anonymiser wrapper with multiple redaction modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


@dataclass
class SanitizeResult:
    """Result of a sanitise operation, including optional token mapping."""

    text: str
    token_mapping: dict[str, str] = field(default_factory=dict)


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


def _build_tokenize_operators_and_mapping(
    text: str,
    results: list[RecognizerResult],
) -> tuple[dict[str, OperatorConfig], dict[str, str]]:
    """Build operator config for tokenize mode and capture the token-to-value mapping.

    Assigns each detected entity a unique readable token like ``{{TYPE_N}}`` with
    per-type counters. Returns both the Presidio operator config and a mapping
    from token to original value for use with de-tokenisation.

    Note: Presidio applies operators per entity type uniformly, so when multiple
    instances of the same type exist we manually replace them after anonymisation.
    For this reason, the operators dict uses single-instance tokens and the caller
    handles multi-instance cases via post-processing in sanitize().
    """
    # Assign numbered tokens to each result, sorted by position
    sorted_results = sorted(results, key=lambda r: r.start)
    type_counters: dict[str, int] = {}
    token_mapping: dict[str, str] = {}  # token → original value
    result_tokens: dict[int, str] = {}  # result id → token

    for r in sorted_results:
        entity_type = r.entity_type
        type_counters[entity_type] = type_counters.get(entity_type, 0) + 1
        token = f"{{{{{entity_type}_{type_counters[entity_type]}}}}}"
        original_value = text[r.start:r.end]
        token_mapping[token] = original_value
        result_tokens[id(r)] = token

    # Build per-type operators (Presidio requires one operator per type)
    # For single-instance types, use the token directly
    # For multi-instance types, use type_1 as placeholder — we'll post-process
    operators: dict[str, OperatorConfig] = {}
    type_counts: dict[str, int] = {}
    for r in results:
        type_counts[r.entity_type] = type_counts.get(r.entity_type, 0) + 1

    for entity_type, count in type_counts.items():
        operators[entity_type] = OperatorConfig(
            "replace", {"new_value": f"{{{{{entity_type}_1}}}}"}
        )

    return operators, token_mapping


def sanitize(
    anonymizer: AnonymizerEngine,
    text: str,
    results: list[RecognizerResult],
    mode: Literal["redact", "replace", "tokenize"] = "redact",
) -> SanitizeResult:
    """Sanitise text by applying the chosen anonymisation mode.

    Args:
        anonymizer: Configured Presidio AnonymizerEngine.
        text: Original text to sanitise.
        results: Detection results from the analyser.
        mode: Anonymisation strategy — redact, replace, or tokenize.

    Returns:
        SanitizeResult with sanitised text and optional token mapping.
    """
    if not results:
        return SanitizeResult(text=text)

    token_mapping: dict[str, str] = {}

    if mode == "redact":
        operators = _build_redact_operators(results)
    elif mode == "replace":
        operators = _build_replace_operators(results)
    elif mode == "tokenize":
        operators, token_mapping = _build_tokenize_operators_and_mapping(text, results)
    else:
        operators = {}

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators if operators else None,
    )

    output_text = anonymized.text

    # For tokenize mode with multiple instances of the same type, Presidio
    # replaces all instances with the same token ({{TYPE_1}}). We need to
    # do a manual replacement pass to assign unique numbered tokens.
    if mode == "tokenize" and token_mapping:
        # Check for types with multiple instances
        type_counts: dict[str, int] = {}
        for r in results:
            type_counts[r.entity_type] = type_counts.get(r.entity_type, 0) + 1

        multi_types = {t for t, c in type_counts.items() if c > 1}
        if multi_types:
            # Rebuild from original text with manual token substitution
            sorted_results = sorted(results, key=lambda r: r.start)
            type_counters: dict[str, int] = {}
            # Build replacement list (in reverse order to preserve positions)
            replacements: list[tuple[int, int, str]] = []
            for r in sorted_results:
                type_counters[r.entity_type] = type_counters.get(r.entity_type, 0) + 1
                token = f"{{{{{r.entity_type}_{type_counters[r.entity_type]}}}}}"
                replacements.append((r.start, r.end, token))

            # Apply replacements in reverse order
            output_text = text
            for start, end, token in reversed(replacements):
                output_text = output_text[:start] + token + output_text[end:]

    return SanitizeResult(text=output_text, token_mapping=token_mapping)
