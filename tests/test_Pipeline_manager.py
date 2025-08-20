import pytest
from ai_powered_jenkins_auditor.jenkins_files_parser.Pipeline_manager import PipelineManager

JENKINSFILE_WITH_SECRET_IN_ENV = """
pipeline {
    agent any
    environment {
        AWS_SECRET_KEY = 'AKIA1234567890XYZ'
    }
    stages {
        stage('Deploy') {
            steps {
                sh 'aws deploy --key $AWS_SECRET_KEY'
            }
        }
    }
}
"""

@pytest.fixture
def manager():
    """Provides a fresh PipelineManager instance for each test."""
    return PipelineManager()


def test_run_audit_finds_hardcoded_secret_in_environment(manager):
    """
    Tests that run_audit correctly identifies the hardcoded AWS secret key
    in the environment block.
    """
    
    pipeline_obj = manager.run_audit(JENKINSFILE_WITH_SECRET_IN_ENV)
    
   
    
    assert len(pipeline_obj.findings) == 1
    
    finding = pipeline_obj.findings[0]
    
    assert 'Hardcoded' in finding['type']
    assert 'Secret' in finding['type']

    
   
    assert 'AWS_SECRET_KEY' in pipeline_obj.environment
    assert pipeline_obj.environment['AWS_SECRET_KEY'] == "'AKIA1234567890XYZ'"

# --- Test 2: Verify the Remediation Function ---

def test_run_remediation_removes_hardcoded_secret_from_environment(manager):
    """
    Tests that run_remediation correctly identifies AND removes the
    hardcoded AWS secret key, replacing it with a placeholder.
    """
    # 1. Arrange: We use the same insecure Jenkinsfile.
    
    # 2. Act: Run the full audit AND remediation process.
    remediated_pipeline = manager.run_remediation(JENKINSFILE_WITH_SECRET_IN_ENV)
    
    # 3. Assert: Check the final state of the remediated object.
    
    remediated_env = remediated_pipeline.environment
    
    # Verify that the secret was replaced with the correct placeholder.
    assert remediated_env['AWS_SECRET_KEY'].startswith("${REDACTED_")
    assert remediated_env['AWS_SECRET_KEY'].endswith("}")
    # You can also check that the original secret is GONE.
    assert 'AKIA1234567890XYZ' not in remediated_env['AWS_SECRET_KEY']
        
def test_audit_passes_on_valid_best_practice_pipeline(manager):
    """
    Tests that a well-written pipeline that follows best practices
    (uses environment variables, credentials, when clauses) produces
    ZERO findings.
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
                when {
                    branch 'main'
                }
                steps {
                    withCredentials([string(credentialsId: 'deploy-token', variable: 'TOKEN')]) {
                        sh 'curl -H "Authorization: Beararer $TOKEN" https://api.example.com/deploy'
                    }
                }
            }
        }
        post {
            always {
                echo "Finished"
            }
        }
    }
    """
    
   
    pipeline_obj = manager.run_audit(valid_jenkinsfile)
    
    
    assert not pipeline_obj.findings, f"Expected no findings, but got: {pipeline_obj.findings}"
    
   
    assert len(pipeline_obj.stages) == 3
    deploy_stage = next((s for s in pipeline_obj.stages if s.name == 'Deploy'), None)
    assert deploy_stage is not None
    assert deploy_stage.when == ["branch 'main'"]    