import os
import hmac
import hashlib
import json
from flask import Flask, request, abort
import requests

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")


def verify_github_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    """
    Verifies the GitHub HMAC signature.

    Args:
        secret (str): Webhook secret configured in GitHub
        payload (bytes): Raw request body
        signature_header (str): X-Hub-Signature-256 header value

    Returns:
        bool: True if signature is valid
    """
    if not signature_header:
        return False

    try:
        algo, received_sig = signature_header.split('=')
    except ValueError:
        return False

    if algo != 'sha256':
        return False

    computed_mac = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_mac, received_sig)


def fetch_jenkinsfile(repo_full_name: str, commit_sha: str) -> str | None:
    """
    Fetches the Jenkinsfile content from GitHub via the API.

    Args:
        repo_full_name (str): e.g., 'user/repo'
        commit_sha (str): Commit SHA to target the correct version

    Returns:
        str or None: Jenkinsfile content if successful
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }

    url = f"https://api.github.com/repos/{repo_full_name}/contents/Jenkinsfile?ref={commit_sha}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        print(f"❌ Failed to fetch Jenkinsfile: {response.status_code}")
        return None


@app.route("/webhook", methods=["POST"])
def github_webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload = request.get_data()

    # Step 1: Verify signature
    if not verify_github_signature(GITHUB_WEBHOOK_SECRET, payload, signature):
        print("⚠️ Invalid GitHub signature.")
        abort(403)

    # Step 2: Parse JSON payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON.")
        abort(400)

    event = request.headers.get("X-GitHub-Event")

    # Step 3: Handle Pull Request event
    if event == "pull_request":
        action = data.get("action")
        if action in ["opened", "synchronize", "reopened"]: 
            repo_name = data["repository"]["full_name"]             
            commit_sha = data["pull_request"]["head"]["sha"]        

            jenkinsfile_content = fetch_jenkinsfile(repo_name, commit_sha)
            if jenkinsfile_content:
                print("✅ Jenkinsfile Content from PR:")
                print(jenkinsfile_content)
            else:
                print("🟡 Jenkinsfile not found in PR.")

    return "", 204
