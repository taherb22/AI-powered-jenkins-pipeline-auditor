import re
from pathlib import Path
from ai_powered_jenkins_auditor.security_advisor_agent.workflow import app_workflow
from ai_powered_jenkins_auditor.security_advisor_agent.state import AgentState
from tests.benchmark_data import BENCHMARK_CASES, GROUND_TRUTH


RESULTS_DIR = Path("benchmark_results")
def run_and_generate_table():
    """
    This function will:
    1. Run the agent against every case in the benchmark dataset.
    2. Score the results based on the ground truth.
    3. Print a final summary table to the console.
    """
    
    RESULTS_DIR.mkdir(exist_ok=True)
    
   
    table_data = []

    print("--- Starting Benchmark Run ---")

   
    for case_name, pipeline_builder in BENCHMARK_CASES.items():
        print(f"\n--- Running Benchmark Case: {case_name} ---")
        
        
        pipeline_obj = pipeline_builder()
        ground_truth = GROUND_TRUTH[case_name]
        
       
        initial_state: AgentState = {
            "pipeline": pipeline_obj, "tasks_to_do": [], "raw_findings": [], "final_report": ""
        }
        final_state = app_workflow.invoke(initial_state)
        final_report = final_state.get("final_report", "Error: Report generation failed.")
        
       
        result_filename = RESULTS_DIR / f"{case_name}_report.md"
        result_filename.write_text(final_report, encoding='utf-8')
        print(f"--- Full report saved to: {result_filename} ---")

        
        report_lower = final_report.lower()
        expected_vulnerabilities = ground_truth["expected_vulnerabilities"]
        
        
        found_count = sum(1 for vuln in expected_vulnerabilities if vuln in report_lower)
        
        
        reported_count = len(re.findall(r"#### vulnerability:", report_lower))
        
        
        status = "✅ PASS"
        details = f"Found {found_count}/{len(expected_vulnerabilities)} expected issues."
        
        if found_count < len(expected_vulnerabilities):
            status = "❌ FAIL"
            details = f"Missed {len(expected_vulnerabilities) - found_count} expected issue(s)."
        
        false_positives = reported_count - found_count
        if false_positives > 0:
            status = "❌ FAIL"
            details += f" Reported {false_positives} unexpected issue(s)."

        if not expected_vulnerabilities and reported_count > 0:
            status = "❌ FAIL"
            details = f"Reported {reported_count} false positive(s)."
        elif not expected_vulnerabilities and reported_count == 0:
            status = "✅ PASS"
            details = "Correctly found no issues."

        
        table_data.append({
            "case": case_name,
            "status": status,
            "details": details
        })

 
    print("\n\n" + "="*65)
    print("---                BENCHMARK RESULTS SUMMARY                ---")
    print("="*65 + "\n")
    
    # Print table header
    print(f"| {'Benchmark Case'.ljust(25)} | {'Status'.ljust(8)} | {'Details'.ljust(40)} |")
    print(f"|:{'-'*25}|:{'-'*8}|:{'-'*40}|")
    
    # Print table rows
    for row in table_data:
        print(f"| {row['case'].ljust(25)} | {row['status'].ljust(8)} | {row['details'].ljust(40)} |")
        
    print("\n" + "="*65)
    print(f"Detailed reports for each run are saved in the '{RESULTS_DIR}' directory.")
    print("="*65 + "\n")


if __name__ == "__main__":
    run_and_generate_table()