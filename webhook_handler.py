import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")

if not GITHUB_TOKEN:
    raise ValueError("Environment variable GITHUB_TOKEN is not set")
if not GITHUB_WEBHOOK_SECRET:
    raise ValueError("Environment variable GITHUB_WEBHOOK_SECRET is not set")

app = FastAPI(title="GitHub Webhook Handler", version="1.0.0")

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
        print(f"Failed to fetch Jenkinsfile: {response.status_code} - {response.text}")
        return None

@app.get("/")
async def health_check():
    """Health check endpoint"""
    print("👉 Received GET request to /")
    return {"message": "Webhook is live!"}

@app.post("/")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event")
):
    """
    Handle GitHub webhook events
    """
    payload = await request.body()
    
    if not verify_github_signature(GITHUB_WEBHOOK_SECRET, payload, x_hub_signature_256 or ""):
        print("Invalid GitHub signature.")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("Failed to decode JSON.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    if x_github_event == "pull_request":
        action = data.get("action")
        if action in ["opened", "synchronize", "reopened"]:
            repo_name = data["repository"]["full_name"]
            commit_sha = data["pull_request"]["head"]["sha"]
            
            jenkinsfile_content = fetch_jenkinsfile(repo_name, commit_sha)
            
            if jenkinsfile_content:
                print("Jenkinsfile Content from PR:")
                print(jenkinsfile_content)
            else:
                print("Jenkinsfile not found in PR.")
    
    return {"status": "processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)