# In ai_powered_jenkins_auditor/linters/base_linter.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseLinter(ABC):
    """
    An abstract base class that defines the contract for all linters.

    Each specific linter (e.g., for 'agent' or 'stage' blocks) must inherit
    from this class and implement the `lint` method. This ensures a consistent
    interface for the main PipelineOrchestrator.
    """

    @abstractmethod
    def lint(self, data: Any, context: Dict) -> List[Dict]:
        """
        The core method for a linter. It takes data and context, and returns findings.

        Args:
            data: The specific piece of the pipeline to be analyzed (e.g.,
                  the agent dictionary or a list of stage dictionaries).
            context: A dictionary containing metadata, such as the starting
                     line number of the block being analyzed.

        Returns:
            A list of finding dictionaries. An empty list means no issues were found.
        """
        pass

    def _create_finding(self, line: int, finding_type: str, message: str, value: str, context: Dict) -> Dict:
        """
        A helper method to create a consistently formatted finding dictionary.
        This includes the crucial 'context' for the remediator.
        """
        finding = {
            "line": line,
            "type": f"Hardcoded {finding_type}",
            "message": message,
            "value": value,
            "context": context  # The context is passed through
        }
        return finding