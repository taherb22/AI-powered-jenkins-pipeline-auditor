
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field
from ..models.pipeline import Pipeline  


class AuditTask(BaseModel):
    section_name: str = Field(description="The name of the section to audit (e.g., 'agent', 'stage', 'environment')")
    
    description: str = Field(description="A detailed prompt or instruction for the specialist agent.")
    code_snippet: str = Field(description="The relevant piece of the Jenkinsfile for this task.")
   
    

class AgentState(TypedDict):
    pipeline: Pipeline
    tasks_to_do: List[AuditTask]
    raw_findings: Annotated[List[str], operator.add]
    final_report: str