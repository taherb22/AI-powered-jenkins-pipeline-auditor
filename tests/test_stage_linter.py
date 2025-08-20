import pytest
from ai_powered_jenkins_auditor.models.stage import Stage
from ai_powered_jenkins_auditor.jenkins_files_parser.linters.stage_linter import StageLinter

@pytest.fixture
def linter():
    return StageLinter()

def test_finds_generic_secret_in_stage(linter):
    """
    Tests that a generic secret (e.g., password=...) is found.
    """
    bad_stage = Stage(name="Deploy")
    bad_stage.steps = ["sh 'deploy.sh --password=MyS3cr3tP@ssw0rd!'"]
    stages_data = [bad_stage]
    findings = linter(stages_data)
    
    
    assert len(findings) == 1
    assert findings[0]['type'] == 'Hardcoded Secret'

def test_finds_specific_secret_in_stage(linter):
    """
    Tests that a specific secret (an AWS Key) is found.
    """
    bad_stage = Stage(name="AWS Setup")
    bad_stage.steps = ["sh 'export AWS_KEY=AKIAIOSFODNN7EXAMPLE'"]
    stages_data = [bad_stage]

    
    findings = linter(stages_data)
    
    
    assert len(findings) == 1
    assert findings[0]['type'] == 'Hardcoded Secret'

def test_no_findings_in_clean_stage(linter):
    """
    Tests that a clean stage produces no findings.
    """
    clean_stage = Stage(name="Build")
    clean_stage.steps = ["sh 'npm run build'", "checkout scm", "withCredentials(...)"]
    stages_data = [clean_stage]

    
    findings = linter(stages_data)
    
   
    assert len(findings) == 0