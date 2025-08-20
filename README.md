    
# AI-Powered Jenkins Auditor

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg) ![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)

An intelligent, multi-agent system designed to perform a comprehensive security audit of Jenkins declarative pipelines. This tool leverages a powerful Large Language Model, grounded by a curated knowledge base, to identify a wide range of security vulnerabilities and code quality issues.

## Overview

Traditional security scanners often rely on rigid, predefined rules. This project takes a modern approach by combining fast, rule-based linting with the advanced contextual reasoning of a multi-agent AI system. The result is a tool that can find not only common misconfigurations but also subtle, context-dependent security flaws.

The agent's intelligence is grounded in a curated knowledge base derived from authoritative sources like the **CWE Top 25** and the **OWASP CI/CD Security Top 10**, ensuring its findings are accurate, reliable, and actionable.

## Features

-   **Hybrid Analysis:** Combines a fast, rule-based linter for common secrets with a sophisticated multi-agent system for deep logical analysis.
-   **Intelligent Vulnerability Detection:** Identifies risks like hardcoded secrets, command injection, insecure agent configurations, use of vulnerable components, and logical flaws.
-   **Actionable Reporting:** Generates a clean, professional Markdown report for each audited file, detailing each finding, its risk, the violating code, and a specific remediation suggestion.
-   **Automated Remediation:** Includes an optional mode to automatically redact hardcoded secrets from the parsed pipeline object.
-   **Batch Processing:** Capable of scanning an entire directory of Jenkinsfiles in a single run.

## Project Structure

The project is organized into a clean, modular structure to separate concerns:

  

AI-POWERED-JENKINS-AUDITOR/
├── main.py                     # The main command-line entry point
├── knowledge_base/             # Contains the security rules for the AI agent
│   └── rules.json
├── jenkins_files_directory/    # Default directory for Jenkinsfiles to be audited
├── audit_reports/              # Default directory for generated reports
├── tests/                      # The test suite
└── ai_powered_jenkins_auditor/
    ├── Parser/                 # Contains the parser, linters, and remediators
    └── security_agent/         # The core multi-agent AI system

    
## Getting Started

### Prerequisites

-   [Python](https://www.python.org/downloads/) (3.10+)
-   [Poetry](https://python-poetry.org/docs/#installation)
-   [Git](https://git-scm.com/downloads/)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AI-Powered-Jenkins-Auditor.git
    cd AI-Powered-Jenkins-Auditor
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

### Configuration

The AI agent requires an API key from grok cloud  to function.

1.  **Get an API Key:** Obtain an API key from grok cloud 

2.  **Create an environment file:**
    ```bash
    cp .env.example .env
    ```

3.  **Add your key to the `.env` file:**
    ```ini
    # .env
    GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxx"
    ```

## Usage

The application is run from the command line via `main.py`.

### Basic Audit

To run a security audit on the default `jenkins_files_directory/` and save the reports to the default `audit_reports/` directory, simply run:

```bash
poetry run python main.py

  