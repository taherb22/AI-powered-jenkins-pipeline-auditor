import pytest
from ai_powered_jenkins_auditor.jenkins_files_parser.linters.environment_linter import EnvironmentLinter


@pytest.fixture
def linter() -> EnvironmentLinter:
    return EnvironmentLinter()


def test_finds_specific_secret_in_environment(linter):
    """
    Tests that a high-confidence secret (GitHub Token) is found.
    """
    env_data = {
        "GITHUB_TOKEN": "ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
        "SAFE_VARIABLE": "some-value"
    }
    
   
    findings = linter(env_data)
    
    assert len(findings) == 1
    assert findings[0]['type'] == "Hardcoded Secret"
    assert findings[0]['value'] == "ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"

def test_finds_generic_secret_by_keyword(linter):
    """
    Tests that a generic secret is found based on a suspicious key name.
    """
    env_data = {
        "DATABASE_PASSWORD": "MySuperSecretDbPassword123"
    }
    
   
    findings = linter(env_data)
    
    assert len(findings) == 1
    assert findings[0]['type'] == "Hardcoded Secret"
    assert "MySuperSecretDbPassword123" in findings[0]['value']

def test_ignores_safe_environment_variables(linter):
    """
    Tests that normal, non-secret variables are ignored.
    """
    env_data = {
        "BUILD_MODE": "release",
        "DEPLOY_ENV": "staging"
    }
    
    findings = linter(env_data)
    
    assert len(findings) == 0

def test_ignores_suspicious_key_with_safe_value(linter):
    """
    Tests that a suspicious key is ignored if its value is safe (e.g., credentials() or a variable).
    """
    env_data = {
        "API_TOKEN_CRED": "credentials('my-secret-token')",
        "API_KEY_VAR": "'${env.SECRET_FROM_JENKINS}'"
    }
    
   
    findings = linter(env_data)
    
    assert len(findings) == 0