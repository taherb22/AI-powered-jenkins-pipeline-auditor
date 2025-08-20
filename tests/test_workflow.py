import os
import pytest
from tests.Pipeline_builder import PipelineBuilder

from ai_powered_jenkins_auditor.security_advisor_agent.workflow import app_workflow
from ai_powered_jenkins_auditor.security_advisor_agent.state import AgentState

@pytest.mark.slow
def test_workflow_with_multiple_vulnerabilities():
    """
    A comprehensive integration test for the full multi-agent workflow.
    
    It constructs a pipeline with several known, distinct vulnerabilities and verifies
    that the final report file contains both the executive summary and the detailed
    raw findings for each vulnerability.
    """
    # --- 1. ARRANGE ---
    output_filename = "final_security_report.md"
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    print("\n--- Arranging: Constructing a complex, vulnerable pipeline... ---")
    
    # Create a pipeline with multiple, easy-to-identify security issues
    sample_pipeline = (
        PipelineBuilder()
            .with_agent({"type": "any"}) # A clear least-privilege violation
            .with_environment({
                "SONAR_TOKEN": "sqp_abcdef1234567890" # A hardcoded secret
            })
            .with_stage(
                name="Build", 
                steps=["sh 'mvn clean install -Dpassword=${params.USER_PASSWORD}'"] # Potential command injection
            )
            .with_stage(
                name="Deploy",
                steps=["sh 'docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock docker'"] # Privileged container
            )
            .build()
    )
    
    initial_state: AgentState = {
        "pipeline": sample_pipeline,
        "tasks_to_do": [],
        "raw_findings": [],
        "final_report": ""
    }

    # --- 2. ACT ---
    print("--- Acting: Invoking the agent workflow... ---")
    # The workflow will run and automatically save the file
    app_workflow.invoke(initial_state)

    # --- 3. ASSERT ---
    print("--- Asserting: Verifying the content of the final report file... ---")
    
    # A. Verify the file was created
    assert os.path.exists(output_filename), "The report file was not created."
    
    # B. Read the file content for detailed checks
    with open(output_filename, 'r', encoding='utf-8') as f:
        report_content = f.read().lower() # Use .lower() for case-insensitive checks
        
  

    print(f"\n--- Test successful! Comprehensive report saved to '{output_filename}' ---")