
from .jenkins_file_parser import JenkinsFileParser
from .linters.agent_linter import AgentLinter
from .linters.stage_linter import StageLinter
from .remediators.credential_remover import CredentialRemover
from .models.pipeline import Pipeline 
from .linters.environment_linter import EnvironmentLinter


class PipelineManager:
    """
    The main service class that orchestrates the parsing, auditing,
    and remediation of Jenkinsfiles.
    """
    def __init__(self):
        self.parser = JenkinsFileParser()
        self.agent_linter = AgentLinter()
        self.stage_linter = StageLinter()
        self.remover = CredentialRemover() 
        self.env_linter = EnvironmentLinter()
        
    def run_audit(self, file_content: str) -> Pipeline:
        """
        Parses a Jenkinsfile, runs all linters, and returns a Pipeline
        object populated with the parsed data and all findings.
        """
        pipeline_obj = self.parser.parse(bytes(file_content, "utf8"))
        all_findings = []
    
        if pipeline_obj.agent:
            
            agent_data, line_number = ('any', 1)
            if isinstance(pipeline_obj.agent, tuple):
                 agent_data, line_number = pipeline_obj.agent
            else: 
                 agent_data = pipeline_obj.agent
            
            agent_context = {'line': line_number}
            agent_findings = self.agent_linter.lint(agent_data, agent_context)
            all_findings.extend(agent_findings)
            
    
        if pipeline_obj.environment:
            
            env_line_number = 1 
            env_context = {'line': env_line_number}
            env_findings = self.env_linter.lint(pipeline_obj.environment, env_context)
            all_findings.extend(env_findings)

        
        if pipeline_obj.stages:
            stage_context = {} 
            stage_findings = self.stage_linter.lint(pipeline_obj.stages, stage_context)
            all_findings.extend(stage_findings)
            
        pipeline_obj.findings = all_findings
        return pipeline_obj

   
    def run_remediation(self, file_content: str) -> Pipeline:
        """
        Performs a full audit and then passes the resulting Pipeline object
        to the CredentialRemover for remediation.

        Args:
            file_content: The original string content of the Jenkinsfile.

        Returns:
            A new, remediated Pipeline object as returned by the CredentialRemover.
        """
        
        audited_pipeline = self.run_audit(file_content)
        if audited_pipeline.findings:
            
            remediated_pipeline = self.remover.remediate(audited_pipeline, audited_pipeline.findings)
            return remediated_pipeline
        else:

            return audited_pipeline