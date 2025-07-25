# AI-Powered Jenkins Auditor

A tool to parse, analyze, and remediate Jenkinsfiles for security and best practices.

## Installation

This project is managed with [Poetry](https://python-poetry.org/).



1.  **Install dependencies with Poetry:**
    ```bash
    poetry install
    ```

2.  **Download the NLP Model:**
    The PII linter requires a SpaCy language model. This must be downloaded separately after the main dependencies are installed.
    ```bash
    poetry run python -m spacy download en_core_web_sm
    ```

## Usage

To run the tests:
```bash
poetry run pytest# Update for testing webhook
