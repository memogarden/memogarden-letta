"""CLI tool for GMail OAuth flow."""

import argparse
import sys

from gmail_oauth import GmailOAuthClient, SimpleCallbackServer


def cmd_auth_url(args):
    """Generate and display OAuth authorization URL."""
    client = GmailOAuthClient(args.hacm)

    url = client.get_authorization_url()
    print(f"\nVisit this URL to authorize the application:\n")
    print(f"  {url}\n")

    # Display state for verification
    parsed = dict(x.split("=") for x in url.split("?")[1].split("&"))
    print(f"State token (for verification): {parsed.get('state', 'N/A')}\n")


def cmd_callback(args):
    """Run OAuth callback server and store tokens."""
    client = GmailOAuthClient(args.hacm)

    # Start callback server
    server = SimpleCallbackServer(args.port)

    try:
        # Wait for callback
        callback_data = server.wait_for_callback(timeout=args.timeout)

        # Exchange code for tokens
        tokens = client.exchange_code_for_tokens(
            callback_data["code"], callback_data.get("state")
        )

        # Store refresh token
        account_id = args.account or extract_email_from_token(tokens)
        client.store_tokens(account_id, tokens)

        print(f"\nOAuth successful!")
        print(f"Account: {account_id}")
        print(f"Refresh token stored in HACM")
        print(f"Scopes: {', '.join(tokens.get('scope', '').split())}")

    except (ValueError, TimeoutError) as e:
        print(f"\nOAuth failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_refresh(args):
    """Refresh access token (test)."""
    client = GmailOAuthClient(args.hacm)

    try:
        tokens = client.refresh_access_token(args.account)
        print(f"\nToken refresh successful!")
        print(f"Access token: {tokens['access_token'][:20]}...")
        print(f"Expires in: {tokens.get('expires_in')} seconds")
    except ValueError as e:
        print(f"\nRefresh failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List stored OAuth credentials."""
    try:
        from hacm import CredentialStore

        store = CredentialStore(args.hacm)
        creds = store.list()

        if not creds:
            print("\nNo OAuth credentials stored.")
            return

        print("\nStored OAuth credentials:")
        for cred_id, cred in creds:
            if cred.type == "oauth_client":
                print(f"  [client] {cred_id}")
            elif cred.type == "oauth_refresh":
                print(f"  [token]  {cred.account_id}")

    except ImportError:
        print("\nHACM not installed: pip install memogarden-hacm", file=sys.stderr)
        sys.exit(1)


def extract_email_from_token(tokens: dict) -> str:
    """Extract email from token response (fallback)."""
    # Google doesn't return email in token response
    # User would need to provide account_id
    return "unknown@gmail.com"


def main():
    parser = argparse.ArgumentParser(description="GMail OAuth 2.0 CLI")
    parser.add_argument("--hacm", default="/var/lib/hacm/credentials.enc", help="HACM credential file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # auth-url command
    auth_url_parser = subparsers.add_parser("auth-url", help="Generate OAuth authorization URL")
    auth_url_parser.set_defaults(func=cmd_auth_url)

    # callback command
    callback_parser = subparsers.add_parser("callback", help="Run OAuth callback server")
    callback_parser.add_argument("--port", type=int, default=8080, help="Callback server port")
    callback_parser.add_argument("--account", help="GMail account ID (e.g., user@gmail.com)")
    callback_parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    callback_parser.set_defaults(func=cmd_callback)

    # refresh command (test)
    refresh_parser = subparsers.add_parser("refresh", help="Refresh access token")
    refresh_parser.add_argument("account", help="GMail account ID")
    refresh_parser.set_defaults(func=cmd_refresh)

    # list command
    list_parser = subparsers.add_parser("list", help="List stored credentials")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
