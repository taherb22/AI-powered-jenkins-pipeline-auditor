import re

class AgentLinter:
    """
    Finds hardcoded secret-like values in agent data represented as simple Python dict or string.
    """

    def __init__(self):
        # Keywords indicating a secret-related field
        self.secret_keywords = {"password", "token", "secret", "credentialsid", "apikey", "accesskey", "privatekey"}
        # Patterns to detect known secrets
        self.aws_pattern = re.compile(r'AKIA[0-9A-Z]{16}')
        self.jwt_pattern = re.compile(r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+')
        # Valid Jenkins credentials ID pattern (alphanumeric, dash, underscore)
        self.id_pattern = re.compile(r'^[A-Za-z0-9_\-]+$')

    def lint(self, agent_data: any, line_number: int = 1) -> list[dict]:
        """
        Takes the extracted agent data (a dict, list or string) and inspects it.
        """
        findings = []
        self._check_value(agent_data, line_number, findings, parent_key=None)
        return findings

    def _check_value(self, value: any, line: int, findings: list[dict], parent_key: str | None):
        """
        Recursively checks a value (string, dict, or list) for hardcoded secrets or suspicious values.
        """
        if isinstance(value, str):
            val = value.strip()
            key_lower = parent_key.lower() if parent_key else ''
            # Skip non-values or variables
            if val.lower() in ('any', 'none') or '$' in val or '{' in val or val.startswith('credentials('):
                return

            is_suspicious = bool(self.aws_pattern.search(val) or self.jwt_pattern.search(val) or len(val) >= 30)
            is_secret_field = bool(parent_key and any(k in key_lower for k in self.secret_keywords))

            # Handle secret fields first
            if is_secret_field:
                # JWT under secret field: flag Hardcoded Secret
                if self.jwt_pattern.search(val):
                    findings.append({
                        'line': line,
                        'type': 'Hardcoded Secret',
                        'message': f"Hardcoded secret-like value under '{parent_key}': '{val}'",
                        'value': val
                    })
                # Other non-ID values (except AWS keys) under secret field: flag Hardcoded Secret
                elif not self.id_pattern.match(val) and not self.aws_pattern.search(val):
                    findings.append({
                        'line': line,
                        'type': 'Hardcoded Secret',
                        'message': f"Hardcoded secret-like value under '{parent_key}': '{val}'",
                        'value': val
                    })
                # Continue to suspicious detection
            # Suspicious detection
            if is_suspicious:
                findings.append({
                    'line': line,
                    'type': 'Suspicious Agent Value',
                    'message': f"Suspicious hardcoded string in agent block: '{val}'",
                    'value': val
                })
                return

        elif isinstance(value, dict):
            for k, v in value.items():
                self._check_value(v, line, findings, parent_key=k)

        elif isinstance(value, list):
            for item in value:
                self._check_value(item, line, findings, parent_key=parent_key)
