
import json
from ..state import AgentState, AuditTask
from ..config import llm_client
from ..tools.rulebook import rulebook_instance
from langchain_core.messages import AIMessage

class WorkerAuditor:
    def __init__(self):
        self.rulebook = rulebook_instance
        self.llm = llm_client
        
        all_rules = self.rulebook.get_all_rules()
        self.rulebook_context_str = json.dumps(all_rules, indent=2)
        
        
        self.prompt_template = """
***Persona:**
You are a meticulous and expert cybersecurity analyst. Your task is to analyze a code snippet based ONLY on the provided, authoritative `RULEBOOK_CONTEXT`.

**CRITICAL DIRECTIVE:**
Your analysis MUST be grounded in the `RULEBOOK_CONTEXT`.
**The `withCredentials` block is a primary security control in Jenkins. You MUST assume that any `sh` step inside a `withCredentials` block is SECURE and should NOT be flagged, unless it contains a *different*, clear violation like a second hardcoded secret.**

**RULEBOOK_CONTEXT (in JSON format):**
---
{rulebook_context}
---

**CODE_SNIPPET_TO_ANALYZE (from section: {section_name}):**

    
{code_snippet}
**Your Task:**
1.  Analyze the `CODE_SNIPPET`.
2.  Determine if it violates any of the rules described in the `RULEBOOK_CONTEXT`.
3.  If it does, format your finding using the data from the matching rule in the rulebook.

**OUTPUT_FORMAT:**
#### Vulnerability: [The 'title' from the matching rule]
- **Finding:** [A one-sentence description of how the code violates the rule.]
- **Violating Code:** `[The exact line of code from the snippet that violates the rule.]`
- **Severity:** [The 'cvss_score' from the matching rule.]
- **Remediation:** [The 'jenkins_remediation' from the matching rule.]

If the code does not violate any rules, your entire response MUST be the single sentence: "No security vulnerabilities were identified in this section."
"""

    def run_single_task(self, task: AuditTask) -> str:
        print(f"--- WorkerAuditor (In-Context): Auditing section '{task.section_name}'... ---")
        
        
        prompt = self.prompt_template.format(
            rulebook_context=self.rulebook_context_str, 
            section_name=task.section_name,
            code_snippet=task.code_snippet
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"!!! WorkerAuditor ERROR for section {task.section_name}: {e} !!!")
            return f"An error occurred during the analysis of section {task.section_name}."


worker_auditor_instance = WorkerAuditor()


def run_specialist_audit(state: AgentState) -> dict:
    """
    The node function that uses the WorkerAuditor instance to process all tasks.
    """
    tasks = state.get('tasks_to_do', [])
    findings = []
    for task in tasks:
        finding_content = worker_auditor_instance.run_single_task(task)
        findings.append(f"### Analysis for Section: `{task.section_name}`\n\n{finding_content}")

    return {"raw_findings": findings, "tasks_to_do": []}

    