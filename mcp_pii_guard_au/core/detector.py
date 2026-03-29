"""Presidio analyser wrapper with custom Australian and New Zealand recognisers."""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

from ..config import DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_ENTITY_TYPES, DEFAULT_LANGUAGE
from .recognizers import (
    AuAbnRecognizer,
    AuAcnRecognizer,
    AuAddressRecognizer,
    AuBankAccountRecognizer,
    AuBsbRecognizer,
    AuDriversLicenceRecognizer,
    AuMedicareRecognizer,
    AuPassportRecognizer,
    AuPhoneRecognizer,
    AuTfnRecognizer,
    CentrelinkCrnRecognizer,
    NzDriversLicenceRecognizer,
    NzIrdRecognizer,
    NzNhiRecognizer,
)


def create_analyzer() -> AnalyzerEngine:
    """Create and configure the Presidio AnalyzerEngine with custom recognisers.

    Loads the spaCy en_core_web_lg model and registers Australian and
    New Zealand recognisers.
    """
    nlp_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    # Register custom Australian recognisers
    analyzer.registry.add_recognizer(AuTfnRecognizer())
    analyzer.registry.add_recognizer(AuMedicareRecognizer())
    analyzer.registry.add_recognizer(AuAbnRecognizer())
    analyzer.registry.add_recognizer(AuAcnRecognizer())
    analyzer.registry.add_recognizer(AuDriversLicenceRecognizer())
    analyzer.registry.add_recognizer(AuPassportRecognizer())
    analyzer.registry.add_recognizer(AuBsbRecognizer())
    analyzer.registry.add_recognizer(AuBankAccountRecognizer())
    analyzer.registry.add_recognizer(AuAddressRecognizer())
    analyzer.registry.add_recognizer(AuPhoneRecognizer())
    analyzer.registry.add_recognizer(CentrelinkCrnRecognizer())

    # Register custom New Zealand recognisers
    analyzer.registry.add_recognizer(NzIrdRecognizer())
    analyzer.registry.add_recognizer(NzNhiRecognizer())
    analyzer.registry.add_recognizer(NzDriversLicenceRecognizer())

    return analyzer


def detect(
    analyzer: AnalyzerEngine,
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    entity_types: list[str] | None = None,
    min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
    entity_thresholds: dict[str, float] | None = None,
) -> list[RecognizerResult]:
    """Run PII detection on text and return results above the confidence threshold.

    Args:
        analyzer: Configured Presidio AnalyzerEngine.
        text: The text to scan.
        language: Language code for analysis.
        entity_types: Entity types to scan for, or None for all supported types.
        min_confidence: Minimum confidence score to include in results.
        entity_thresholds: Optional per-entity-type confidence thresholds.
            Overrides min_confidence for specific types. For example,
            ``{"AU_ADDRESS": 0.9, "PERSON": 0.5}`` would require 0.9 for
            addresses but only 0.5 for person names. Entity types not listed
            fall back to min_confidence.

    Returns:
        List of RecognizerResult objects sorted by start position.
    """
    entities = entity_types if entity_types else DEFAULT_ENTITY_TYPES

    # Use the lowest threshold to cast a wide net, then post-filter per entity type
    if entity_thresholds:
        floor = min(min_confidence, *entity_thresholds.values())
    else:
        floor = min_confidence

    results = analyzer.analyze(
        text=text,
        language=language,
        entities=entities,
        score_threshold=floor,
    )

    # Apply per-entity thresholds
    if entity_thresholds:
        results = [
            r for r in results
            if r.score >= entity_thresholds.get(r.entity_type, min_confidence)
        ]

    # Sort by position for stable ordering
    results.sort(key=lambda r: r.start)
    return results
