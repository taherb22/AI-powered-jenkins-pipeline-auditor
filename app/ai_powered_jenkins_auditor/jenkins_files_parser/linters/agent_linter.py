from .linter_config import LinterConfig
from collections.abc import Iterable

class AgentLinter:
    """
    Callable object that inspects agent data for vulnerabilities
    using an iterative approach and match-case for type dispatch.
    """

    def __call__(self, agent_data: any, line_number: int = 1):
        """
        Makes the AgentLinter instance callable.
        Iteratively checks the agent data for issues and yields findings.
        """
        yield from self._lint_iterative(agent_data, line_number, parent_key="agent")

    def _lint_iterative(self, value: any, line: int, parent_key: str):
        """
        Iteratively checks a value for hardcoded secrets using a stack,
        with match-case instead of if-else.
        """
        stack = [(parent_key, value, line)]

        while stack:
            key, current_value, current_line = stack.pop()

            match current_value:
                case str():
                    match_obj = LinterConfig.HARDCODED_SECRET_PATTERN.search(current_value)
                    if match_obj:
                        yield {
                            "line": current_line,
                            "type": "Hardcoded Secret",
                            "message": f"Potential hardcoded secret found in agent key '{key}'.",
                            "value": match_obj.group(0)
                        }

                case dict():
                    stack.extend((k, v, current_line) for k, v in current_value.items())

                case list() | tuple():
                    stack.extend((key, item, current_line) for item in current_value)
