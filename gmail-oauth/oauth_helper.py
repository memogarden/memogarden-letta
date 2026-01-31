#!/usr/bin/env python
"""GMail OAuth helper script (standalone)."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for hacm
sys.path.insert(0, "/home/kureshii/memogarden/hacm")

# Add current directory for gmail_oauth module
sys.path.insert(0, str(Path(__file__).parent))

from gmail_oauth import GmailOAuthClient


def main():
    parser = argparse.ArgumentParser(description="GMail OAuth 2.0 CLI (OOB Flow)")
    parser.add_argument("--hacm", default="~/hacm-test/credentials.enc", help="HACM credential file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # auth-url-oob command
    auth_url_parser = subparsers.add_parser("auth-url-oob", help="Generate OAuth authorization URL (OOB)")
    auth_url_parser.set_defaults(func=lambda args: auth_url_oob(args, parser))

    # exchange-oob command
    exchange_parser = subparsers.add_parser("exchange-oob", help="Exchange authorization code (OOB)")
    exchange_parser.add_argument("code", help="Authorization code from Google")
    exchange_parser.add_argument("account", help="Your GMail address")
    exchange_parser.set_defaults(func=lambda args: exchange_oob(args, parser))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


def auth_url_oob(args, parser):
    """Generate OAuth authorization URL (OOB flow)."""
    client = GmailOAuthClient(args.hacm)

    # Use OOB flow
    url = client.get_authorization_url(use_oob=True)

    print(f"\nVisit this URL to authorize the application:\n")
    print(f"  {url}\n")
    print(f"After authorizing, Google will display a code.")
    print(f"Copy that code and run:\n")
    print(f"  python gmail-oauth/oauth_helper.py exchange-oob <code> <your-email@gmail.com>\n")


def exchange_oob(args, parser):
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


if __name__ == "__main__":
    main()
