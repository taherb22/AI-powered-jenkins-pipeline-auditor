
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage


def get_insecure_obvious_pipeline() -> Pipeline:
    """
    Returns a Pipeline object with multiple, obvious vulnerabilities.
    """
    p = Pipeline()
    p.agent = {"type": "any"}
    p.environment = {"API_KEY": "secret-key-12345"}
    
    build_stage = Stage(name="Build")
    build_stage.steps = ["sh 'echo \"password=supersecret\"'"]
    
    deploy_stage = Stage(name="Deploy")
 
    deploy_stage.steps = ["sh 'docker run --privileged ubuntu'"]
    
    p.stages = [build_stage, deploy_stage]
    return p

def get_insecure_subtle_pipeline() -> Pipeline:
    """
    Returns a Pipeline object with a more subtle command injection vulnerability.
    """
    p = Pipeline()
    p.agent = {"label": "linux-worker"}
    
    scan_stage = Stage(name="Security Scan")
    scan_stage.steps = ["sh 'trivy fs --severity HIGH,CRITICAL --exit-code 1 /path/to/${params.BRANCH_NAME}'"]
    
    p.stages = [scan_stage]
    return p

def get_perfectly_secure_pipeline() -> Pipeline:
    """
    Returns a Pipeline object that follows best practices.
    """
    p = Pipeline()
    p.agent = {"docker": {"image": "maven:3.8-jdk-11-slim", "args": "-u 1000:1000"}}
    p.environment = {"SONAR_TOKEN": "credentials('sonar-token-id')"}
    
    build_stage = Stage(name="Build")
    build_stage.steps = [
        "withCredentials([string(credentialsId: 'nexus-password', variable: 'NEXUS_PASS')]) {",
        "  sh 'mvn clean deploy -Dpassword=${NEXUS_PASS}'",
        "}"
    ]
    
    p.stages = [build_stage]
    return p


def get_outdated_component_pipeline() -> Pipeline:
    """
    Returns a Pipeline with an old, known-vulnerable Docker image.
    PURPOSE: Specifically tests the agent's new web search capability.
    """
    p = Pipeline()
    # nginx 1.20.0 is known to be vulnerable to CVE-2021-23017
    p.agent = {"docker": {"image": "nginx:1.20.0"}}
    
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'echo Deploying vulnerable image...'"]
    p.stages = [deploy_stage]
    return p

def get_complex_insecure_pipeline() -> Pipeline:
    """
    Returns a Pipeline with a combination of multiple, different vulnerabilities.
    PURPOSE: Tests the agent's ability to handle a complex file with many issues.
    """
    p = Pipeline()
    p.agent = {"type": "any"} # Vulnerability 1
    p.environment = {
        "NEXUS_USER": "admin",
        "NEXUS_PASS": "${params.NEXUS_PASSWORD_PARAM}" 
    }
    
    build_stage = Stage(name="Build")
    build_stage.steps = ["sh 'echo \"API_TOKEN=tok_12345...\"'"] # Vulnerability 3
    
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'docker run --privileged nginx:1.20.0'"] # Vulnerability 4 & 5
    
    p.stages = [build_stage, deploy_stage]
    return p

def get_multistage_secure_pipeline() -> Pipeline:
    """
    Returns a longer, multi-stage pipeline that is completely secure.
    PURPOSE: A more robust test for false positives.
    """
    p = Pipeline()
    p.agent = {"label": "ubuntu-22.04"}
    p.environment = {"SONAR_HOST": "credentials('sonar-host-url')"}
    
    build_stage = Stage(name="Build")
    build_stage.steps = [
        "withCredentials([string(credentialsId: 'nexus-creds', variable: 'NEXUS_AUTH')]) {",
        "  sh 'mvn clean deploy -s settings.xml -Dnexus.auth=${NEXUS_AUTH}'",
        "}"
    ]
    
    test_stage = Stage(name="Test")
    test_stage.steps = ["sh 'mvn verify'"]
    
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'echo All secure, ready to deploy.'"]
    
    p.stages = [build_stage, test_stage, deploy_stage]
    return p

def get_env_command_injection_pipeline() -> Pipeline:
    """
    Returns a Pipeline with a command injection vulnerability in the environment block.
    """
    p = Pipeline()
    p.agent = {"label": "linux"}
    p.environment = {"NEXUS_PASSWORD": "${params.USER_SUPPLIED_PASSWORD}"}
    
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'deploy.sh --user admin --password $NEXUS_PASSWORD'"]
    p.stages = [deploy_stage]
    return p

