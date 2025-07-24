# In tests/test_environment_linter.py

from ai_powered_jenkins_auditor.linters.environment_linter import EnvironmentLinter

def test_finds_specific_secret_in_environment():
    """
    Tests that a high-confidence secret (GitHub Token) is found.
    """
    # Arrange
    linter = EnvironmentLinter()
    env_data = {
        "GITHUB_TOKEN": "'ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0'",
        "SAFE_VARIABLE": "'some-value'"
    }
    # The context dictionary is now a required argument.
    context = {"line": 5}

    # Act
    findings = linter.lint(env_data, context)

    # Assert
    assert len(findings) == 1
    
    finding = findings[0]
    assert finding['type'] == "Hardcoded GitHub Token"
    assert finding['value'] == "'ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0'"
    # We can also test that the context was correctly added
    assert finding['context']['block'] == 'environment'
    assert finding['context']['key'] == 'GITHUB_TOKEN'


def test_finds_generic_secret_by_keyword():
    """
    Tests that a generic secret is found based on a suspicious key name.
    """
    # Arrange
    linter = EnvironmentLinter()
    env_data = {
        "DATABASE_PASSWORD": "'MySuperSecretDbPassword123'"
    }
    context = {"line": 10}

    # Act
    findings = linter.lint(env_data, context)

    # Assert
    assert len(findings) == 1
    
    finding = findings[0]
    assert finding['type'] == "Hardcoded Generic Secret"
    assert finding['context']['key'] == 'DATABASE_PASSWORD'


def test_ignores_safe_environment_variables():
    """
    Tests that normal, non-secret variables are ignored.
    """
    # Arrange
    linter = EnvironmentLinter()
    env_data = {
        "BUILD_MODE": "'release'",
        "DEPLOY_ENV": "'staging'"
    }
    context = {"line": 3}
    
    # Act
    findings = linter.lint(env_data, context)

    # Assert
    assert len(findings) == 0


def test_ignores_suspicious_key_with_safe_value():
    """
    Tests that a suspicious key is ignored if its value is safe (e.g., credentials() or a variable).
    """
    # Arrange
    linter = EnvironmentLinter()
    env_data = {
        "API_TOKEN_CRED": "credentials('my-secret-token')",
        "API_KEY_VAR": "'${env.SECRET_FROM_JENKINS}'"
    }
    context = {"line": 8}
    
    # Act
    findings = linter.lint(env_data, context)

    # Assert
    assert len(findings) == 0, "Should not flag keys when their values are safe"