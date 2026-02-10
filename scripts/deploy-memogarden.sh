#!/bin/bash
#
# MemoGarden - Local Deployment Script
#
# Run this script on the Raspberry Pi to deploy memogarden.
#
# RFC 004: Package Structure & Deployment (v2.0)
# - Clones root repo to /opt/memogarden for install.sh and wrapper script
# - install.sh handles pip install from git repositories
# - Packages are installed into shared venv at /opt/memogarden/venv/
#
# Usage:
#   ~/scripts/deploy-memogarden.sh
#
# This script:
# 1. Clones memogarden root repo to /opt/memogarden (or updates if exists)
# 2. Runs the install script (idempotent - safe to run multiple times)
# 3. Starts the service

set -eo pipefail

#=============================================================================
# Configuration
#=============================================================================

INSTALL_DIR="/opt/memogarden"
REPO_URL="https://github.com/memogarden/memogarden.git"

#=============================================================================
# Colors
#=============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

#=============================================================================
# Deploy
#=============================================================================

# Add safe.directory for Git (fixes ownership security error)
sudo git config --global --add safe.directory "$INSTALL_DIR" 2>/dev/null || true

# Stop service if running (to avoid conflicts during update)
if systemctl is-active --quiet memogarden 2>/dev/null; then
    log_info "Stopping memogarden service..."
    sudo systemctl stop memogarden
fi

# Clone or update root repository
if [ -d "$INSTALL_DIR" ]; then
    log_info "Updating existing installation at ${INSTALL_DIR}..."
    cd "$INSTALL_DIR"
    sudo git fetch origin
    sudo git reset --hard origin/main
else
    log_info "Cloning fresh installation to ${INSTALL_DIR}..."
    sudo git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Make scripts executable
sudo chmod +x "$INSTALL_DIR/install.sh"
sudo chmod +x "$INSTALL_DIR/scripts/memogarden-wrapper.sh" 2>/dev/null || true

#=============================================================================
# Install
#=============================================================================

log_info "Running install script..."
cd "$INSTALL_DIR"
sudo ./install.sh

#=============================================================================
# Start Service
#=============================================================================

log_info "Starting memogarden service..."
sudo systemctl daemon-reload
sudo systemctl start memogarden
sudo systemctl status memogarden --no-pager

log_info "Deployment complete!"
