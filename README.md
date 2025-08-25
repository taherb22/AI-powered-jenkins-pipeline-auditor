AI-Powered Jenkins Auditor

![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)

![alt text](https://img.shields.io/badge/python-3.11+-blue.svg)

![alt text](https://img.shields.io/badge/dependency%20management-Poetry-blueviolet)

An intelligent, multi-agent system designed to perform a comprehensive security audit of Jenkins declarative pipelines. This tool leverages a powerful Large Language Model (LLM), grounded by a curated knowledge base, to identify a wide range of security vulnerabilities and code quality issues.

The auditor integrates directly into the developer workflow by listening to GitHub Pull Request webhooks, automatically auditing any Jenkinsfile in the PR, and posting the detailed report back as a PR comment.
Key Features

    Automated Security Auditing: Automatically scans Jenkinsfile configurations for common security flaws, such as hardcoded secrets, insecure shell commands, and improper agent usage.

    AI-Powered Analysis: Utilizes a multi-agent system powered by the Groq LLM API to provide deep, context-aware analysis and actionable remediation advice.

    Seamless GitHub PR Integration: Listens for pull request events (opened, synchronize) and posts audit reports directly as comments, providing immediate feedback to developers.

    Event-Driven Architecture: A robust, event-driven design using a FastAPI webhook handler that directly triggers the audit process, eliminating the need for inefficient polling.

    Containerized and Portable: The entire application is containerized using Docker and orchestrated with Docker Compose, making it easy to set up and run in any environment.

    Local Development Ready: Includes an ngrok service in the docker-compose setup to easily expose the local webhook endpoint to the public internet for testing with GitHub.

How It Works (Architecture)

The application uses a clean, event-driven architecture where services are decoupled and communicate through webhooks and shared volumes.
code Mermaid

    
graph TD
    A[Developer opens/updates PR on GitHub] --> B{GitHub Webhook};
    B --> C{ngrok Tunnel};
    C --> D[FastAPI Server (app.py)];
    
    subgraph Docker Compose Services
        D;
        E[Audit Script (main.py)];
        F[Shared Volume: jenkins_files_directory];
        G[Shared Volume: audit_reports];
    end

    D -- Fetches Jenkinsfile --> H[GitHub API];
    D -- Saves file to --> F;
    D -- Executes as subprocess --> E;
    E -- Reads file from --> F;
    E -- Audits using --> I{Groq LLM API};
    E -- Writes report to --> G;
    D -- Reads report from --> G;
    D -- Posts comment to --> H;

  

    A developer opens or updates a Pull Request on GitHub.

    GitHub sends a webhook event to the public ngrok URL.

    ngrok forwards the request to the FastAPI server (app.py) running in a Docker container.

    app.py verifies the webhook signature, then uses the GitHub API to fetch the Jenkinsfile from the PR.

    The Jenkinsfile is saved to a shared Docker volume (jenkins_files_directory).

    app.py then executes the audit script (main.py) as a direct subprocess.

    main.py reads the Jenkinsfile, performs the AI-powered audit using the Groq API, and saves the markdown report to another shared volume (audit_reports).

    Once main.py completes, app.py finds the new report, reads it, and uses the GitHub API to post it as a comment on the original pull request.

Getting Started

Follow these instructions to get the auditor running on your local machine.
Prerequisites

    Git

    Docker and Docker Compose

    An ngrok account and authtoken.

    A GitHub Personal Access Token (PAT) with repo scope.

Installation & Setup

    Clone the repository:
    code Bash


    
git clone <your-repository-url>
cd testing_purposes_internship

  

Create the environment file:
Copy the example environment file.
code Bash

cp .env.example .env

  

Note: If .env.example does not exist, create a new file named .env.

Configure your environment:
Open the .env file and fill in the required values. See the Configuration section below for details on where to get these values.
code Ini

# .env
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=your_strong_secret_here
NGROK_AUTHTOKEN=your_ngrok_authtoken_here

  

Run the application:
Use Docker Compose to build the images and start the services.
code Bash

   
        
    docker-compose up --build

      

    The first time you run this, it will download the base images and install all dependencies.

    Get your public URL:
    When the containers start, the ngrok service will connect and print its public URL in the logs. Look for a line like:
    t=... level=info msg="started tunnel" obj=tunnels name=command_line addr=http://jenkins-auditor:8000 url=https://<unique-string>.ngrok-free.app

    Your public webhook URL is https://<unique-string>.ngrok-free.app.

GitHub Webhook Configuration

    Navigate to your GitHub repository and go to Settings > Webhooks.

    Click Add webhook.

    Payload URL: Paste your public ngrok URL.

    Content type: Change this to application/json.

    Secret: Enter the same secret you used for GITHUB_WEBHOOK_SECRET in your .env file.

    Which events would you like to trigger this webhook? Select "Let me select individual events." and then check Pull requests.

    Click Add webhook.

Usage

Once the setup is complete, the auditor will work automatically. To trigger an audit:

    Create a new branch in your repository.

    Add or modify a file named Jenkinsfile.

    Commit the changes and open a Pull Request.

Within a minute, the webhook will trigger the service, and you should see a new comment appear on your pull request with the detailed audit report.
Configuration

The following environment variables must be set in the .env file:
Variable	Description
GITHUB_TOKEN	A GitHub Personal Access Token used to fetch files and post comments. Must have the repo scope. Create one here.
GITHUB_WEBHOOK_SECRET	A strong, random string you create. It's used to secure the communication between GitHub and your application.
NGROK_AUTHTOKEN	Your ngrok authtoken, required to run the ngrok service. You can find it on your ngrok dashboard.
License

This project is licensed under the MIT License.