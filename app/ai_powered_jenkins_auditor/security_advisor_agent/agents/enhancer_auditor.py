
from ..state import AgentState
from ..config import llm_client
from langchain_core.messages import AIMessage
SUMMARY_PROMPT_TEMPLATE = """
**Persona:**
You are a Principal Security Consultant. Your task is to write a high-level executive summary based on a list of technical findings.

**Context:**
You have been given the following raw security findings from an automated scan of a Jenkinsfile.
{raw_findings}```
Task:
Write a brief, high-level executive summary (2-4 sentences) of the overall security posture. This summary MUST include the total number of vulnerabilities found and a mention of the highest severity level discovered (e.g., "Critical," "High," "Medium," or "Low").

Output:
Provide ONLY the text for the executive summary. Do not add any other headings, titles, or the detailed findings themselves.
"""


def generate_final_report(state: AgentState) -> dict:
    """
    Creates a comprehensive report using a more reliable two-step process:
    1. An LLM call to generate ONLY the executive summary.
    2. A simple Python f-string to assemble the final report.
    """
    print("--- Enhancer: Generating comprehensive report (Isolate & Format)... ---")
    
    raw_findings = state.get('raw_findings', [])
    
    is_completely_clean = all(
        "no security vulnerabilities were identified" in finding.lower()
        for finding in raw_findings
    )

    if not raw_findings or is_completely_clean:
        # Handle the case where there are truly no findings.
        final_report_content = "# Jenkins Pipeline Security Audit Report\n\n## Executive Summary\n\nNo security vulnerabilities were identified during the scan. The pipeline appears to be configured securely according to the checks performed."
    else:
        # If there is at least one real finding, proceed with the summary and report.
        raw_findings_str = "\n\n---\n\n".join(raw_findings)
        
        # --- Step 1: Generate ONLY the Executive Summary ---
        print("--- Enhancer (Step 1): Calling LLM to generate summary... ---")
        summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(raw_findings=raw_findings_str)
        
        try:
            summary_response = llm_client.invoke(summary_prompt)
            executive_summary = summary_response.content if isinstance(summary_response, AIMessage) else str(summary_response)
        except Exception as e:
            print(f"!!! Enhancer ERROR: Failed to generate summary: {e} !!!")
            executive_summary = "An error occurred while generating the summary."

        # --- Step 2: Assemble the Final Report using an f-string ---
        print("--- Enhancer (Step 2): Assembling final report... ---")
        final_report_content = f"""# Jenkins Pipeline Security Audit Report

## Executive Summary
{executive_summary}

---

## Detailed Specialist Findings
{raw_findings_str}
"""
    
    print("--- Enhancer: Final comprehensive report generated. ---")
    return {"final_report": final_report_content.strip()}

# (The save_report_to_file function remains exactly the same)
def save_report_to_file(state: AgentState) -> dict:
 
    print("--- I/O: Saving final report to file... ---")
    report_content = state.get("final_report", "Error: No report content found.")
    
    # You can make the filename configurable in config.py if you want
    output_filename = "final_security_report.md"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"--- I/O: Report successfully saved to {output_filename} ---")
    except IOError as e:
        print(f"!!! I/O ERROR: Failed to write report to file {output_filename}: {e} !!!")
        
    
    return {}