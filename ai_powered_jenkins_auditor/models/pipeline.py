

from __future__ import annotations
from typing import List, Any, Dict 
from ai_powered_jenkins_auditor.models.stage import Stage

class Pipeline:
    """
    Represents the structured data of a parsed Jenkinsfile and the results
    of any audits performed on it.
    """
    def __init__(self):
        """
        Initializes the Pipeline data object.
        """
        self.agent: Any = None
        self.stages: List[Stage] = []
        self.environment: Dict[str, str] = {}
        self.post: Dict[str, list[str]] = {}
        self.findings: List[Dict] = []

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0

    def to_dict(self) -> Dict:
        """
        Converts the Pipeline object into a dictionary for easy serialization or printing.
        """
        return {
            "agent": self.agent,
            "stages": [stage.to_dict() for stage in self.stages], 
            "environment": self.environment,
            "post": self.post,
            "findings": self.findings 
        }