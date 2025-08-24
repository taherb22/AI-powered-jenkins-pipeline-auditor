from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from .linter_config import LinterConfig
from ai_powered_jenkins_auditor.models.stage import Stage


class StageLinter:
    """
    Inspects Stage objects for hardcoded secrets in both their `steps` and `when` blocks.
    """

    def __call__(self, stages: list[Stage]) -> list[dict]:
        return list(self._find_in_stages(stages))

    def _find_in_stages(self, stages: list[Stage]) -> Iterable[dict]:
        for stage in stages:
            yield from self._find_secrets_in_list(stage.steps, stage.name, "step")
            yield from self._find_secrets_in_list(stage.when, stage.name, "when condition")

    def _find_secrets_in_list(self, lines: list[str], stage_name: str, context: str) -> Iterable[dict]:
        if not isinstance(lines, list):
            return
        for line_content in lines:
            match = LinterConfig.HARDCODED_SECRET_PATTERN.search(line_content)
            if match:
                yield {
                    "line": "N/A",
                    "type": "Hardcoded Secret",
                    "message": f"Potential hardcoded secret found in a {context} within stage '{stage_name}'.",
                    "value": match.group(0)
                }
