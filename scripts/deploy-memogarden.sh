#!/bin/bash
#
# MemoGarden - Local Deployment Script
#
# Run this script on the Raspberry Pi to deploy memogarden.
# Clones/updates the repo to /opt/memogarden and runs the install script.
#
# Usage:
#   ~/scripts/deploy-memogarden.sh
#
# This script:
# 1. Clones memogarden to /opt/memogarden (or updates if exists)
# 2. Runs the install script (idempotent - safe to run multiple times)

set -eo pipefail

#=============================================================================
# Configuration
#=============================================================================

INSTALL_DIR="/opt/memogarden"
REPO_URL="https://github.com/memogarden/memogarden.git"
API_REPO_URL="https://github.com/memogarden/memogarden-api.git"
SYSTEM_REPO_URL="https://github.com/memogarden/memogarden-system.git"

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

#=============================================================================
# Clone sub-repositories
#=============================================================================

log_info "Ensuring sub-repositories are present..."

# Clone/update memogarden-system
if [ -d "$INSTALL_DIR/memogarden-system" ]; then
    log_info "Updating memogarden-system..."
    cd "$INSTALL_DIR/memogarden-system"
    sudo git fetch origin
    sudo git reset --hard origin/main
else
    log_info "Cloning memogarden-system..."
    sudo git clone "$SYSTEM_REPO_URL" "$INSTALL_DIR/memogarden-system"
fi

# Clone/update memogarden-api
if [ -d "$INSTALL_DIR/memogarden-api" ]; then
    log_info "Updating memogarden-api..."
    cd "$INSTALL_DIR/memogarden-api"
    sudo git fetch origin
    sudo git reset --hard origin/main
else
    log_info "Cloning memogarden-api..."
    sudo git clone "$API_REPO_URL" "$INSTALL_DIR/memogarden-api"
fi

cd "$INSTALL_DIR"

#=============================================================================
# Install
#=============================================================================

log_info "Running install script..."
cd "$INSTALL_DIR"
sudo ./install.sh

log_info "Deployment complete!"
