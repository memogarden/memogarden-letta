#!/usr/bin/env python3
"""Plaintext formatter for test runner output."""

import argparse
import sys


def format_plaintext(title: str, body_lines: list[str]) -> str:
    """Generate plain text output with title and body.

    Args:
        title: The title line
        body_lines: List of body content lines

    Returns:
        Formatted text as a string
    """
    result = [title, ""]
    result.extend(body_lines)
    return "\n".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format text in plain text (no borders)"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Title line"
    )
    parser.add_argument(
        "--body",
        nargs="+",
        required=True,
        help="Body content lines (one or more)"
    )

    args = parser.parse_args()

    output = format_plaintext(args.title, args.body)
    print(output)


if __name__ == "__main__":
    main()
