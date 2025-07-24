import os
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode()

@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Verify GitHub signature
    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        abort(400, "Missing signature")

    sha_name, received_signature = signature.split("=")
    if sha_name != "sha256":
        abort(400, "Only sha256 is supported")

    # 2. Compute HMAC
    mac = hmac.new(WEBHOOK_SECRET, msg=request.data, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    if not hmac.compare_digest(received_signature, expected_signature):
        abort(403, "Invalid signature")

    # 3. Parse and log payload
    payload = request.json
    print("Received GitHub event:", payload.get("action", "N/A"))

    # (Optional: trigger scripts, jobs, etc.)
    
    return "", 200