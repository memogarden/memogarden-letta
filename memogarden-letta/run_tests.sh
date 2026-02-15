#!/bin/bash
# MemoGarden-Letta Test Runner
#
# Standardized test entrypoint for mgLetta package.

# Project configuration
export PROJECT_NAME="mgLetta"
export MODULE_NAME="mgLetta"
export DEPENDENCY_CHECK=""
export TEST_FORMAT="${TEST_FORMAT:-textbox}"

# Find and source the centralized test entrypoint
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if MEMOGARDEN_ROOT is set
if [ -z "$MEMOGARDEN_ROOT" ]; then
    # Try to find root by looking for scripts/test_entrypoint.sh
    # Start from current directory and go up
    SEARCH_PATH="$SCRIPT_DIR"
    while [ "$SEARCH_PATH" != "/" ]; do
        if [ -f "$SEARCH_PATH/scripts/test_entrypoint.sh" ]; then
            export MEMOGARDEN_ROOT="$SEARCH_PATH"
            break
        fi
        SEARCH_PATH="$(dirname "$SEARCH_PATH")"
    done

    if [ -z "$MEMOGARDEN_ROOT" ]; then
        echo "ERROR: Cannot find MEMOGARDEN_ROOT (scripts/test_entrypoint.sh not found)" >&2
        echo "Please set MEMOGARDEN_ROOT environment variable" >&2
        exit 1
    fi
fi

# Source the centralized entrypoint
. "$MEMOGARDEN_ROOT/scripts/test_entrypoint.sh"
