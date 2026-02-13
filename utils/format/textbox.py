#!/usr/bin/env python3
"""Textbox formatter for consistent bordered output in test runners."""

import argparse
import sys
import unicodedata


def display_width(s: str) -> int:
    """Get display width of string, accounting for multi-byte characters."""
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1
               for c in s)


def format_box(title: str, body_lines: list[str], min_width: int = 60) -> str:
    """Generate a bordered box with dynamic width.

    Args:
        title: The title line for the box header
        body_lines: List of body content lines
        min_width: Minimum box width (default 60)

    Returns:
        Formatted box as a string
    """
    all_lines = [title] + body_lines
    content_width = max((display_width(line) for line in all_lines), default=0)
    width = max(min_width, content_width + 4)  # +4 for side padding

    # Helper to pad a line
    def pad(line: str) -> str:
        needed = width - display_width(line) - 2  # -2 for border chars
        return f"║ {line}{' ' * needed} ║"

    # Build box
    border = "╔" + "═" * (width - 2) + "╗"
    divider = "╠" + "═" * (width - 2) + "╣"
    bottom = "╚" + "═" * (width - 2) + "╝"

    result = [border, pad(title), divider]
    result.extend(pad(line) for line in body_lines)
    result.append(bottom)
    return "\n".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format text in a bordered box"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Box title (header section)"
    )
    parser.add_argument(
        "--body",
        nargs="+",
        required=True,
        help="Body content lines (one or more)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=60,
        help="Minimum box width (default: 60)"
    )

    args = parser.parse_args()

    output = format_box(args.title, args.body, args.width)
    print(output)


if __name__ == "__main__":
    main()
