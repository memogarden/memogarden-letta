#!/bin/bash
# MemoGarden Test Runner - Standardized Entrypoint
#
# This is the generic test entrypoint for all MemoGarden projects.
# Project-specific run_tests.sh scripts configure this via environment variables.
#
# WARNING TO AGENTS: If you need functionality not supported by this entrypoint,
# DO NOT work around it with ad-hoc bash commands. Instead:
# 1. Alert a human that the test entrypoint needs improvement
# 2. Explain what functionality is needed
# 3. Wait for the entrypoint to be enhanced centrally
#
# This ensures consistency across all projects and makes maintenance easier.
#
# Configured via environment variables (set by calling run_tests.sh):
#   PROJECT_NAME      - Display name for the project
#   MODULE_NAME       - Python module name (for coverage)
#   DEPENDENCY_CHECK - Python import to verify dependencies (empty = no check)
#   TEST_RUN_ID      - Generated test run ID (YYYYMMDD-HHMMSS)
#   TEST_FORMAT      - Output format: textbox, plaintext, markdown (default: textbox)
#   WIDTH            - Box width for textbox format (default: 60)
#
# Usage: Source this script after setting environment variables
#   PROJECT_NAME="memogarden-api"
#   MODULE_NAME="api"
#   DEPENDENCY_CHECK="from system.utils import isodatetime"
#   export TEST_FORMAT="${TEST_FORMAT:-textbox}"
#   . /workspaces/memogarden/scripts/test_entrypoint.sh

set -e

# ============================================================================
# VALIDATION
# ============================================================================

# Required environment variables
if [ -z "$PROJECT_NAME" ]; then
    echo "ERROR: PROJECT_NAME environment variable not set" >&2
    echo "This script should be called from run_tests.sh" >&2
    exit 1
fi

# Default values
: "${TEST_RUN_ID:=$(date +%Y%m%d-%H%M%S)}"
: "${TEST_FORMAT:=textbox}"
: "${WIDTH:=60}"

# Export for child processes
export TEST_FORMAT
export WIDTH

# ============================================================================
# PARSE SCRIPT OPTIONS
# ============================================================================

# Show help if requested
_show_help() {
    cat << EOF
MemoGarden Test Runner - $PROJECT_NAME

Standardized test entrypoint for $PROJECT_NAME.

USAGE:
    ./run_tests.sh [options] [pytest_args...]

OPTIONS:
    -h, --help              Show this help message
    --format=FORMAT         Output format for headers/summaries:
                            - textbox (default): Bordered box with Unicode characters
                            - plaintext: Plain text without borders
                            - markdown, md: Markdown formatted output

PYTEST OPTIONS:
    All other arguments are passed directly to pytest.
    Common options:
        -x              Stop on first failure
        -v              Verbose output
        -s              Show print output
        --cov=MODULE    Coverage report
        --tb=short      Shorter traceback format
        -k EXPRESSION   Only run tests matching expression

EXAMPLES:
    ./run_tests.sh                    # Run all tests
    ./run_tests.sh --format=md        # Markdown output
    ./run_tests.sh -xvs               # Verbose, stop on first failure
    ./run_tests.sh tests/test_api.py  # Run specific test file

ENVIRONMENT:
    TEST_FORMAT           Override default format (textbox/plaintext/markdown)
    WIDTH                 Override default box width (default: 60)

For more pytest options, see: poetry run pytest --help

---
This is the MemoGarden standardized test entrypoint. If you need functionality
not supported here, please alert a human to improve this script rather than
working around it with custom bash commands.
EOF
}

# Parse options (consume script options, pass rest to pytest)
PYTEST_ARGS=()

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            _show_help
            exit 0
            ;;
        --format=*)
            TEST_FORMAT="${arg#*=}"
            ;;
        --format)
            # Handled in caller - this is for help display only
            ;;
        *)
            PYTEST_ARGS+=("$arg")
            ;;
    esac
done

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Add utils to PATH and source formatting functions
export PATH="/workspaces/memogarden/utils:$PATH"
if [ -f "/workspaces/memogarden/utils/test-runner-functions.sh" ]; then
    source /workspaces/memogarden/utils/test-runner-functions.sh
else
    echo "ERROR: /workspaces/memogarden/utils/test-runner-functions.sh not found" >&2
    echo "Please ensure MemoGarden utils are available." >&2
    exit 1
fi

# ============================================================================
# SCRIPT START
# ============================================================================

# Script directory: run_tests.sh has already cd'd to its directory
# We use the current working directory directly
SCRIPT_DIR="$(pwd)"

# Verify pyproject.toml exists (sanity check)
if [ ! -f "$SCRIPT_DIR/pyproject.toml" ]; then
    echo "WARNING: pyproject.toml not found in $SCRIPT_DIR" >&2
    echo "Tests may not run correctly." >&2
fi

# Header output
test_header "$PROJECT_NAME Test Runner" "$PROJECT_NAME" "$TEST_RUN_ID"
echo ""

# Already in the correct directory (cd'd by run_tests.sh)

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "ERROR: poetry not found. Please install poetry first." >&2
    echo "Visit: https://python-poetry.org/docs/#installation" >&2
    exit 1
fi

# Verify dependencies if DEPENDENCY_CHECK is set and non-empty
if [ -n "$DEPENDENCY_CHECK" ]; then
    if ! poetry run python -c "$DEPENDENCY_CHECK" 2>/dev/null; then
        echo "WARNING: Poetry dependencies not installed."
        echo "Running 'poetry install'..."
        poetry install --quiet

        # Verify again after install
        if ! poetry run python -c "$DEPENDENCY_CHECK" 2>/dev/null; then
            echo "ERROR: Dependency check failed even after install." >&2
            echo "Check: $DEPENDENCY_CHECK" >&2
            exit 1
        fi
        echo "Dependencies installed successfully."
        echo ""
    fi
fi

# Run tests with poetry, capturing output for parsing
set +e  # Don't exit on test failure

# Capture pytest output to a temp file for parsing
TEMP_OUTPUT=$(mktemp)
poetry run pytest "${PYTEST_ARGS[@]}" 2>&1 | tee "$TEMP_OUTPUT"
PYTEST_EXIT_CODE=${PIPESTATUS[0]}

set -e

echo ""

# ============================================================================
# PARSE TEST RESULTS
# ============================================================================

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

# ============================================================================
# PARSE PASS/FAIL COUNTS
# ============================================================================

# TESTS_SUMMARY format: "250 passed" or "1 failed, 250 passed"
PASS_COUNT=$(echo "$TESTS_SUMMARY" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
FAIL_COUNT=$(echo "$TESTS_SUMMARY" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

# ============================================================================
# FOOTER OUTPUT
# ============================================================================

echo ""
test_summary "$STATUS" "$FAIL_COUNT" "$PASS_COUNT" "$DURATION" "$TEST_RUN_ID"

# Exit with pytest's exit code
exit $PYTEST_EXIT_CODE
