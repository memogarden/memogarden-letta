#!/usr/bin/env bash
# MemoGarden CLI Wrapper
#
# This script activates the shared virtual environment and runs the Flask application.
# Deployed to: /opt/memogarden/bin/memogarden (serve) or ~/.local/bin/memogarden (run)
#
# Usage: memogarden [serve|run|deploy] [--config <path>]
#
# RFC 004: Command verbs determine configuration sources and file locations

set -e

# Script directory (for locating venv)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine deployment context from first argument
# Default to "run" if no verb specified
VERB="${1:-run}"
shift  # Remove verb from arguments

# Parse optional arguments
CONFIG_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        *)
            # Unknown argument - pass through to Flask
            break
            ;;
    esac
done

# Set venv and binary paths based on deployment context
if [[ "$VERB" == "serve" ]]; then
    # System daemon: /opt/memogarden/venv
    VENV_DIR="/opt/memogarden/venv"
    CONFIG_DEFAULT="/etc/memogarden/config.toml"
elif [[ "$VERB" == "run" ]]; then
    # User process: use shared venv if in development, otherwise user-local
    if [[ -d "/opt/memogarden/venv" ]]; then
        VENV_DIR="/opt/memogarden/venv"
    else
        # For user-local installation
        VENV_DIR="$HOME/.local/lib/memogarden/venv"
    fi
    CONFIG_DEFAULT="$HOME/.config/memogarden/config.toml"
elif [[ "$VERB" == "deploy" ]]; then
    # Container: system-wide Python install
    VENV_DIR=""  # No venv in container
    CONFIG_DEFAULT="/config/config.toml"
else
    echo "Error: Unknown verb '$VERB'" >&2
    echo "Usage: memogarden [serve|run|deploy] [--config <path>]" >&2
    exit 1
fi

# Use specified config path or default
if [[ -n "$CONFIG_PATH" ]]; then
    CONFIG_FILE="$CONFIG_PATH"
else
    CONFIG_FILE="$CONFIG_DEFAULT"
fi

# Activate venv if present (serve and run modes)
if [[ -n "$VENV_DIR" && -d "$VENV_DIR" ]]; then
    source "$VENV_DIR/bin/activate"
fi

# Set config path as environment variable for API config module
export MEMOGARDEN_CONFIG="$CONFIG_FILE"
export MEMOGARDEN_VERB="$VERB"

# Run the Flask application
# For serve mode, use gunicorn (production)
# For run mode, use flask development server
if [[ "$VERB" == "serve" ]]; then
    # Production: use gunicorn
    exec gunicorn --config /etc/memogarden/gunicorn.conf.py api.main:create_app "$@"
else
    # Development: use flask dev server
    exec python -m flask run --host=127.0.0.1 --port=5000 "$@"
fi
