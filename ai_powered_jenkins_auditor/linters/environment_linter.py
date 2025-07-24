

import re
from typing import Dict, List, Any
from .base_linter import BaseLinter # 

class EnvironmentLinter(BaseLinter): 
    """
    Scans the key-value pairs from an 'environment' block for hardcoded secrets.
    """
    
    _SPECIFIC_PATTERNS = {
        "AWS Access Key ID": re.compile(r'AKIA[0-9A-Z]{16}'),
        "GitHub Token": re.compile(r'ghp_[0-9a-zA-Z]{36}'),
    }
    
    
    _GENERIC_KEYWORD_TRIGGERS = ['secret', 'token', 'password', 'passwd', 'pwd', 'key']

    def lint(self, environment_data: Dict[str, str], context: Dict) -> List[Dict]:
        """
        Implements the linting logic for the environment block's data.

        This method uses a two-pass system: first checking for high-confidence,
        specific secret patterns, and then checking for more generic secrets
        based on suspicious key names.

        Args:
            environment_data: A dictionary of key-value pairs from the environment block.
            context: A dictionary containing metadata, like the `line` number.
        
        Returns:
            A list of finding dictionaries, each including a rich 'context'.
        """
        findings = []
        if not isinstance(environment_data, dict):
            return [] # Silently ignore malformed data

        line_number = context.get('line', 1)

        for key, value in environment_data.items():
            clean_value = value.strip("'\"")
            found_specific_secret = False

            # --- PASS 1: Check for high-confidence, specific patterns in the value ---
            for finding_type, pattern in self._SPECIFIC_PATTERNS.items():
                if pattern.search(clean_value):
                   
                    finding_context = {"block": "environment", "key": key}
                    message = f"A high-confidence secret ({finding_type}) was found in the environment variable '{key}'."
                    finding = self._create_finding(line_number, finding_type, message, value, finding_context)
                    
                    findings.append(finding)
                    found_specific_secret = True
                    break  

            # --- PASS 2: If no specific secret was found, do a generic check ---
            if not found_specific_secret:
                is_suspicious_key = any(word in key.lower() for word in self._GENERIC_KEYWORD_TRIGGERS)
                is_safe_value = 'credentials(' in clean_value or '$' in clean_value or '{' in clean_value

                if is_suspicious_key and not is_safe_value:
                   
                    finding_context = {"block": "environment", "key": key}
                    message = f"The environment variable '{key}' may contain a hardcoded secret."
                    finding = self._create_finding(line_number, "Generic Secret", message, value, finding_context)
                    findings.append(finding)
                        
        return findings