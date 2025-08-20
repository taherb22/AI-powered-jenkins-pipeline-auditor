import pytest
# We need our data models to create test objects
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage
# We import the class we are testing
from ai_powered_jenkins_auditor.jenkins_files_parser.linters.pii_linter import PiiLinter

@pytest.fixture
def pii_linter():
    """
    Provides a fresh, initialized PiiLinter instance for each test.
    The Presidio model will be lazy-loaded once per test session.
    """
    return PiiLinter()

# --- Tests for the lint() Method ---

def test_lint_finds_pii_in_stage_step(pii_linter):
    """
    Tests that lint() can find PII (a person's name) inside a stage's step.
    """
    pipeline = Pipeline()
    problem_stage = Stage(name="Debug Stage")
    problem_stage.steps.append("sh 'echo For help, contact John Doe immediately.'")
    pipeline.stages.append(problem_stage)

    findings = pii_linter.lint(pipeline)

    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Potential PII (PERSON)'
    assert finding['value'] == 'John Doe'
    assert finding['context']['stage_name'] == 'Debug Stage'


def test_lint_finds_pii_in_environment_variable(pii_linter):
    """
    Tests that lint() can find PII (an email address) in an environment variable.
    """
    pipeline = Pipeline()
    pipeline.environment = {"CONTACT_EMAIL": "'jane.doe@example.com'"}

    findings = pii_linter.lint(pipeline)

    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Potential PII (EMAIL_ADDRESS)'
    assert finding['value'] == 'jane.doe@example.com'
    assert finding['location'] == "environment.CONTACT_EMAIL"

def test_lint_detects_api_key_in_env(pii_linter):
    pipeline = Pipeline()
    pipeline.environment = {
        "API_KEY": "'sk_live_1234567890abcdefABCDEF'"
    }

    findings = pii_linter.lint(pipeline)

    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Potential PII (API_KEY)'
    assert 'sk_live_1234567890abcdefABCDEF' in finding['value']
    assert finding['location'] == 'environment.API_KEY'


def test_lint_detects_secret_token_in_step(pii_linter):
    pipeline = Pipeline()
    stage = Stage(name="Deploy")
    stage.steps.append("sh 'export SECRET_TOKEN=MySuperSecret123!'" )
    pipeline.stages.append(stage)

    findings = pii_linter.lint(pipeline)

    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Potential PII (SECRET_TOKEN)'
    assert 'MySuperSecret123!' in finding['value']
    assert finding['context']['stage_name'] == 'Deploy'


def test_lint_detects_access_token_in_step(pii_linter):
    pipeline = Pipeline()
    stage = Stage(name="Deploy")
    stage.steps.append("sh 'export ACCESS_TOKEN=ghp_ABC1234567890SECRET'" )
    pipeline.stages.append(stage)

    findings = pii_linter.lint(pipeline)

    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Potential PII (ACCESS_TOKEN)'
    assert 'ghp_ABC1234567890SECRET' in finding['value']
    assert finding['context']['stage_name'] == 'Deploy'

# --- Tests for the anonymize_pipeline() Method ---

def test_anonymize_pipeline_replaces_pii_in_step(pii_linter):
    """
    Tests that anonymize_pipeline() correctly replaces PII in a stage step.
    """
    pipeline_with_pii = Pipeline()
    stage_with_pii = Stage(name="Contact Stage")
    original_step = "sh 'echo Contact Jane Doe for help.'"
    stage_with_pii.steps.append(original_step)
    pipeline_with_pii.stages.append(stage_with_pii)

    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline_with_pii)

    anonymized_step = anonymized_pipeline.stages[0].steps[0]
    expected_anonymized_step = "sh 'echo Contact ${REDACTED_PERSON} for help.'"

    assert anonymized_step == expected_anonymized_step
    assert pipeline_with_pii.stages[0].steps[0] == original_step


def test_anonymize_pipeline_replaces_pii_in_environment(pii_linter):
    """
    Tests that anonymize_pipeline() correctly replaces PII in an environment variable.
    """
    pipeline_with_pii = Pipeline()
    original_email = "'jane.doe@example.com'"
    pipeline_with_pii.environment = {"CONTACT_EMAIL": original_email}

    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline_with_pii)

    anonymized_email = anonymized_pipeline.environment["CONTACT_EMAIL"]
    expected_anonymized_email = "'${REDACTED_EMAIL}'"

    assert anonymized_email == expected_anonymized_email
    assert pipeline_with_pii.environment["CONTACT_EMAIL"] == original_email


def test_anonymize_pipeline_removes_api_key(pii_linter):
    pipeline = Pipeline()
    original_key = "'sk_live_1234567890abcdefABCDEF'"
    pipeline.environment = {"API_KEY": original_key}

    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline)

    anonymized_value = anonymized_pipeline.environment["API_KEY"]
    expected_value = "'${REDACTED_API_KEY}'"

    assert anonymized_value == expected_value
    assert pipeline.environment["API_KEY"] == original_key


def test_anonymize_pipeline_removes_secret_token(pii_linter):
    pipeline = Pipeline()
    stage = Stage(name="Deploy")
    original_step = "sh 'export SECRET_TOKEN=MySuperSecret123!'"
    stage.steps.append(original_step)
    pipeline.stages.append(stage)

    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline)

    anonymized_step = anonymized_pipeline.stages[0].steps[0]
    expected_step = "sh 'export SECRET_TOKEN=${REDACTED_SECRET}'"

    assert anonymized_step == expected_step
    assert pipeline.stages[0].steps[0] == original_step


def test_anonymize_pipeline_removes_access_token(pii_linter):
    pipeline = Pipeline()
    stage = Stage(name="Deploy")
    original_step = "sh 'export ACCESS_TOKEN=ghp_ABC1234567890SECRET'"
    stage.steps.append(original_step)
    pipeline.stages.append(stage)

    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline)

    anonymized_step = anonymized_pipeline.stages[0].steps[0]
    expected_step = "sh 'export ACCESS_TOKEN=${REDACTED_TOKEN}'"

    assert anonymized_step == expected_step
    assert pipeline.stages[0].steps[0] == original_step


def test_anonymize_pipeline_does_not_change_clean_pipeline(pii_linter):
    pipeline = Pipeline()
    clean_stage = Stage(name="Build")
    clean_stage.steps.append("sh 'npm run build'")
    pipeline.stages.append(clean_stage)
    
    anonymized_pipeline = pii_linter.anonymize_pipeline(pipeline)
    
    assert anonymized_pipeline.to_dict() == pipeline.to_dict()
