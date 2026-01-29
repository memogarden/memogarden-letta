"""GMail OAuth 2.0 placeholder endpoints for MemoGarden Core API.

This module provides minimal Flask endpoints for OAuth flow integration.
"""

from flask import Blueprint, request, jsonify

from gmail_oauth import GmailOAuthClient

bp = Blueprint("gmail_oauth", __name__, url_prefix="/api/v1/oauth/gmail")


def get_client(hacm_path: str = "/var/lib/hacm/credentials.enc"):
    """Get OAuth client instance."""
    return GmailOAuthClient(hacm_path)


@bp.route("/auth-url", methods=["GET"])
def generate_auth_url():
    """Generate OAuth authorization URL.

    Query params:
        state: Optional state parameter
        redirect_uri: Optional override for redirect URI

    Returns:
        JSON: {"authorization_url": "...", "state": "..."}
    """
    hacm_path = request.args.get("hacm", "/var/lib/hacm/credentials.enc")
    redirect_uri = request.args.get("redirect_uri")

    client = GmailOAuthClient(hacm_path, redirect_uri=redirect_uri)
    state = request.args.get("state")

    url = client.get_authorization_url(state=state)

    # Extract state from URL for response
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    state_value = params.get("state", [""])[0]

    return jsonify({
        "authorization_url": url,
        "state": state_value,
        "redirect_uri": redirect_uri or "http://localhost:8080/callback",
    })


@bp.route("/callback", methods=["POST"])
def handle_callback():
    """Handle OAuth callback and store tokens.

    Request body:
        {
            "code": "authorization_code_from_callback",
            "state": "state_parameter",
            "account_id": "user@gmail.com"  // optional
        }

    Returns:
        JSON: {"success": true, "account_id": "..."}
    """
    data = request.get_json()
    hacm_path = request.args.get("hacm", "/var/lib/hacm/credentials.enc")

    code = data.get("code")
    state = data.get("state")
    account_id = data.get("account_id")

    if not code:
        return jsonify({"error": "Missing 'code' parameter"}), 400

    try:
        client = get_client(hacm_path)

        # Exchange code for tokens
        tokens = client.exchange_code_for_tokens(code, state)

        # Extract account ID from token info if not provided
        # (Google doesn't return email in token response, so this is required)
        if not account_id:
            return jsonify({
                "error": "Missing 'account_id' parameter",
                "hint": "Provide your GMail address (e.g., user@gmail.com)"
            }), 400

        # Store refresh token in HACM
        client.store_tokens(account_id, tokens)

        return jsonify({
            "success": True,
            "account_id": account_id,
            "scopes": tokens.get("scope", "").split(),
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal error: {e}"}), 500


@bp.route("/credentials/<account_id>", methods=["GET"])
def get_stored_credential(account_id: str):
    """Get stored OAuth credential info.

    Returns:
        JSON: {"account_id": "...", "metadata": {...}}
    """
    hacm_path = request.args.get("hacm", "/var/lib/hacm/credentials.enc")

    try:
        client = get_client(hacm_path)
        refresh_token = client.get_refresh_token(account_id)

        # Return minimal info (no secret material)
        return jsonify({
            "account_id": account_id,
            "has_token": True,
            "provider": "google",
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Internal error: {e}"}), 500


@bp.route("/credentials", methods=["GET"])
def list_credentials():
    """List all stored OAuth credentials.

    Returns:
        JSON: {"credentials": [{"account_id": "...", "provider": "google"}, ...]}
    """
    hacm_path = request.args.get("hacm", "/var/lib/hacm/credentials.enc")

    try:
        from hacm import CredentialStore

        store = CredentialStore(hacm_path)
        creds = store.list()

        oauth_creds = [
            {
                "account_id": cred.account_id,
                "provider": cred.provider,
                "type": cred.type,
            }
            for cred_id, cred in creds
            if cred.provider == "google" and cred.type == "oauth_refresh"
        ]

        return jsonify({"credentials": oauth_creds})

    except ImportError:
        return jsonify({"error": "HACM not installed"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal error: {e}"}), 500
