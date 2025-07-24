# In tests/test_jenkins_file_parser.py

import pytest
from ai_powered_jenkins_auditor.jenkins_file_parser import JenkinsFileParser
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage

@pytest.fixture(scope="module")
def parser() -> JenkinsFileParser:
    """Creates one parser instance for all tests in this file."""
    return JenkinsFileParser()


def test_parser_handles_scripted_pipeline_gracefully(parser):
    """
    Based on Example 1: A Scripted Pipeline should not be parsed.
    The `parse` method should return an empty Pipeline object without stages.
    """
    scripted_jenkinsfile = """
    node {
        stage('Build') {
            echo 'Building...'
        }
    }
    """
    pipeline_object = parser.parse(bytes(scripted_jenkinsfile, "utf8"))
    
    # We expect it to find no 'pipeline' block, so the object should be mostly empty.
    assert isinstance(pipeline_object, Pipeline)
    assert len(pipeline_object.stages) == 0
    assert pipeline_object.agent is None

def test_parser_extracts_environment_variables(parser):
    """
    Based on Example 2 & 3: Correctly parse the environment block.
    """
    jenkinsfile_with_env = """
    pipeline {
        agent any
        environment {
            BUILD_MODE = 'release'
            AWS_SECRET_KEY = 'AKIA1234567890XYZ'
        }
        stages { stage('dummy'){} }
    }
    """
    pipeline_object = parser.parse(bytes(jenkinsfile_with_env, "utf8"))
    
    assert isinstance(pipeline_object.environment, dict)
    assert len(pipeline_object.environment) == 2
    assert pipeline_object.environment['BUILD_MODE'] == "'release'"
    assert pipeline_object.environment['AWS_SECRET_KEY'] == "'AKIA1234567890XYZ'"

def test_parser_extracts_dangerous_shell_command(parser):
    """
    Based on Example 4: Correctly parse a simple shell command in a stage.
    """
    jenkinsfile_with_curl = """
    pipeline {
        agent any
        stages {
            stage('Deploy') {
                steps {
                    sh 'curl -X POST http://insecure-service.local/deploy'
                }
            }
        }
    }
    """
    pipeline_object = parser.parse(bytes(jenkinsfile_with_curl, "utf8"))
    
    assert len(pipeline_object.stages) == 1
    deploy_stage = pipeline_object.stages[0]
    
    assert deploy_stage.name == 'Deploy'
    assert len(deploy_stage.steps) == 1
    assert deploy_stage.steps[0] == "sh 'curl -X POST http://insecure-service.local/deploy'"

def test_parser_handles_valid_multibranch_file(parser):
    """
    Based on the 'Valid Multibranch' example: Correctly parse a full, clean file.
    """
    valid_jenkinsfile = """
    pipeline {
        agent any
        environment {
            DEPLOY_ENV = 'staging'
        }
        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }
            stage('Test') {
                steps {
                    sh 'pytest tests/'
                }
            }
            stage('Deploy') {
                steps {
                    echo 'deploying...' // Placeholder for simplicity
                }
            }
        }
    }
    """
    pipeline_object = parser.parse(bytes(valid_jenkinsfile, "utf8"))

    # Assert the overall structure
    assert pipeline_object.agent == 'any'
    assert pipeline_object.environment['DEPLOY_ENV'] == "'staging'"
    assert len(pipeline_object.stages) == 3

    # Assert details of the stages
    checkout_stage, test_stage, deploy_stage = pipeline_object.stages
    assert checkout_stage.name == 'Checkout'
    assert checkout_stage.steps[0] == 'checkout scm'
    
    assert test_stage.name == 'Test'
    assert test_stage.steps[0] == "sh 'pytest tests/'"

    assert deploy_stage.name == 'Deploy'
    assert deploy_stage.steps[0] == "echo 'deploying...'"