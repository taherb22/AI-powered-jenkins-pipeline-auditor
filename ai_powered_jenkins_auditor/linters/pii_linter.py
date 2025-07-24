from __future__ import annotations
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
import copy
import re

try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine, OperatorConfig
    from presidio_analyzer.predefined_recognizers import SpacyRecognizer, EmailRecognizer, PhoneRecognizer, CreditCardRecognizer
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


class ApiKeyRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="API Key Pattern",
                regex=r"(?i)(?<=\bAPI[_-]?KEY=['\"]?)[A-Za-z0-9_-]{16,64}",
                score=0.85,
            ),
            Pattern(
                name="Stripe API Key",
                regex=r"sk_live_[A-Za-z0-9]{16,}",  # lowered threshold to match 16+
                score=0.85,
            ),
        ]
        super().__init__(supported_entity="API_KEY", patterns=patterns)


class SecretTokenRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="Secret Token Pattern",
                regex=r"(?i)(?<=\bSECRET_TOKEN=['\"]?)[A-Za-z0-9_@#\$%\^&\*\-!]{8,64}",
                score=0.85,
            ),
            Pattern(
                name="Password Pattern",
                regex=r"(?i)(?<=\bPASSWORD=['\"]?)[A-Za-z0-9_@#\$%\^&\*\-!]{8,64}",
                score=0.85,
            ),
        ]
        super().__init__(supported_entity="SECRET_TOKEN", patterns=patterns)


class TokenRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="Access Token Pattern",
                regex=r"(?i)(?<=\bACCESS_TOKEN=['\"]?)[A-Za-z0-9_\-.!]{16,128}",
                score=0.85,
            ),
            Pattern(
                name="Bearer Token Pattern",
                regex=r"(?i)(?<=\bBearer\s+)[A-Za-z0-9_\-.!]{16,128}",
                score=0.85,
            ),
        ]
        super().__init__(supported_entity="ACCESS_TOKEN", patterns=patterns)


class PiiLinter:
    """
    An isolated linter that scans a complete Pipeline object for PII.
    """
    def __init__(self):
        self._pii_analyzer = None
        self._pii_anonymizer = None
        self.pii_entities_to_find = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "API_KEY",
            "SECRET_TOKEN",
            "ACCESS_TOKEN",
        ]

    def _create_minimal_analyzer(self):
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
        # register custom recognizers
        analyzer.registry.add_recognizer(ApiKeyRecognizer())
        analyzer.registry.add_recognizer(SecretTokenRecognizer())
        analyzer.registry.add_recognizer(TokenRecognizer())
        # register built-in recognizers
        analyzer.registry.add_recognizer(EmailRecognizer(supported_language="en"))
        analyzer.registry.add_recognizer(PhoneRecognizer(supported_language="en"))
        analyzer.registry.add_recognizer(CreditCardRecognizer(supported_language="en"))
        # register spaCy for PERSON
        analyzer.registry.add_recognizer(SpacyRecognizer(supported_language="en"))
        return analyzer

    @property
    def pii_analyzer(self):
        if not PRESIDIO_AVAILABLE:
            return None
        if self._pii_analyzer is None:
            self._pii_analyzer = self._create_minimal_analyzer()
        return self._pii_analyzer

    @property
    def pii_anonymizer(self):
        if not PRESIDIO_AVAILABLE:
            return None
        if self._pii_anonymizer is None:
            self._pii_anonymizer = AnonymizerEngine()
        return self._pii_anonymizer

    def lint(self, pipeline: Pipeline) -> list[dict]:
        if not self.pii_analyzer:
            return []
        findings = []
        # scan environment vars (include raw value without stripping context)
        for key, value in pipeline.environment.items():
            raw = value.strip("'\"")
            for f in self._scan_text(raw, f"environment.{key}"):
                findings.append(f)
        # scan each stage step
        for stage in pipeline.stages:
            for idx, step in enumerate(stage.steps):
                for f in self._scan_text(step, f"stage '{stage.name}'"):
                    f['context'] = {'block': 'stage', 'stage_name': stage.name, 'step_index': idx}
                    findings.append(f)
        return findings

    def anonymize_pipeline(self, pipeline: Pipeline) -> Pipeline:
        if not self.pii_analyzer or not self.pii_anonymizer:
            return pipeline
        anon = copy.deepcopy(pipeline)
        # anonymize environment
        for k, v in anon.environment.items():
            if isinstance(v, str):
                raw = v.strip("'\"")
                new = self._anonymize_text(raw)
                # wrap new in quotes for environment value
                anon.environment[k] = f"'{new}'"
        # anonymize steps
        for stage in anon.stages:
            new_steps = []
            for s in stage.steps:
                if isinstance(s, str):
                    new_steps.append(self._anonymize_text(s))
                else:
                    new_steps.append(s)
            stage.steps = new_steps
        return anon

    def _anonymize_text(self, text: str) -> str:
        def run(txt: str) -> str:
            results = self.pii_analyzer.analyze(text=txt, entities=self.pii_entities_to_find, language='en')
            if not results:
                return txt
            return self.pii_anonymizer.anonymize(
                text=txt,
                analyzer_results=results,
                operators={
                    'DEFAULT': OperatorConfig('replace', {'new_value': '${REDACTED}'}),
                    'API_KEY': OperatorConfig('replace', {'new_value': '${REDACTED_API_KEY}'}),
                    'SECRET_TOKEN': OperatorConfig('replace', {'new_value': '${REDACTED_SECRET}'}),
                    'ACCESS_TOKEN': OperatorConfig('replace', {'new_value': '${REDACTED_TOKEN}'}),
                    'EMAIL_ADDRESS': OperatorConfig('replace', {'new_value': '${REDACTED_EMAIL}'}),
                    'PHONE_NUMBER': OperatorConfig('replace', {'new_value': '${REDACTED_PHONE}'}),
                    'CREDIT_CARD': OperatorConfig('replace', {'new_value': '${REDACTED_CREDIT_CARD}'}),
                    'PERSON': OperatorConfig('replace', {'new_value': '${REDACTED_PERSON}'}),
                }
            ).text
        # handle echo steps
        m = re.match(r"^(sh\s+'echo\s+)(.*)(')$", text)
        if m:
            prefix, msg, suffix = m.groups()
            return f"{prefix}{run(msg)}{suffix}"
        return run(text)

    def _scan_text(self, text: str, location: str) -> list[dict]:
        found = []
        try:
            for res in self.pii_analyzer.analyze(text=text, entities=self.pii_entities_to_find, language='en'):
                if res.score > 0.75:
                    found.append({
                        'type': f"Potential PII ({res.entity_type})",
                        'value': text[res.start:res.end],
                        'location': location
                    })
        except Exception:
            pass
        return found
