import pytest
from ai_powered_jenkins_auditor.jenkins_files_parser.linters.agent_linter import AgentLinter


agent_data_1 = 'any'
agent_data_2 = {'label': 'build-node'}
agent_data_3 = {'docker': {'image': 'mycorp/app:2.0'}}
agent_data_4 = {'docker': {'registryCredentialsId': 'admin:SuperSecretP@ss!'}}
agent_data_5 = {'docker': {'args': '-e API_TOKEN=sk-test-abcdef1234567890'}}
agent_data_6 = {
    'kubernetes': {
        'credentialsId': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.AbcDefGhiJKLmnoPQRstuVWXYZ1234567890',
        'yaml': 'env:\n  - name: DB_PASSWORD\n    value: "user:P@ssw0rd123"' 
    }
}


agent_data_7 = {
    'ecs': {
        'credentialsId': 'AKIAIOSFODNN7EXAMPLE' # AWS Key
    }
}


agent_data_8 = [
    {'docker': {'registryCredentialsId': 'root:toor1234'}} # User:Pass
]



@pytest.mark.parametrize("data, expected_finding_count", [
    (agent_data_1, 0), # 'any' is not a secret
    (agent_data_2, 0), # a label is not a secret
    (agent_data_3, 0), # a docker image is not a secret
    (agent_data_4, 1), # 'admin:SuperSecretP@ss!' is one secret
    (agent_data_5, 1), # 'API_TOKEN=...' is one secret
    (agent_data_6, 2), # The JWT and the user:pass are two secrets
    (agent_data_7, 1), # The AWS key is one secret
    (agent_data_8, 1), # The 'root:toor123' is one secret
])
def test_agent_linter_secret_detection(data, expected_finding_count):
    """
    Tests the AgentLinter against various data structures and verifies that the
    correct NUMBER of hardcoded secrets is detected.
    """
    linter = AgentLinter()
    findings = linter(data, line_number=1)
    
    # --- 3. THE CORRECTED ASSERTION LOGIC ---
    # First, assert that the number of findings is correct.
    assert len(findings) == expected_finding_count, (
        f"Expected {expected_finding_count} findings, but got {len(findings)}: {findings}"
    )
    
    # Second, if findings exist, assert that they all have the correct, unified type.
    if findings:
        assert all(f['type'] == "Hardcoded Secret" for f in findings)