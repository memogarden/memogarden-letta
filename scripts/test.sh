#!/bin/bash
# Run MemoGarden API test suite
#
# DEPRECATED: This script is deprecated. Use ./memogarden-api/run_tests.sh instead.
# The new run_tests.sh script provides:
# - Grep-able output with test run ID and summary
# - Consistent behavior across all MemoGarden projects
# - Last 6 lines always contain summary (for tail/grep)
#
# Migration: Replace 'scripts/test.sh' with 'memogarden-api/run_tests.sh'
#
# This script will continue to work for backward compatibility but may be removed in future versions.

echo "⚠️  DEPRECATED: Use './memogarden-api/run_tests.sh' instead"
echo "   See plan/test_runner_implementation_plan.md for details"
echo ""

cd "$(dirname "$0")/../memogarden-api"
poetry run pytest "$@"