def get_secure_withcredentials_pipeline() -> Pipeline:
    """
    Returns a Pipeline that uses the secure withCredentials pattern correctly.
    """
    p = Pipeline()
    p.agent = {"label": "linux"}
    
    build_stage = Stage(name="Build")
    build_stage.steps = [
        "withCredentials([string(credentialsId: 'nexus-password', variable: 'NEXUS_PASS')]) {",
        "  sh 'mvn clean deploy -Dpassword=${NEXUS_PASS}'",
        "}"
    ]
    p.stages = [build_stage]
    return p

def get_example_2_unused_env_pipeline() -> Pipeline:
    """From doc: A pipeline with an unused environment variable."""
    p = Pipeline()
    p.agent = {"type": "any"}
    p.environment = {"BUILD_MODE": "'release'"}
    build_stage = Stage(name="Build")
    build_stage.steps = ["sh 'make build'"]
    p.stages = [build_stage]
    return p

def get_example_3_hardcoded_secret_pipeline() -> Pipeline:
    """From doc: A pipeline with a hardcoded AWS secret key."""
    p = Pipeline()
    p.agent = {"type": "any"}
    p.environment = {"AWS_SECRET_KEY": "'AKIA1234567890XYZ'"}
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'aws deploy --key $AWS_SECRET_KEY'"]
    p.stages = [deploy_stage]
    return p

def get_example_4_dangerous_curl_pipeline() -> Pipeline:
    """From doc: A pipeline with a potentially dangerous curl command."""
    p = Pipeline()
    p.agent = {"type": "any"}
    deploy_stage = Stage(name="Deploy")
    deploy_stage.steps = ["sh 'curl -X POST http://insecure-service.local/deploy'"]
    p.stages = [deploy_stage]
    return p

def get_example_5_valid_multibranch_pipeline() -> Pipeline:
    """From doc: A valid, secure multibranch pipeline example."""
    p = Pipeline()
    p.agent = {"type": "any"}
    p.environment = {"DEPLOY_ENV": "'staging'"}
    
    checkout_stage = Stage(name="Checkout")
    checkout_stage.steps = ["checkout scm"]
    
    test_stage = Stage(name="Test")
    test_stage.steps = ["sh 'pytest tests/'"]
    
    deploy_stage = Stage(name="Deploy")
    deploy_stage.when = ["branch 'main'"]
    deploy_stage.steps = [
        "withCredentials([string(credentialsId: 'deploy-token', variable: 'TOKEN')]) {",
        "  sh 'curl -H \"Authorization: Bearer $TOKEN\" https://api.example.com/deploy'",
        "}"
    ]
    p.stages = [checkout_stage, test_stage, deploy_stage]
    return p

GROUND_TRUTH = {
    "1_insecure_obvious": {
        "expected_vulnerabilities": ["agent any", "hardcoded secret", "privileged"]
    },
    "2_insecure_subtle": {
        "expected_vulnerabilities": ["command injection"]
    },
    "3_perfectly_secure": {
        "expected_vulnerabilities": []
    },
    
    "4_outdated_component": {
        "expected_vulnerabilities": ["cve", "nginx:1.20.0"] # Check for the keyword "cve"
    },
    "5_complex_insecure": {
        "expected_vulnerabilities": ["agent any", "command injection", "hardcoded secret", "privileged", "cve"]
    },
    "6_multistage_secure": {
        "expected_vulnerabilities": []
    },
    "7_env_command_injection": {
        "expected_vulnerabilities": ["command injection"]
    },
    "8_secure_withcredentials": {
        "expected_vulnerabilities": []
    } , 
    "example_2_unused_env": {"expected_vulnerabilities": ["agent any"]},
    "example_3_hardcoded_secret": {"expected_vulnerabilities": ["agent any", "hardcoded secret"]},
    "example_4_dangerous_curl": {"expected_vulnerabilities": ["agent any"]}, # Curl itself isn't a finding based on our rules
    "example_5_valid_multibranch": {"expected_vulnerabilities": ["agent any"]}, 

}

'''"1_insecure_obvious": get_insecure_obvious_pipeline,
    "2_insecure_subtle": get_insecure_subtle_pipeline,
    "3_perfectly_secure": get_perfectly_secure_pipeline,
    "4_outdated_component": get_outdated_component_pipeline,
    "5_complex_insecure": get_complex_insecure_pipeline,
    "6_multistage_secure": get_multistage_secure_pipeline,
    "7_env_command_injection": get_env_command_injection_pipeline,
    "8_secure_withcredentials": get_secure_withcredentials_pipeline,  
    '''
BENCHMARK_CASES = {
    "example_2_unused_env": get_example_2_unused_env_pipeline,
    "example_3_hardcoded_secret": get_example_3_hardcoded_secret_pipeline,
    "example_4_dangerous_curl": get_example_4_dangerous_curl_pipeline,
    "example_5_valid_multibranch": get_example_5_valid_multibranch_pipeline, 
}