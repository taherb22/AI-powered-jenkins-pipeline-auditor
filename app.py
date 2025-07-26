import os
import hmac
import hashlib
import json
from flask import Flask, request, abort
import requests
import base64
from datetime import datetime
app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")


def verify_github_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    """
    Verifies the GitHub HMAC signature.
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
    Fetches the Jenkinsfile content from GitHub.
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
        print(f"❌ Failed to fetch Jenkinsfile: {response.status_code} - {response.text}")
        return None


@app.route("/", methods=["GET", "POST"])
def github_webhook():
    print(f"👉 Received {request.method} request to /")

    if request.method == "GET":
        return "👋 Webhook is live!", 200

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

    print(f"📦 Event: {request.headers.get('X-GitHub-Event')}")
    print(f"📄 Payload: {json.dumps(data, indent=2)}")

    event = request.headers.get("X-GitHub-Event")

    # Step 3: Handle Pull Request event
    if event == "pull_request":
        action = data.get("action")
        if action in ["opened", "synchronize", "reopened"]:
            repo_name = data["repository"]["full_name"]
            commit_sha = data["pull_request"]["head"]["sha"]
            pr_number = data["pull_request"]["number"]

            jenkinsfile_content = fetch_jenkinsfile(repo_name, commit_sha)
            if jenkinsfile_content:
                print("✅ Jenkinsfile Content from PR:")
                print(jenkinsfile_content)
                push_log_to_repo(pr_number, jenkinsfile_content)
            else:
                print("🟡 Jenkinsfile not found in PR.")

    return "", 204



def push_log_to_repo(pr_number: int, log_content: str):
    logs_repo = os.environ.get("LOGS_REPO")
    token = os.environ.get("LOGS_PAT")
    if not logs_repo or not token:
        print("❌ Missing LOGS_REPO or LOGS_PAT in env vars.")
        return

    # e.g., logs/pr_42_2025-07-25T14:22.txt
    timestamp = datetime.utcnow().isoformat(timespec="seconds").replace(":", "-")
    filename = f"logs/pr_{pr_number}_{timestamp}.txt"

    url = f"https://api.github.com/repos/{logs_repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # GitHub expects base64-encoded content
    encoded_content = base64.b64encode(log_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Add audit log for PR #{pr_number}",
        "content": encoded_content,
        "branch": "main"  # adjust if using a different branch
    }

    resp = requests.put(url, headers=headers, json=payload)

    if resp.status_code in [200, 201]:
        print(f"✅ Log pushed to {filename}")
    else:
        print(f"❌ Failed to push log: {resp.status_code} - {resp.text}")


@app.errorhandler(404)
def not_found(e):
    print("❌ Flask received an unknown route")
    return "Not found", 404