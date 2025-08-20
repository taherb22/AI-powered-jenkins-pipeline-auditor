import os
import pytest
from pathlib import Path

from ai_powered_jenkins_auditor.security_advisor_agent.workflow import app_workflow
from ai_powered_jenkins_auditor.security_advisor_agent.state import AgentState


from .benchmark_data import BENCHMARK_CASES

# --- Configuration ---
RESULTS_DIR = Path("benchmark_results")

@pytest.mark.slow
@pytest.mark.parametrize("case_name, pipeline_builder", BENCHMARK_CASES.items())
def test_security_agent_on_benchmark_case(case_name, pipeline_builder):
    """
    Runs the security agent against a single benchmark case defined as a Python object.
    This test is parameterized to run for every case in BENCHMARK_CASES.
    """
    # --- 1. ARRANGE ---
    print(f"\n--- Running Benchmark Case: {case_name} ---")
    
    # Create the results directory if it doesn't exist
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Get the Pipeline object from our data builder function
    pipeline_obj = pipeline_builder()
    
    initial_state: AgentState = {
        "pipeline": pipeline_obj,
        "tasks_to_do": [],
        "raw_findings": [],
        "final_report": ""
    }

    # --- 2. ACT ---
    # Invoke the agent workflow with the Python object
    final_state = app_workflow.invoke(initial_state)
    final_report = final_state.get("final_report", "Error: Report generation failed.")

    # --- 3. ASSERT & SAVE ---
    # Save the result to a file for manual review
    result_filename = RESULTS_DIR / f"{case_name}_report.md"
    with open(result_filename, 'w', encoding='utf-8') as f:
        f.write(final_report)
    
    print(f"--- Result saved to: {result_filename} ---")

    # Basic assertion to ensure the agent didn't crash
    assert final_report is not None
    assert "executive summary" in final_report.lower()

    # Here you would add more specific assertions for each case if desired
    if case_name == "3_perfectly_secure":
        assert "no security vulnerabilities were identified" in final_report.lower()