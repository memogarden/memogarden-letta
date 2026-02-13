#!/usr/bin/env python3
"""Markdown formatter for test runner output."""

import argparse
import sys


def format_markdown(title: str, body_lines: list[str]) -> str:
    """Generate markdown formatted output.

    Args:
        title: The title (will be an H3 heading)
        body_lines: List of body content lines

    Returns:
        Formatted markdown as a string
    """
    result = [f"### {title}", ""]
    for line in body_lines:
        # Format "Key: value" lines as bold keys
        if ": " in line:
            key, value = line.split(": ", 1)
            result.append(f"**{key}:** {value}")
        else:
            result.append(line)
    return "\n".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format text in markdown"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Title (H3 heading)"
    )
    parser.add_argument(
        "--body",
        nargs="+",
        required=True,
        help="Body content lines (one or more)"
    )

    args = parser.parse_args()

    output = format_markdown(args.title, args.body)
    print(output)


if __name__ == "__main__":
    main()
