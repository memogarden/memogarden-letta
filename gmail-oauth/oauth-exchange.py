#!/usr/bin/env python
"""GMail OAuth helper - exchange authorization code for refresh token."""

import base64
import json
import os
import sys
from datetime import datetime

# Configuration
HACM_PATH = os.path.expanduser("~/hacm-test/credentials.enc")
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_client_credentials():
    """Load client credentials from HACM."""
    sys.path.insert(0, "/home/kureshii/memogarden/hacm")
    from hacm import CredentialStore

    store = CredentialStore(HACM_PATH)
    client_cred = store.get("google:oauth-client")

    creds_data = json.loads(base64.b64decode(client_cred.material).decode("utf-8"))
    return creds_data["client_id"], creds_data["client_secret"]


def get_stored_credentials(account_id):
    """Load refresh token from HACM."""
    sys.path.insert(0, "/home/kureshii/memogarden/hacm")
    from hacm import CredentialStore

    store = CredentialStore(HACM_PATH)
    cred = store.get(f"google:{account_id}")

    if not cred:
        print(f"Error: No refresh token found for {account_id}")
        sys.exit(1)

    return cred.material


def store_refresh_token(account_id, tokens):
    """Store refresh token in HACM."""
    sys.path.insert(0, "/home/kureshii/memogarden/hacm")
    from hacm import Credential, CredentialStore

    store = CredentialStore(HACM_PATH)

    cred = Credential(
        id=f"google:{account_id}",
        provider="google",
        account_id=account_id,
        type="oauth_refresh",
        material=tokens["refresh_token"],
        metadata={
            "scopes": tokens.get("scope", "").split(),
            "token_endpoint": GOOGLE_TOKEN_URI,
            "access_expires_in": tokens.get("expires_in"),
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    store.put(f"google:{account_id}", cred)


def main():
    if len(sys.argv) != 3:
        print("Usage: python oauth-exchange.py <authorization-code> <your-email@gmail.com>")
        print()
        print("Example:")
        print("  python oauth-exchange.py 4/0AX4Xf... user@gmail.com")
        sys.exit(1)

    code = sys.argv[1]
    account_id = sys.argv[2]

    client_id, client_secret = get_client_credentials()

    # Exchange code for tokens
    print(f"Exchanging authorization code for tokens...")

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "authorization_code",
    }

    import requests
    response = requests.post(GOOGLE_TOKEN_URI, data=data)
    response.raise_for_status()

    tokens = response.json()

    if "error" in tokens:
        print(f"Error: {tokens.get('error')}: {tokens.get('error_description')}")
        sys.exit(1)

    if "refresh_token" not in tokens:
        print("Error: No refresh token in response.")
        print("Did you set access_type=offline?")
        sys.exit(1)

    # Store refresh token
    store_refresh_token(account_id, tokens)

    print()
    print("✓ OAuth successful!")
    print(f"  Account: {account_id}")
    print(f"  Refresh token stored in HACM")
    print(f"  Scopes: {', '.join(tokens.get('scope', '').split())}")


if __name__ == "__main__":
    main()
