import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header, Form
from typing import Optional
import requests
from dotenv import load_dotenv
from pathlib import Path
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
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
):
    raw_payload = await request.body()
    content_type = request.headers.get("content-type", "")

    if not verify_github_signature(GITHUB_WEBHOOK_SECRET, raw_payload, x_hub_signature_256 or ""):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        if "application/x-www-form-urlencoded" in content_type:
            # GitHub sends form payload as "payload=<json>"
            form = await request.form()
            data = json.loads(form["payload"])
           

        elif "application/json" in content_type:
            data = json.loads(raw_payload.decode())
          

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing payload: {e}")

  


   
    if x_github_event == "pull_request":
        action = data.get("action")
        
        
        if action in ["opened", "synchronize", "reopened"]:
            try:
                repo_name = data["repository"]["full_name"]
                pr_number = data["pull_request"]["number"]
                commit_sha = data["pull_request"]["head"]["sha"]
                
             
                
                
                jenkinsfile_content = fetch_jenkinsfile(repo_name, commit_sha)
                if jenkinsfile_content:
                   
                    target_dir = Path("jenkins_files_directory")
                    target_dir.mkdir(parents=True, exist_ok=True)  # create directory if it doesn't exist

                    # Define full target file path
                    target_file = target_dir / "Jenkinsfile"

                    # Save Jenkinsfile content
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(jenkinsfile_content)
                   
                    
                    
                    
                else:
                    print("⚠️  Jenkinsfile not found in this PR.")
                
            except KeyError as e:
                print(f"❌ Missing required field in webhook payload: {e}")
                raise HTTPException(status_code=400, detail=f"Missing field: {e}")
        else:
            print(f"ℹ️  PR action '{action}' - no processing needed")
    else:
        print(f"ℹ️  Event '{x_github_event}' - not a pull request event")
    
    return {"status": "processed", "event": x_github_event, "action": data.get("action")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)