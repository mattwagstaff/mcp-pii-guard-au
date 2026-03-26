"""Presidio analyser wrapper with custom Australian recognisers."""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

from config import DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_ENTITY_TYPES, DEFAULT_LANGUAGE
from core.recognizers import (
    AuAbnRecognizer,
    AuAcnRecognizer,
    AuAddressRecognizer,
    AuBankAccountRecognizer,
    AuBsbRecognizer,
    AuDriversLicenceRecognizer,
    AuMedicareRecognizer,
    AuPassportRecognizer,
    AuTfnRecognizer,
    CentrelinkCrnRecognizer,
)


def create_analyzer() -> AnalyzerEngine:
    """Create and configure the Presidio AnalyzerEngine with custom recognisers.

    Loads the spaCy en_core_web_lg model and registers Australian recognisers.
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
    analyzer.registry.add_recognizer(CentrelinkCrnRecognizer())

    return analyzer


def detect(
    analyzer: AnalyzerEngine,
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    entity_types: list[str] | None = None,
    min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[RecognizerResult]:
    """Run PII detection on text and return results above the confidence threshold.

    Args:
        analyzer: Configured Presidio AnalyzerEngine.
        text: The text to scan.
        language: Language code for analysis.
        entity_types: Entity types to scan for, or None for all supported types.
        min_confidence: Minimum confidence score to include in results.

    Returns:
        List of RecognizerResult objects sorted by start position.
    """
    entities = entity_types if entity_types else DEFAULT_ENTITY_TYPES

    results = analyzer.analyze(
        text=text,
        language=language,
        entities=entities,
        score_threshold=min_confidence,
    )

    # Sort by position for stable ordering
    results.sort(key=lambda r: r.start)
    return results
