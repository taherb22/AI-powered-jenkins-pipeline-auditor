import json
from ..state import AgentState
from ..config import llm_client
from ..tools.rulebook import rulebook_instance 
from langchain_core.messages import AIMessage
from ai_powered_jenkins_auditor.models import pipeline

class HolisticAuditor:
    """
    An agent that performs a holistic, cross-sectional analysis of the entire
    pipeline object to find unused or redundant definitions.
    """
    def __init__(self):
        self.rulebook = rulebook_instance
        self.llm = llm_client
        self.prompt_template = """
**Persona:**
You are an expert Jenkins pipeline optimizer and code quality analyst. Your task is to analyze a complete, structured representation of a Jenkinsfile to find "dead code" - specifically, unused environment variables and redundant agent definitions.

**Rules for Analysis:**
1.  **Unused Environment Variable:** An environment variable is "unused" if it is defined in the top-level `environment` block but its name does not appear as a variable (e.g., `$VAR` or `${{VAR}}`) inside any `steps` or `when` block of any stage.
2.  **Redundant Stage Agent:** An agent defined inside a `stage` is "redundant" if a global `agent` is already defined at the top level of the pipeline (and is not `agent none`). The global agent will be used by default, making the stage-level agent unnecessary.

**CONTEXT (Full Pipeline Data in JSON format):**
```json
{pipeline_json}
Your Task:

    Analyze the full pipeline data provided in the CONTEXT.

    Compare the defined environment variables against their usage in all stages.

    Check if any stage has an agent definition when a global agent is also present.

    If you find any violations of the rules, report them using the OUTPUT_FORMAT.

OUTPUT_FORMAT:
If you find one or more violations, respond with a list of findings in this Markdown format.
Vulnerability: [Title of the Rule Violated]

    Finding: [A one-sentence description of the unused or redundant definition.]

    Location: [The key or stage name where the unused item was defined.]

    Remediation: [A one-sentence suggestion on how to fix it.]

    Severity: [LOW]

If you find no violations, you MUST respond with the single sentence: "No unused or redundant definitions were found."
"""
    
    def run_analysis(self, pipeline: pipeline) -> str:
        """
        Runs the holistic analysis on the entire Pipeline object.
        """
        print("--- HolisticAuditor: Performing full-pipeline analysis... ---")
        
        pipeline_json = json.dumps(pipeline.to_llm_context(), indent=2)
        
        prompt = self.prompt_template.format(pipeline_json=pipeline_json)
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"!!! HolisticAuditor ERROR: {e} !!!")
            return "An error occurred during holistic analysis."

holistic_auditor_instance = HolisticAuditor()

def run_holistic_audit(state: AgentState) -> dict:
    """
    The node function that uses the HolisticAuditor instance.
    It runs its analysis and adds any findings to the main findings list.
    """
    pipeline = state['pipeline']  
    holistic_finding_content = holistic_auditor_instance.run_analysis(pipeline)

    
    if "no unused or redundant definitions were found" not in holistic_finding_content.lower():
    
        formatted_finding = f"### Analysis for Section: `Pipeline-Wide`\n\n{holistic_finding_content}"
        return {"raw_findings": [formatted_finding]}

    return {}