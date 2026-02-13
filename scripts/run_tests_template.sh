#!/bin/bash
# MemoGarden Test Runner - Standardized Template
#
# This is a template for creating standardized test entrypoints.
# Copy to <project>/run_tests.sh and update PROJECT_NAME, MODULE_NAME,
# and DEPENDENCY_CHECK values.
#
# Usage: ./run_tests.sh [pytest_args...]
#
# Examples:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh -xvs         # Verbose, stop on first failure
#   ./run_tests.sh tests/test_foo.py::test_bar
#   ./run_tests.sh --cov=module --cov-report=term-missing

set -e

# ============================================================================
# CONFIGURATION - Update these values for each project
# ============================================================================

# Project name (for display only)
PROJECT_NAME="{{PROJECT_NAME}}"

# Python module name for coverage (e.g., "api", "system", "mg_client")
MODULE_NAME="{{MODULE_NAME}}"

# Dependency check: Python import to verify (empty = no check)
# Examples: "from system.utils import isodatetime" or "" for no check
DEPENDENCY_CHECK="{{DEPENDENCY_CHECK}}"

# Optional: Test environment variables (set before running tests)
# Format: KEY1="value1"
#         KEY2="value2"
# Leave empty to use defaults from conftest.py
# {{ENV_VARS}}

# ============================================================================
# SCRIPT START - No changes needed below this line
# ============================================================================

# Script directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Generate test run ID (YYYYMMDD-HHMMSS)
TEST_RUN_ID="$(date +%Y%m%d-%H%M%S)"

# Header output (6 lines for consistent parsing)
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  MemoGarden Test Runner                                     ║"
echo "║  Project: $PROJECT_NAME                                    ║"
echo "║  Test Run ID: $TEST_RUN_ID                                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Change to script directory to ensure correct working directory
cd "$SCRIPT_DIR"

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "ERROR: poetry not found. Please install poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Optional: Install dependencies if not present
# Check if DEPENDENCY_CHECK is non-empty and not a template placeholder
if [ -n "$DEPENDENCY_CHECK" ] && [ "$DEPENDENCY_CHECK" != "{{DEPENDENCY_CHECK}}" ]; then
    if ! poetry run python -c "$DEPENDENCY_CHECK" 2>/dev/null; then
        echo "WARNING: Poetry dependencies not installed."
        echo "Running 'poetry install'..."
        poetry install --quiet

        # Verify again after install
        if ! poetry run python -c "$DEPENDENCY_CHECK" 2>/dev/null; then
            echo "ERROR: Dependency check failed even after install."
            echo "Check: $DEPENDENCY_CHECK"
            exit 1
        fi
        echo "Dependencies installed successfully."
        echo ""
    fi
fi

# Set test environment variables (if configured)
# {{ENV_VARS_SETUP}}

# Run tests with poetry, capturing output for parsing
set +e  # Don't exit on test failure

# Capture pytest output to a temp file for parsing
TEMP_OUTPUT=$(mktemp)
poetry run pytest "$@" 2>&1 | tee "$TEMP_OUTPUT"
PYTEST_EXIT_CODE=${PIPESTATUS[0]}

set -e

echo ""

# Parse test results from captured output
# Pytest summary format: "==== X passed in Y.YYs ====" or "==== X passed, Y failed in Y.YYs ===="
SUMMARY_RAW=$(grep "passed" "$TEMP_OUTPUT" 2>/dev/null | tail -1 || echo "")
SUMMARY_LINE=$(echo "$SUMMARY_RAW" | sed 's/=//g' | xargs)

if [ -z "$SUMMARY_LINE" ]; then
    # Check for no tests
    if grep -q "no tests" "$TEMP_OUTPUT" 2>/dev/null; then
        STATUS="NO TESTS"
        TESTS_SUMMARY="0 passed, 0 failed, 0 skipped"
        DURATION="0.00s"
    # Check for errors
    elif grep -q "ERROR" "$TEMP_OUTPUT" 2>/dev/null || grep -q "error" "$TEMP_OUTPUT" 2>/dev/null; then
        STATUS="ERROR"
        TESTS_SUMMARY="error during collection or execution"
        DURATION="0.00s"
    else
        # Fallback: use exit code
        if [ $PYTEST_EXIT_CODE -eq 0 ]; then
            STATUS="PASSED"
        else
            STATUS="FAILED"
        fi
        TESTS_SUMMARY="unknown (check output above)"
        DURATION="unknown"
    fi
else
    # Parse the summary line
    # Extract status
    if echo "$SUMMARY_LINE" | grep -qE "(failed|error)"; then
        STATUS="FAILED"
    else
        STATUS="PASSED"
    fi

    # Extract test counts (everything before "in X.XXs")
    TESTS_SUMMARY=$(echo "$SUMMARY_LINE" | sed -E 's/ in [0-9]+\.[0-9]+s.*$//' | sed -E 's/=$//')

    # Extract duration (the "in X.XXs" part)
    DURATION=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+\.[0-9]+s' | head -1 || echo "unknown")
fi

# Clean up temp file
rm -f "$TEMP_OUTPUT"

# Footer output (7 lines total, last 6 lines are summary content for tail -n 6)
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Test Summary                                               ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Status: $STATUS                                            ║"
echo "║  Tests: $TESTS_SUMMARY                                      ║"
echo "║  Duration: $DURATION                                        ║"
echo "║  Test Run ID: $TEST_RUN_ID                                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"

# Exit with pytest's exit code
exit $PYTEST_EXIT_CODE
