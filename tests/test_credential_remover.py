import pytest
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage
from ai_powered_jenkins_auditor.Parser.remediators.credential_remover import CredentialRemover


@pytest.fixture
def remover() -> CredentialRemover:
    """Provides a fresh instance of the CredentialRemover."""
    return CredentialRemover()

@pytest.fixture
def simple_pipeline() -> Pipeline:
    """Provides a simple, consistent pipeline object for tests."""
    p = Pipeline()
    p.agent = {'docker': {'registryCredentialsId': 'admin:SuperSecretP@ss!'}}
    p.environment = {'AWS_SECRET_KEY': 'AKIA1234567890XYZ', 'OTHER_VAR': 'value'}
    build_stage = Stage(name="Build")
    build_stage.steps = [
        'docker pull admin:SuperSecretP@ss!',
        'echo $AWS_SECRET_KEY'
    ]
    p.stages.append(build_stage)
    return p

# --- The Corrected Test Cases ---

def test_remediate_environment(remover, simple_pipeline):
    """
    Tests that the remover correctly modifies the environment block.
    NOTE: This requires updating the CredentialRemover class itself.
    Assuming the remover is updated to handle the environment block.
    """
    finding = {
        'type': 'Hardcoded Secret',
        'value': 'AKIA1234567890XYZ'
    }
    
    # ACT
    remediated = remover(simple_pipeline, [finding])
    
    # ASSERT
    placeholder = remover._get_placeholder_variable(finding)
    # The remover should only replace the value, not the key.
    assert remediated.environment['AWS_SECRET_KEY'] == placeholder
    assert remediated.environment['OTHER_VAR'] == 'value' # Ensure other vars are untouched

def test_remediate_agent(remover, simple_pipeline):
    """
    Tests that the remover correctly modifies a secret within the agent block.
    """
    finding = {
        'type': 'Hardcoded User:Pass',
        'value': 'admin:SuperSecretP@ss!'
    }
    
    # ACT
    remediated = remover(simple_pipeline, [finding])
    
    # ASSERT
    placeholder = remover._get_placeholder_variable(finding)
    assert remediated.agent['docker']['registryCredentialsId'] == placeholder

@pytest.mark.parametrize("step_index, finding_value, expected_type", [
    (0, 'admin:SuperSecretP@ss!', 'Hardcoded User:Pass'),
    (1, '$AWS_SECRET_KEY', 'Suspicious Value') # Assuming a pattern for this
])
def test_remediate_stage_step(remover, simple_pipeline, step_index, finding_value, expected_type):
    """
    Tests that secrets are correctly replaced within stage steps.
    """
    finding = {
        'type': expected_type,
        'value': finding_value
    }
    
    # ACT
    remediated = remover(simple_pipeline, [finding])
    
    # ASSERT
    placeholder = remover._get_placeholder_variable(finding)
    # We need to reconstruct the expected full string
    original_step = simple_pipeline.stages[0].steps[step_index]
    expected_step = original_step.replace(finding_value, placeholder)
    
    assert remediated.stages[0].steps[step_index] == expected_step