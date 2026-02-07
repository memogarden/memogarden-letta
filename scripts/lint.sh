#!/bin/bash
# Run linters and formatters on MemoGarden codebase

set -e

echo "=========================================="
echo "MemoGarden Lint Check"
echo "=========================================="

# Determine which package to lint (default: api)
PACKAGE="${1:-api}"

case "$PACKAGE" in
    api)
        cd /home/kureshii/memogarden/memogarden-api
        ;;
    system)
        cd /home/kureshii/memogarden/memogarden-system
        ;;
    *)
        echo "Usage: $0 [api|system]"
        exit 1
        ;;
esac

echo ""
echo "Linting $PACKAGE..."
echo ""

# Check if we're in a Poetry project
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Not a Poetry project."
    exit 1
fi

# Run ruff to check for issues
echo "→ Running ruff check..."
poetry run ruff check .

echo ""
echo "=========================================="
echo "Lint complete!"
echo "=========================================="
echo ""
echo "To auto-fix issues, run: poetry run ruff check --fix ."
