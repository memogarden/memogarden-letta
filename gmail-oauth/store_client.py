"""Store Google OAuth client credentials in HACM."""

import base64
import json
import sys
from datetime import datetime

# Add hacm to path if running locally
sys.path.insert(0, "/home/kureshii/memogarden/hacm")

try:
    from hacm import CredentialStore, Credential
except ImportError as e:
    print(f"Error: HACM not found at expected path.")
    print("Please ensure HACM is installed:")
    print("  cd /home/kureshii/memogarden/hacm")
    print("  poetry install")
    print("Or add to PYTHONPATH: export PYTHONPATH=/home/kureshii/memogarden/hacm:$PYTHONPATH")
    sys.exit(1)

# Your Google OAuth client credentials
CLIENT_ID = "31802475223-pnu2ue77uojeucmficsb6h35kqb7j708.apps.googleusercontent.com"
CLIENT_SECRET = "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"

# HACM credential file path
HACM_PATH = "/var/lib/hacm/credentials.enc"

# Create HACM store
store = CredentialStore(HACM_PATH)

# Package client credentials as JSON, then base64 encode
client_creds = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

material = base64.b64encode(
    json.dumps(client_creds).encode()
).decode()

# Create credential
cred = Credential(
    id="google:oauth-client",
    provider="google",
    account_id="gmail-scraper-app",
    type="oauth_client",
    material=material,
    metadata={
        "redirect_uris": ["http://localhost:8080/callback"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    },
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

# Store in HACM
store.put("google:oauth-client", cred)

print("✓ OAuth client credentials stored in HACM")
print(f"  HACM path: {HACM_PATH}")
print(f"  Credential ID: google:oauth-client")
print(f"  Client ID: {CLIENT_ID}")
