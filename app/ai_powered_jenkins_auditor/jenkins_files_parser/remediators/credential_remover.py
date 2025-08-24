      
from __future__ import annotations
from typing import TYPE_CHECKING
import re

from ai_powered_jenkins_auditor.models.pipeline import Pipeline
import logging
class CredentialRemover:
    """
    Removes hardcoded secrets from a Pipeline by replacing them with placeholders.
    Operates in-place on agent, environment, and stage blocks.
    """

    def __call__(self, pipeline: Pipeline, findings: list[dict]) -> Pipeline:
        secrets_map = {
            f["value"]: self._get_placeholder_variable(f)
            for f in findings
            if "Hardcoded" in f["type"]
        }
        if not secrets_map:
            return pipeline
        pipeline.agent = self._redact_value(pipeline.agent, secrets_map)
        pipeline.environment = self._redact_value(pipeline.environment, secrets_map)
        pipeline.stages = [
            self._redact_stage(stage, secrets_map) for stage in pipeline.stages
        ]
        return pipeline

    def _redact_stage(self, stage, secrets_map: dict[str, str]):
        stage.steps = self._redact_value(stage.steps, secrets_map)
        stage.when = self._redact_value(stage.when, secrets_map)
        return stage

    from typing import Union, List, Dict, Optional

    def _redact_value(
        self, 
        data: Union[str, Dict, List, None], 
        secrets_map: dict[str, str]
    ) -> Union[str, Dict, List, None]:
        """
        Recursively redacts secrets in strings, dictionaries, or lists.
        
        Args:
            data: The data to process (string, dict, list, or None)
            secrets_map: Mapping of secrets to their placeholders
            
        Returns:
            The redacted data with same type as input
        """
        if data is None:
            return None
            
        if isinstance(data, str):
            for secret, placeholder in secrets_map.items():
                if secret in data:
                    return data.replace(secret, placeholder)
            return data
        
        if isinstance(data, dict):
            return {k: self._redact_value(v, secrets_map) for k, v in data.items()}
        
        if isinstance(data, list):
            return [self._redact_value(item, secrets_map) for item in data]
        
        raise TypeError(f"Unsupported type for redaction: {type(data)}")

    def _get_placeholder_variable(self, finding: dict) -> str:
        """Returns a standardized redaction placeholder for sensitive values.
        
        Args:
            finding: A dictionary containing at least a "type" key indicating
                    what type of sensitive data was found (e.g., "Hardcoded Password")
        
        Returns:
            str: The redaction placeholder "***REDACTED***"
        """
       
        var_name = finding["type"].replace("Hardcoded ", "").replace(" ", "_").upper()
        
        logging.debug(f"Redacted {var_name}")
        return "***REDACTED***"
