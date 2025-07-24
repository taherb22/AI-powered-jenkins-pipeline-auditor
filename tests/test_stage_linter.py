# tests/test_stage_linter.py
import pytest
from ai_powered_jenkins_auditor.models.stage import Stage
from ai_powered_jenkins_auditor.linters.stage_linter import StageLinter

@pytest.fixture
def linter():
    return StageLinter()

def test_finds_generic_secret_in_stage(linter):
    """
    Tests that a generic secret (e.g., password=...) is found.
    """
    # Arrange
    bad_stage = Stage(name="Deploy")
    bad_stage.steps = ["sh 'deploy.sh --password=MyS3cr3tP@ssw0rd!'"]
    stages_data = [bad_stage]
    
    # Act
    findings = linter.lint(stages_data, {})
    
    # Assert
    assert len(findings) == 1
    finding = findings[0]
    assert finding['type'] == 'Hardcoded Generic Secret'
    assert 'password=MyS3cr3tP@ssw0rd!' in finding['value']

def test_finds_specific_secret_in_stage(linter):
    """
    Tests that a specific secret (an AWS Key) is found, and ONLY that one.
    """
    # Arrange
    bad_stage = Stage(name="AWS Setup")
    # Note: The generic pattern is designed to NOT match AWS_KEY
    bad_stage.steps = ["sh 'export AWS_KEY=AKIAIOSFODNN7EXAMPLE'"]
    stages_data = [bad_stage]
    
    # Act
    findings = linter.lint(stages_data, {})
    
    # Assert
    assert len(findings) == 1
    # FIX: Access the first item in the list with [0] before getting the key
    finding = findings[0]
    assert finding['type'] == 'Hardcoded AWS Access Key ID'
    assert finding['value'] == 'AKIAIOSFODNN7EXAMPLE'

def test_no_findings_in_clean_stage(linter):
    """
    Tests that a clean stage produces no findings.
    """
    # Arrange
    clean_stage = Stage(name="Build")
    clean_stage.steps = ["sh 'npm run build'", "checkout scm", "withCredentials(...)"]
    stages_data = [clean_stage]
    
    # Act
    findings = linter.lint(stages_data, {})
    
    # Assert
    assert not findings, f"Expected no findings, but got: {findings}"