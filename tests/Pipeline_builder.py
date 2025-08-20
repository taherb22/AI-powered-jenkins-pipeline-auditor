from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage
from typing import List, Dict, Any

class PipelineBuilder:
    """
    A builder class to conveniently construct Pipeline objects for testing.
    Uses a fluent interface to allow for chaining of method calls.
    """
    def __init__(self):
        self._pipeline = Pipeline()

    def with_agent(self, agent_data: Any) -> 'PipelineBuilder':
        self._pipeline.agent = agent_data
        return self

    def with_stage(self, name: str, steps: List[str]) -> 'PipelineBuilder':
        """Correctly creates a Stage object and adds it to the pipeline."""
        # The FIX is here: Pass 'name' directly into the Stage constructor.
        stage = Stage(name=name)
        stage.steps = steps
        self._pipeline.stages.append(stage)
        return self

    def with_environment(self, env_data: Dict[str, str]) -> 'PipelineBuilder':
        self._pipeline.environment = env_data
        return self

    def with_post(self, post_data: Dict[str, list[str]]) -> 'PipelineBuilder':
        self._pipeline.post = post_data
        return self

    def with_findings(self, findings_data: List[Dict]) -> 'PipelineBuilder':
        self._pipeline.findings = findings_data
        return self

    def build(self) -> Pipeline:
        """Returns the fully constructed Pipeline object."""
        return self._pipeline