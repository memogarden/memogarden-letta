#!/usr/bin/env python
"""GMail OAuth helper - generate authorization URL."""

import base64
import json
import os
from datetime import datetime
from urllib.parse import urlencode
import secrets

# Configuration
HACM_PATH = os.path.expanduser("~/hacm-test/credentials.enc")
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_client_credentials():
    """Load client credentials from HACM."""
    # Read and decrypt HACM file
    import sys
    sys.path.insert(0, "/home/kureshii/memogarden/hacm")
    from hacm import CredentialStore

    store = CredentialStore(HACM_PATH)
    client_cred = store.get("google:oauth-client")

    if not client_cred:
        print("Error: OAuth client credentials not found in HACM.")
        print("Please run the setup script first.")
        sys.exit(1)

    # Decode client credentials
    creds_data = json.loads(base64.b64decode(client_cred.material).decode("utf-8"))
    return creds_data["client_id"]


def main():
    client_id = get_client_credentials()

    # Generate state
    state = secrets.token_urlsafe(16)

    # Build OAuth URL with OOB flow
    params = {
        "client_id": client_id,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",  # OOB flow
        "scope": " ".join(GOOGLE_SCOPES),
        "response_type": "code",
        "access_type": "offline",  # For refresh token
        "prompt": "consent",  # Force consent screen
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URI}?{urlencode(params)}"

    print("=" * 70)
    print("GMail OAuth Authorization (OOB Flow)")
    print("=" * 70)
    print()
    print("1. Visit this URL:")
    print()
    print(f"   {auth_url}")
    print()
    print("2. Sign in and grant permissions")
    print()
    print("3. Google will display an authorization code (4/0AX4Xf...)")
    print()
    print("4. Copy the code and run:")
    print()
    print(f"   python oauth-exchange.py <code> <your-email@gmail.com>")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
