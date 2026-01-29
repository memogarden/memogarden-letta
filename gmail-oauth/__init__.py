"""GMail OAuth 2.0 Flow Handler.

Minimal OAuth flow implementation for obtaining GMail refresh tokens.
Stores credentials in HACM for secure persistence.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from typing import Literal

# Configuration
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
    "https://www.googleapis.com/auth/gmail.modify",  # Modify labels (optional)
]


class GmailOAuthClient:
    """Minimal GMail OAuth 2.0 client for headless systems."""

    def __init__(
        self,
        hacm_path: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str = "http://localhost:8080/callback",
    ):
        """Initialize OAuth client.

        Args:
            hacm_path: Path to HACM credential store
            client_id: OAuth client ID (or load from HACM)
            client_secret: OAuth client secret (or load from HACM)
            redirect_uri: OAuth redirect URI
        """
        self.hacm_path = hacm_path
        self.redirect_uri = redirect_uri
        self._client_id = client_id
        self._client_secret = client_secret

    def get_client_credentials(self) -> tuple[str, str]:
        """Get OAuth client credentials (from HACM or constructor)."""
        if self._client_id and self._client_secret:
            return self._client_id, self._client_secret

        # Load from HACM
        try:
            from hacm import CredentialStore

            store = CredentialStore(self.hacm_path)
            client_cred = store.get("google:oauth-client")
            if not client_cred:
                raise ValueError(
                    "OAuth client credentials not found in HACM. "
                    "Add them using `hacm-credentials add-client` or via API."
                )

            # Decode client credentials
            import base64
            creds_data = json.loads(base64.b64decode(client_cred.material).decode("utf-8"))
            return creds_data["client_id"], creds_data["client_secret"]

        except ImportError:
            raise ImportError("HACM not installed: pip install memogarden-hacm")

    def get_authorization_url(
        self,
        state: str | None = None,
        access_type: Literal["online", "offline"] = "offline",
        prompt: Literal["consent", "select_account"] = "consent",
        use_oob: bool = False,
    ) -> str:
        """Generate GMail OAuth authorization URL.

        Args:
            state: Optional CSRF token (generated if not provided)
            access_type: "offline" for refresh token (required)
            prompt: "consent" to force approval screen
            use_oob: Use out-of-band flow (oob) for headless/CLI usage

        Returns:
            Authorization URL for user to visit
        """
        client_id, _ = self.get_client_credentials()

        if state is None:
            state = self._generate_state()

        # Choose redirect URI based on flow type
        if use_oob:
            redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # OOB flow for headless
        else:
            redirect_uri = self.redirect_uri  # Callback flow

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(GOOGLE_SCOPES),
            "response_type": "code",
            "access_type": access_type,
            "prompt": prompt,
            "state": state,
        }

        url = f"{GOOGLE_AUTH_URI}?{urlencode(params)}"
        return url

    def exchange_code_for_tokens(self, code: str, redirect_uri: str | None = None, state: str | None = None) -> dict:
        """Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback/oob
            redirect_uri: Redirect URI used in authorization (defaults to self.redirect_uri)
            state: State parameter for validation (if generated)

        Returns:
            Token response dict with keys: access_token, refresh_token, expires_in, scope, token_type

        Raises:
            ValueError: If code exchange fails
        """
        client_id, client_secret = self.get_client_credentials()

        # Use provided redirect_uri or default
        if redirect_uri is None:
            redirect_uri = self.redirect_uri

        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(GOOGLE_TOKEN_URI, data=data)
        response.raise_for_status()

        tokens = response.json()

        if "error" in tokens:
            raise ValueError(f"Token exchange failed: {tokens.get('error')}: {tokens.get('error_description')}")

        if "refresh_token" not in tokens:
            raise ValueError("No refresh token in response. Did you set access_type=offline?")

        return tokens

    def store_tokens(self, account_id: str, tokens: dict) -> None:
        """Store OAuth refresh token in HACM.

        Args:
            account_id: GMail account identifier (e.g., "user@gmail.com")
            tokens: Token response from exchange_code_for_tokens
        """
        try:
            from hacm import Credential, CredentialStore
            from datetime import datetime

            store = CredentialStore(self.hacm_path)

            # Create credential
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

        except ImportError:
            raise ImportError("HACM not installed: pip install memogarden-hacm")

    def get_refresh_token(self, account_id: str) -> str:
        """Retrieve stored refresh token for account.

        Args:
            account_id: GMail account identifier

        Returns:
            Refresh token

        Raises:
            ValueError: If token not found in HACM
        """
        try:
            from hacm import CredentialStore

            store = CredentialStore(self.hacm_path)
            cred = store.get(f"google:{account_id}")

            if not cred:
                raise ValueError(f"No refresh token found for {account_id}")

            return cred.material

        except ImportError:
            raise ImportError("HACM not installed: pip install memogarden-hacm")

    def refresh_access_token(self, account_id: str) -> dict:
        """Refresh access token using stored refresh token.

        Args:
            account_id: GMail account identifier

        Returns:
            New token response dict

        Raises:
            ValueError: If refresh fails
        """
        refresh_token = self.get_refresh_token(account_id)
        client_id, client_secret = self.get_client_credentials()

        data = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }

        response = requests.post(GOOGLE_TOKEN_URI, data=data)
        response.raise_for_status()

        tokens = response.json()

        if "error" in tokens:
            raise ValueError(f"Token refresh failed: {tokens.get('error')}: {tokens.get('error_description')}")

        # Note: We don't update the refresh token in HACM because Google returns
        # the same refresh token for subsequent calls. If a new refresh token
        # is returned, we would update it here.

        return tokens

    @staticmethod
    def _generate_state() -> str:
        """Generate random state parameter for CSRF protection."""
        import secrets
        return secrets.token_urlsafe(16)


class SimpleCallbackServer:
    """Minimal HTTP server for OAuth callback on headless systems.

    For production, consider using a proper web framework.
    """

    def __init__(self, port: int = 8080):
        """Initialize callback server.

        Args:
            port: Port to listen on
        """
        self.port = port
        self._code: str | None = None
        self._state: str | None = None
        self._error: str | None = None

    def wait_for_callback(self, timeout: int = 300) -> dict:
        """Start server and wait for OAuth callback.

        Args:
            timeout: Seconds to wait before giving up

        Returns:
            Callback params dict with keys: code, state (or error)

        Raises:
            TimeoutError: If no callback within timeout
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import socket
        import threading
        import time

        class CallbackHandler(BaseHTTPRequestHandler):
            """Handle OAuth callback."""

            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def do_GET(self):
                """Handle GET request for OAuth callback."""
                # Parse query string
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                if "code" in params:
                    self.outer._code = params["code"][0]
                    if "state" in params:
                        self.outer._state = params["state"][0]

                    # Send success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Authorization successful!</h1>"
                        b"<p>You can close this window.</p></body></html>"
                    )
                elif "error" in params:
                    self.outer._error = params["error"][0]
                    if "error_description" in params:
                        self.outer._error += f": {params['error_description'][0]}"

                    # Send error response
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h1>Authorization failed</h1>"
                        b"<p>Error: " + self.outer._error.encode() + b"</p></body></html>"
                    )
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Invalid request</h1></body></html>")

                # Shutdown server after processing request
                threading.Thread(target=self.server.shutdown, daemon=True).start()

        # Start server
        server = HTTPServer(("localhost", self.port), CallbackHandler(self))
        server.timeout = timeout

        print(f"Listening for OAuth callback on http://localhost:{self.port}")
        print("Waiting for authorization...")

        server.handle_request()

        if self._code:
            return {"code": self._code, "state": self._state}
        elif self._error:
            raise ValueError(f"OAuth error: {self._error}")
        else:
            raise TimeoutError(f"No callback within {timeout}s")
