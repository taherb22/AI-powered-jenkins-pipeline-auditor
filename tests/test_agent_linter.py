import pytest
from ai_powered_jenkins_auditor.linters.agent_linter import AgentLinter

# Example agent_data fixtures
agent_data_1 = "any"
agent_data_2 = {"label": "build-node"}
agent_data_3 = {
    "docker": {
        "image": "mycorp/app:2.0",
        "registryUrl": "https://registry.mycorp.com",
        "registryCredentialsId": "docker-registry-creds"
    }
}
agent_data_4 = {
    "docker": {
        "image": "mycorp/app:2.0",
        "registryCredentialsId": "admin:SuperSecretP@ss!"
    }
}
agent_data_5 = {
    "docker": {
        "image": "node:18",
        "args": "-e API_TOKEN=sk-test-abcdef1234567890"
    }
}
agent_data_6 = {
    "kubernetes": {
        "cloud": "prod",
        "namespace": "ci",
        "credentialsId": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9abc123",
        "yaml": """
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: build
      image: maven:3-jdk-11
      env:
        - name: DB_PASSWORD
          value: \"P@ssw0rd123\"
"""
    }
}
agent_data_7 = {
    "ecs": {
        "cloud": "aws-ecs",
        "cluster": "builds",
        "credentialsId": "AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "launchType": "FARGATE"
    }
}
agent_data_8 = [
    "any",
    {"docker": {"registryCredentialsId": "docker-registry-creds"}},
    {"docker": {"registryCredentialsId": "root:toor123"}},
    {"label": "${NODE_LABEL}"},
]

# Parametrize test with expected finding types only (ignore duplicate counts)
@pytest.mark.parametrize("data, expected_types", [
    (agent_data_1, []),
    (agent_data_2, []),
    (agent_data_3, []),
    (agent_data_4, ["Hardcoded Secret"]),
    (agent_data_5, ["Suspicious Agent Value"]),
    (agent_data_6, ["Hardcoded Secret", "Suspicious Agent Value"]),
    (agent_data_7, ["Suspicious Agent Value"]),
    (agent_data_8, ["Hardcoded Secret"]),
])
def test_agent_linter_types(data, expected_types):
    linter = AgentLinter()
    findings = linter.lint(data, line_number=1)

    found_types = {f['type'] for f in findings}
    assert found_types == set(expected_types), (
        f"Expected finding types {expected_types}, got {found_types}: {findings}"
    )
