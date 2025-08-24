from .linter_config import LinterConfig

class EnvironmentLinter:
    def __call__(self, environment_data: dict, line_number: int = 1) -> list[dict]:
        if not isinstance(environment_data, dict):
            return []

        suspicious_keywords = LinterConfig.SUSPICIOUS_KEY_KEYWORDS
        safe_tokens = ('credentials(', '$', '{')
        secret_pattern = LinterConfig.HARDCODED_SECRET_PATTERN

        def valid_strings():
            return (
                (key, value)
                for key, value in environment_data.items()
                if isinstance(value, str) and not any(token in value for token in safe_tokens)
            )

        def hardcoded_secrets():
            for key, value in valid_strings():
                match = secret_pattern.search(value)
                if match:
                    yield {
                        "line": line_number,
                        "type": "Hardcoded Secret",
                        "message": f"Potential hardcoded secret found in the value of environment variable '{key}'.",
                        "value": match.group(0)
                    }
                else:
                    yield from suspicious_keys(key, value)

        def suspicious_keys(key, value):
            lower_key = key.lower()
            if any(keyword in lower_key for keyword in suspicious_keywords):
                yield {
                    "line": line_number,
                    "type": "Hardcoded Secret",
                    "message": f"The environment variable '{key}' has a suspicious name and may contain a hardcoded secret.",
                    "value": value
                }

        return list(hardcoded_secrets())
