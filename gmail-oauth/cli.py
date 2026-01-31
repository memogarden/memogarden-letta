"""Simple OAuth CLI for GMail (OOB flow)."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_oauth import GmailOAuthClient


def cmd_auth_url_oob(args):
    """Generate OAuth authorization URL (OOB flow)."""
    client = GmailOAuthClient(args.hacm)

    # Use OOB flow
    url = client.get_authorization_url(use_oob=True)

    print(f"\nVisit this URL to authorize the application:\n")
    print(f"  {url}\n")
    print(f"After authorizing, Google will display a code.")
    print(f"Copy that code and run:\n")
    print(f"  python -m gmail_oauth.cli exchange-oob <code> <your-email@gmail.com>\n")


def cmd_exchange_oob(args):
    """Exchange authorization code for tokens (OOB flow)."""
    client = GmailOAuthClient(args.hacm)

    try:
        # Exchange code for tokens
        tokens = client.exchange_code_for_tokens(
            args.code,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )

        # Store refresh token
        client.store_tokens(args.account, tokens)

        print(f"\n✓ OAuth successful!")
        print(f"  Account: {args.account}")
        print(f"  Refresh token stored in HACM")
        print(f"  Scopes: {', '.join(tokens.get('scope', '').split())}")

    except (ValueError, Exception) as e:
        print(f"\n✗ OAuth failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="GMail OAuth 2.0 CLI (OOB Flow)")
    parser.add_argument("--hacm", default="~/hacm-test/credentials.enc", help="HACM credential file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # auth-url-oob command
    auth_url_parser = subparsers.add_parser("auth-url-oob", help="Generate OAuth authorization URL (OOB)")
    auth_url_parser.set_defaults(func=cmd_auth_url_oob)

    # exchange-oob command
    exchange_parser = subparsers.add_parser("exchange-oob", help="Exchange authorization code (OOB)")
    exchange_parser.add_argument("code", help="Authorization code from Google")
    exchange_parser.add_argument("account", help="Your GMail address")
    exchange_parser.set_defaults(func=cmd_exchange_oob)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
