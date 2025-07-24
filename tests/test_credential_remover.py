import pytest
from ai_powered_jenkins_auditor.remediators.credential_remover import CredentialRemover
from ai_powered_jenkins_auditor.models.pipeline import Pipeline, Stage

@pytest.fixture
def simple_pipeline():
    # Build an empty Pipeline and then set its attributes
    pipeline = Pipeline()
    # Agent with hardcoded secret
    pipeline.agent = {'docker': {'registryCredentialsId': 'admin:SuperSecretP@ss!'}}
    # Environment with a hardcoded AWS key and another var
    pipeline.environment = {'AWS_SECRET_KEY': 'AKIA1234567890XYZ', 'OTHER_VAR': 'value'}
    # Create one stage named 'Build' and define its steps
    build_stage = Stage('Build')
    build_stage.steps = [
        'docker pull admin:SuperSecretP@ss!',
        'echo $AWS_SECRET_KEY'
    ]
    pipeline.stages = [build_stage]
    return pipeline


def test_remediate_environment(simple_pipeline):
    remover = CredentialRemover()
    finding = {
        'context': {'block': 'environment', 'key': 'AWS_SECRET_KEY'},
        'type': 'Hardcoded Secret',
        'message': 'Hardcoded AWS key',
        'value': 'AKIA1234567890XYZ'
    }
    remediated = remover.remediate(simple_pipeline, [finding])
    # The AWS_SECRET_KEY should be replaced with quoted placeholder
    placeholder = remover._get_placeholder_variable(finding)
    expected_env = {'AWS_SECRET_KEY': f"'{placeholder}'", 'OTHER_VAR': 'value'}
    assert remediated.environment == expected_env
    # Original pipeline unchanged
    assert simple_pipeline.environment['AWS_SECRET_KEY'] == 'AKIA1234567890XYZ'


def test_remediate_agent(simple_pipeline):
    remover = CredentialRemover()
    finding = {
        'context': {'block': 'agent'},
        'type': 'Hardcoded Secret',
        'message': 'Hardcoded secret in agent',
        'value': 'admin:SuperSecretP@ss!'
    }
    remediated = remover.remediate(simple_pipeline, [finding])
    placeholder = remover._get_placeholder_variable(finding)
    # The agent nested value should be replaced
    assert remediated.agent['docker']['registryCredentialsId'] == placeholder
    # Original pipeline unaffected
    assert simple_pipeline.agent['docker']['registryCredentialsId'] == 'admin:SuperSecretP@ss!'

@pytest.mark.parametrize("step_index, finding, expected_step", [
    (0, {
        'context': {'block': 'stage', 'stage_name': 'Build', 'step_index': 0},
        'type': 'Hardcoded Secret',
        'message': 'Hardcoded secret in step',
        'value': 'admin:SuperSecretP@ss!'
    }, 'docker pull ${REDACTED_SECRET}'),
    (1, {
        'context': {'block': 'stage', 'stage_name': 'Build', 'step_index': 1},
        'type': 'Suspicious Agent Value',
        'message': 'Suspicious value in step',
        'value': '$AWS_SECRET_KEY'
    }, 'echo ${REDACTED_SUSPICIOUS_AGENT_VALUE}')
])
def test_remediate_stage_step(simple_pipeline, step_index, finding, expected_step):
    remover = CredentialRemover()
    remediated = remover.remediate(simple_pipeline, [finding])
    assert remediated.stages[0].steps[step_index] == expected_step
