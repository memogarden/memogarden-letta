# MemoGarden Test Runner Functions
# Shared bash functions for standardized test output across all MemoGarden projects.
# Source this file in run_tests.sh scripts.
#
# Usage:
#   source /workspaces/memogarden/utils/test-runner-functions.sh
#   TEST_FORMAT=textbox  # or plaintext, markdown
#   test_header "MemoGarden API" "memogarden-api" "$TEST_RUN_ID"
#   test_summary "FAILED" "1" "250" "64.21s" "$TEST_RUN_ID"

# Default box width (can be overridden by setting WIDTH before sourcing)
: "${WIDTH:=60}"

# Output format: textbox (default), plaintext, or markdown
: "${TEST_FORMAT:=textbox}"

# Paths to formatters (relative to repo root)
FORMATTERS_DIR="/workspaces/memogarden/utils/format"

# _test_formatter - Get the formatter script for current format
_test_formatter() {
    case "$TEST_FORMAT" in
        textbox|plain|text)
            echo "$FORMATTERS_DIR/textbox.py"
            ;;
        markdown|md)
            echo "$FORMATTERS_DIR/markdown.py"
            ;;
        plaintext|plain)
            echo "$FORMATTERS_DIR/plaintext.py"
            ;;
        *)
            echo "$FORMATTERS_DIR/textbox.py"
            ;;
    esac
}

# test_header - Print formatted test run header
# Args:
#   $1 - Title (e.g., "MemoGarden API Test Runner")
#   $2 - Project name (e.g., "memogarden-api")
#   $3 - Test run ID (e.g., "20260213-074846")
test_header() {
    local title="$1"
    local project="$2"
    local run_id="$3"

    local formatter="$(_test_formatter)"

    if [ "$TEST_FORMAT" = "textbox" ]; then
        python3 "$formatter" \
            --title "$title" \
            --body "Project: $project" "Test Run ID: $run_id" \
            --width "$WIDTH"
    else
        python3 "$formatter" \
            --title "$title" \
            --body "Project: $project" "Test Run ID: $run_id"
    fi
}

# test_summary - Print formatted test summary
# Args:
#   $1 - Status (e.g., "PASSED", "FAILED", "ERROR")
#   $2 - Fail count (e.g., "1", "0")
#   $3 - Pass count (e.g., "250")
#   $4 - Duration (e.g., "64.21s")
#   $5 - Test run ID (e.g., "20260213-074846")
test_summary() {
    local status="$1"
    local fail_count="$2"
    local pass_count="$3"
    local duration="$4"
    local run_id="$5"

    # Format tests line based on results
    local tests_line
    if [ "$fail_count" -eq 0 ]; then
        tests_line="$pass_count passed"
    else
        tests_line="$fail_count failed, $pass_count passed"
    fi

    local formatter="$(_test_formatter)"

    if [ "$TEST_FORMAT" = "textbox" ]; then
        python3 "$formatter" \
            --title "Test Summary" \
            --body "Status: $status" "Tests: $tests_line" "Duration: $duration" "Test Run ID: $run_id" \
            --width "$WIDTH"
    else
        python3 "$formatter" \
            --title "Test Summary" \
            --body "Status: $status" "Tests: $tests_line" "Duration: $duration" "Test Run ID: $run_id"
    fi
}
