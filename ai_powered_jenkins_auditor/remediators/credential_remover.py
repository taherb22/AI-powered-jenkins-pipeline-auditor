# In ai_powered_jenkins_auditor/remediators/credential_remover.py

from __future__ import annotations
from typing import TYPE_CHECKING
import copy
from ai_powered_jenkins_auditor.models.pipeline import Pipeline


class CredentialRemover:
    """
    Takes a Pipeline object with rich findings and modifies a copy of it
    to remove or replace secrets.
    """
    def __init__(self):
        pass

    def remediate(self, pipeline: Pipeline, findings: list[dict]) -> Pipeline:
        """
        Remediates a pipeline object based on the provided findings.
        This method works by dispatching each finding to a specialized
        handler based on the 'context' provided in the finding.
        """
        
        remediated_pipeline = copy.deepcopy(pipeline)
        
        for finding in findings:
            context = finding.get('context', {})
            block_type = context.get('block')

           
            if block_type == 'agent':
                self._remediate_agent(remediated_pipeline, finding)
            elif block_type == 'environment':
                self._remediate_environment(remediated_pipeline, finding)
            elif block_type == 'stage':
                self._remediate_stage_step(remediated_pipeline, finding)
        
        return remediated_pipeline

    

    def _remediate_agent(self, pipeline: Pipeline, finding: dict):
        """Handles remediation for the 'agent' block."""
        placeholder = self._get_placeholder_variable(finding)

        def replace_secret(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and value == finding["value"]:
                        obj[key] = placeholder
                    else:
                        replace_secret(value)
            elif isinstance(obj, list):
                for item in obj:
                    replace_secret(item)

        replace_secret(pipeline.agent)
    def _remediate_environment(self, pipeline: Pipeline, finding: dict):
        """Handles remediation for the 'environment' block."""
        key_to_remediate = finding.get('context', {}).get('key')
        if key_to_remediate and key_to_remediate in pipeline.environment:
            placeholder = self._get_placeholder_variable(finding)
            pipeline.environment[key_to_remediate] = f"'{placeholder}'"

    def _remediate_stage_step(self, pipeline: Pipeline, finding: dict):
        """Handles remediation for a specific step within a specific stage."""
        context = finding.get('context', {})
        stage_name = context.get('stage_name')
        step_index = context.get('step_index')

        if stage_name is None or step_index is None:
            return
        for stage in pipeline.stages:
            if stage.name == stage_name:
                if step_index < len(stage.steps):
                    original_step = stage.steps[step_index]
                    value_to_remove = finding['value']
                    placeholder = self._get_placeholder_variable(finding)
                    replacement = placeholder
                    if '=' in value_to_remove:
                        key = value_to_remove.split('=', 1)[0]
                        replacement = f"{key}={placeholder}"
                    
                   
                    stage.steps[step_index] = original_step.replace(value_to_remove, replacement)
                break 
    def _get_placeholder_variable(self, finding: dict) -> str:
        """
        Generates a descriptive placeholder variable, e.g., ${REDACTED_API_KEY}.
        """
        var_name = finding['type'].replace("Hardcoded ", "").replace(" ", "_").upper()
        return f"${{REDACTED_{var_name}}}"