#!/bin/bash
# Start MemoGarden API development server
#
# This script starts the Flask development server with auto-reload.
# For production, use gunicorn via systemd service.
#
# Usage:
#   ./scripts/run.sh

set -eo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to API directory
cd "$PROJECT_ROOT/memogarden-api"

# Start development server
echo "Starting MemoGarden API development server..."
echo "Project root: $PROJECT_ROOT"
echo "API directory: $(pwd)"
echo ""
poetry run flask --app api.main run --debug
