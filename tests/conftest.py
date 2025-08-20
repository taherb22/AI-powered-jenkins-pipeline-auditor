import pytest
from ai_powered_jenkins_auditor.jenkins_files_parser.jenkins_file_parser import JenkinsFileParser

@pytest.fixture(scope="module")
def parser() -> JenkinsFileParser:
    """Creates one parser instance for all tests in this file."""
    return JenkinsFileParser()

@pytest.fixture(scope="module")
def load_jenkinsfile():
    """
    A fixture that returns a helper function for loading test data files.
    """
    def _loader(name: str) -> str:
        """Loads a Jenkinsfile from the test_data directory."""
        path = f"tests/test_data/{name}.jenkinsfile"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            pytest.fail(f"Test data file not found at: {path}")
            
    return _loader