from .jenkins_file_parser import JenkinsFileParser
from .linters.agent_linter import AgentLinter
from .linters.stage_linter import StageLinter
from .remediators.credential_remover import CredentialRemover
from ..models.pipeline import Pipeline
from .linters.environment_linter import EnvironmentLinter
from .linters.pii_linter import PiiLinter


class PipelineManager:
    """
    The main service class that orchestrates parsing, auditing,
    and remediation of Jenkinsfiles.
    """
    def __init__(self):
        self.parser = JenkinsFileParser()
        self.agent_linter = AgentLinter()
        self.stage_linter = StageLinter()
        self.remover = CredentialRemover()
        self.env_linter = EnvironmentLinter()
        self.pii_linter = PiiLinter()

    def run_audit(self, file_content: str):
        """
        Parses a Jenkinsfile and yields findings lazily instead of
        storing them all in a list.
        """
        pipeline_obj = self.parser.parse(bytes(file_content, "utf8"))

        
        linter_map = {
            "agent": self.agent_linter,
            "environment": self.env_linter,
            "stages": self.stage_linter
        }

        for attr, linter in linter_map.items():
            value = getattr(pipeline_obj, attr, None)
            if value:
                yield from linter(value)

        
        yield from self.pii_linter.lint(pipeline_obj)

    

    def run_remediation(self, file_content: str) -> Pipeline:
        """
        Performs a full audit and then passes the resulting Pipeline object
        to the CredentialRemover for remediation.
        """
        
        text_bytes = file_content.encode("utf-8") if isinstance(file_content, str) else bytes(file_content)
        pipeline_obj = self.parser.parse(text_bytes)
        findings = list(self.run_audit(file_content))
        
        pipeline_obj.findings = findings
        if pipeline_obj.findings:

            anonymized_pipeline = self.remover(pipeline_obj, pipeline_obj.findings)
            for i, s in enumerate(anonymized_pipeline.stages):
                print(f"Stage[{i}].name = {s.name!r}")
                print(f"Stage[{i}].steps = {s.steps}")
                print(f"Stage[{i}].when = {s.when}")
                print("---")
            return anonymized_pipeline
        
        
        return pipeline_obj
        
    