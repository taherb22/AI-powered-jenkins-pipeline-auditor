import re
from typing import List, Dict
from .base_linter import BaseLinter 
from ai_powered_jenkins_auditor.models.stage import Stage



# In linters/stage_linter.py

class StageLinter(BaseLinter):
    _PATTERNS = {
        # These specific patterns should be checked first.
        "Hardcoded AWS Access Key ID": re.compile(r'AKIA[0-9A-Z]{16}'),
        "Hardcoded GitHub Token": re.compile(r'ghp_[0-9a-zA-Z]{36}'),
        
        # --- REVERTED PATTERN ---
        # This is the simple, correct generic pattern without the lookbehind.
        "Hardcoded Generic Secret": re.compile(
            r"""
            \b(key|secret|token|password|passwd|pwd|credentials?)\b
            \s*[:=]\s*
            (['"]?)
            (?!true|false|null\b)
            ([a-zA-Z0-9_/\-!@#$%^&*()+=]{8,})
            \2
            """,
            re.IGNORECASE | re.VERBOSE
        ),
        
        "Hardcoded User:Pass Credentials": re.compile(r'[a-zA-Z0-9\-_]+:[a-zA-Z0-9\-_!@#$%^&*()+=]{8,}'),
    }
    def _create_finding(self, line, finding_type, message, value, context):
        """
        A specialized version for this linter that uses the finding_type directly
        from the _PATTERNS dictionary without adding any prefix.
        """
        return {
            'line': line,
            'type': finding_type, # It uses the type directly
            'message': message,
            'value': value,
            'context': context
        }
    def lint(self, stages_data: List[Stage], context: Dict) -> List[Dict]:
        """
        Implements the linting logic, now with deduplication to prioritize
        specific findings over generic ones.
        """
        findings = []
        for stage in stages_data:
            stage_name = stage.name
            line_number = getattr(stage, 'start_line', 1)
            shell_commands = stage.steps

            for step_index, command in enumerate(shell_commands):
                # --- START OF NEW DEDUPLICATION LOGIC ---
                found_in_step = []
                # Prioritize specific patterns first
                specific_patterns = ["Hardcoded AWS Access Key ID", "Hardcoded GitHub Token", "Hardcoded User:Pass Credentials"]
                
                # 1. Run specific patterns
                for finding_type in specific_patterns:
                    pattern = self._PATTERNS[finding_type]
                    for match in pattern.finditer(command):
                        # ... (create finding as before) ...
                        finding_context = {"block": "stage", "stage_name": stage_name, "step_index": step_index}
                        message = f"A potential hardcoded secret ({finding_type}) was found in stage '{stage_name}'."
                        found_in_step.append(self._create_finding(line_number, finding_type, message, match.group(0), finding_context))
                
                # 2. If no specific secrets were found, run the generic pattern
                if not found_in_step:
                    pattern = self._PATTERNS["Hardcoded Generic Secret"]
                    for match in pattern.finditer(command):
                        # ... (create finding as before) ...
                        finding_context = {"block": "stage", "stage_name": stage_name, "step_index": step_index}
                        message = f"A potential hardcoded secret (Hardcoded Generic Secret) was found in stage '{stage_name}'."
                        found_in_step.append(self._create_finding(line_number, "Hardcoded Generic Secret", message, match.group(0), finding_context))

                findings.extend(found_in_step)
                # --- END OF NEW DEDUPLICATION LOGIC ---
        return findings