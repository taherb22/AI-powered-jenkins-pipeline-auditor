import json
from ..state import AgentState, AuditTask
from ...models.pipeline import Pipeline

def plan_initial_audit(state: AgentState) -> dict:
    """
    Creates a comprehensive audit plan using a reliable, rule-based approach.
    It creates tasks with general, semantic descriptions suitable for RAG retrieval.
    """
    print("--- Lead Auditor: Creating audit plan (Manual)... ---")
    pipeline: Pipeline = state['pipeline']
    tasks = []

    if pipeline.agent:
        tasks.append(AuditTask(
            section_name="agent",
            description="Security analysis of agent configuration for least-privilege and insecure patterns.",
            code_snippet=json.dumps(pipeline.agent)
        ))
        
    if pipeline.environment:
        tasks.append(AuditTask(
            section_name="environment",
            description="Security analysis of environment variables for hardcoded secrets and command injection.",
            code_snippet=json.dumps(pipeline.environment)
        ))
        
    for stage in pipeline.stages:
        tasks.append(AuditTask(
            section_name=f"stage_{stage.name}",
            description=f"Comprehensive security analysis of the '{stage.name}' stage, including checks for hardcoded secrets, command injection, insecure dependencies, and logical flaws.",
            code_snippet=json.dumps(stage.to_dict())
        ))
        
    if pipeline.post:
        tasks.append(AuditTask(
            section_name="post",
            description="Security analysis of post-build actions for data leakage and insecure operations.",
            code_snippet=json.dumps(pipeline.post)
        ))
    
    print(f"--- Lead Auditor: Manually created {len(tasks)} tasks. ---")
    return {"tasks_to_do": tasks}