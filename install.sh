#!/bin/bash
#
# MemoGarden Installation Script for Raspberry Pi
# ================================================
#
# This script installs MemoGarden on a Raspberry Pi running Debian-based Linux.
# It is idempotent - safe to run multiple times.
#
# RFC 004: Package Structure & Deployment (v2.0)
# - Verb-based deployment: "serve" for system daemon
# - Shared venv at /opt/memogarden/venv/
# - TOML configuration at /etc/memogarden/config.toml
# - Binary wrapper at /opt/memogarden/bin/memogarden
#
# Usage:
#   sudo ./install.sh
#
# Environment Variables (optional):
#   MEMOGARDEN_USER      - Service user (default: memogarden)
#   MEMOGARDEN_GROUP     - Service group (default: memogarden)
#   MEMOGARDEN_DATA_DIR  - Data directory (default: /var/lib/memogarden)
#   MEMOGARDEN_INSTALL_DIR - Installation directory (default: /opt/memogarden)
#
set -eo pipefail

#=============================================================================
# Configuration
#=============================================================================

MEMOGARDEN_USER="${MEMOGARDEN_USER:-memogarden}"
MEMOGARDEN_GROUP="${MEMOGARDEN_GROUP:-memogarden}"
MEMOGARDEN_DATA_DIR="${MEMOGARDEN_DATA_DIR:-/var/lib/memogarden}"
MEMOGARDEN_INSTALL_DIR="${MEMOGARDEN_INSTALL_DIR:-/opt/memogarden}"
MEMOGARDEN_VENV_DIR="${MEMOGARDEN_INSTALL_DIR}/venv"

# Git repositories (RFC 004: multi-repo structure)
MEMOGARDEN_SYSTEM_REPO="${MEMOGARDEN_SYSTEM_REPO:-https://github.com/memogarden/memogarden-system.git}"
MEMOGARDEN_API_REPO="${MEMOGARDEN_API_REPO:-https://github.com/memogarden/memogarden-api.git}"

# Optional: Specify git branches or tags
# MEMOGARDEN_SYSTEM_VERSION="${MEMOGARDEN_SYSTEM_VERSION:-main}"
# MEMOGARDEN_API_VERSION="${MEMOGARDEN_API_VERSION:-main}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#=============================================================================
# Distribution Detection
#=============================================================================

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/arch-release ]; then
        echo "arch"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro) # No Color

#=============================================================================
# Logging Functions
#=============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

#=============================================================================
# Utility Functions
#=============================================================================

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_python_version() {
    local required_major=3
    local required_minor=13

    if ! check_command python3; then
        log_error "Python 3 is not installed"
        return 1
    fi

    local python_version=$(python3 --version | cut -d' ' -f2)
    local major=$(echo "$python_version" | cut -d'.' -f1)
    local minor=$(echo "$python_version" | cut -d'.' -f2)

    if [ "$major" -lt "$required_major" ] || ([ "$major" -eq "$required_major" ] && [ "$minor" -lt "$required_minor" ]); then
        log_error "Python $required_major.$required_minor+ is required (found: $python_version)"
        return 1
    fi

    log_info "Python version check passed: $python_version"
    return 0
}

#=============================================================================
# Installation Steps
#=============================================================================

step_check_dependencies() {
    log_step "Checking system dependencies..."
    log_info "Detected distribution: $DISTRO"

    # Check Python version
    if ! check_python_version; then
        log_error "Please install Python 3.13 or higher"
        case "$DISTRO" in
            arch|manjaro|manjaro-arm)
                log_info "On Arch Linux ARM: sudo pacman -S python"
                ;;
            debian|ubuntu|raspbian)
                log_info "On Raspberry Pi OS: sudo apt update && sudo apt install python3"
                ;;
        esac
        exit 1
    fi

    # Check for pip and git based on distribution
    case "$DISTRO" in
        arch|manjaro|manjaro-arm)
            # Arch Linux uses pacman
            if ! check_command pip3; then
                log_warn "pip3 not found, installing..."
                sudo pacman -S --needed --noconfirm python-pip
            fi

            if ! check_command git; then
                log_warn "git not found, installing..."
                sudo pacman -S --needed --noconfirm git
            fi
            ;;
        debian|ubuntu|raspbian)
            # Debian-based systems use apt
            if ! check_command pip3; then
                log_warn "pip3 not found, installing..."
                sudo apt update
                sudo apt install -y python3-pip python3-venv
            fi

            if ! check_command git; then
                log_warn "git not found, installing..."
                sudo apt update
                sudo apt install -y git
            fi
            ;;
        *)
            log_warn "Unknown distribution $DISTRO, skipping package installation"
            log_warn "Please ensure Python 3.13+, pip3, venv, and git are installed"
            ;;
    esac

    log_info "All dependencies satisfied"
}

step_create_user() {
    log_step "Creating memogarden user and group..."

    case "$DISTRO" in
        arch|manjaro|manjaro-arm)
            # Arch Linux user/group creation
            if ! getent group "$MEMOGARDEN_GROUP" &> /dev/null; then
                sudo groupadd -r "$MEMOGARDEN_GROUP"
                log_info "Created group: $MEMOGARDEN_GROUP"
            else
                log_info "Group already exists: $MEMOGARDEN_GROUP"
            fi

            if ! id "$MEMOGARDEN_USER" &> /dev/null; then
                sudo useradd -r -g "$MEMOGARDEN_GROUP" \
                    -d "$MEMOGARDEN_INSTALL_DIR" \
                    -s /usr/bin/nologin \
                    "$MEMOGARDEN_USER"
                log_info "Created user: $MEMOGARDEN_USER"
            else
                log_info "User already exists: $MEMOGARDEN_USER"
            fi
            ;;
        debian|ubuntu|raspbian)
            # Debian user/group creation
            if ! getent group "$MEMOGARDEN_GROUP" &> /dev/null; then
                sudo groupadd --system "$MEMOGARDEN_GROUP"
                log_info "Created group: $MEMOGARDEN_GROUP"
            else
                log_info "Group already exists: $MEMOGARDEN_GROUP"
            fi

            if ! id "$MEMOGARDEN_USER" &> /dev/null; then
                sudo useradd --system \
                    --home-dir "$MEMOGARDEN_INSTALL_DIR" \
                    --no-create-home \
                    --shell /usr/sbin/nologin \
                    --gid "$MEMOGARDEN_GROUP" \
                    "$MEMOGARDEN_USER"
                log_info "Created user: $MEMOGARDEN_USER"
            else
                log_info "User already exists: $MEMOGARDEN_USER"
            fi
            ;;
        *)
            log_warn "Unknown distribution $DISTRO, skipping user creation"
            log_warn "Please ensure user '$MEMOGARDEN_USER' and group '$MEMOGARDEN_GROUP' exist"
            ;;
    esac
}

step_create_directories() {
    log_step "Creating directory structure..."

    # Create installation directory
    if [ ! -d "$MEMOGARDEN_INSTALL_DIR" ]; then
        sudo mkdir -p "$MEMOGARDEN_INSTALL_DIR"
        log_info "Created directory: $MEMOGARDEN_INSTALL_DIR"
    fi

    # Create shared venv directory (RFC 004)
    if [ ! -d "$MEMOGARDEN_VENV_DIR" ]; then
        sudo mkdir -p "$MEMOGARDEN_VENV_DIR"
        log_info "Created directory: $MEMOGARDEN_VENV_DIR"
    fi

    # Create bin directory for wrapper script (RFC 004)
    if [ ! -d "$MEMOGARDEN_INSTALL_DIR/bin" ]; then
        sudo mkdir -p "$MEMOGARDEN_INSTALL_DIR/bin"
        log_info "Created directory: $MEMOGARDEN_INSTALL_DIR/bin"
    fi

    # Create config directory (RFC 004)
    if [ ! -d "/etc/memogarden" ]; then
        sudo mkdir -p "/etc/memogarden"
        log_info "Created directory: /etc/memogarden"
    fi

    # Create data directory
    if [ ! -d "$MEMOGARDEN_DATA_DIR" ]; then
        sudo mkdir -p "$MEMOGARDEN_DATA_DIR"
        log_info "Created directory: $MEMOGARDEN_DATA_DIR"
    fi

    # Create log directory
    local log_dir="/var/log/memogarden"
    if [ ! -d "$log_dir" ]; then
        sudo mkdir -p "$log_dir"
        log_info "Created directory: $log_dir"
    fi

    # Create runtime state directory (RFC 004)
    if [ ! -d "/run/memogarden" ]; then
        sudo mkdir -p "/run/memogarden"
        log_info "Created directory: /run/memogarden"
    fi

    # Set ownership
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_DATA_DIR"
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$log_dir"
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_INSTALL_DIR"
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "/run/memogarden"

    log_info "Directory ownership set to $MEMOGARDEN_USER:$MEMOGARDEN_GROUP"
}

step_create_shared_venv() {
    log_step "Creating shared virtual environment..."

    # Create venv if it doesn't exist
    if [ ! -f "$MEMOGARDEN_VENV_DIR/bin/python" ]; then
        log_info "Creating venv at $MEMOGARDEN_VENV_DIR..."
        sudo -u "$MEMOGARDEN_USER" python3 -m venv "$MEMOGARDEN_VENV_DIR"
        log_info "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    # Upgrade pip
    sudo -u "$MEMOGARDEN_USER" "$MEMOGARDEN_VENV_DIR/bin/pip" install --upgrade pip

    log_info "Shared venv ready at $MEMOGARDEN_VENV_DIR"
}

step_install_python_packages() {
    log_step "Installing Python packages from git repositories..."

    local pip_exec="$MEMOGARDEN_VENV_DIR/bin/pip"

    # Install memogarden-system (RFC 004: separate git repo)
    log_info "Installing memogarden-system from $MEMOGARDEN_SYSTEM_REPO..."
    sudo -u "$MEMOGARDEN_USER" "$pip_exec" install "$MEMOGARDEN_SYSTEM_REPO"

    # Install memogarden-api (RFC 004: separate git repo)
    log_info "Installing memogarden-api from $MEMOGARDEN_API_REPO..."
    sudo -u "$MEMOGARDEN_USER" "$pip_exec" install "$MEMOGARDEN_API_REPO"

    # Verify gunicorn is installed
    local gunicorn_path="$MEMOGARDEN_VENV_DIR/bin/gunicorn"
    if [ ! -f "$gunicorn_path" ]; then
        log_error "gunicorn not found after installation"
        exit 1
    fi

    log_info "Python packages installed successfully"
    log_info "Gunicorn: $($gunicorn_path --version)"
}

step_configure_toml() {
    log_step "Configuring TOML settings..."

    local config_file="/etc/memogarden/config.toml"

    if [ -f "$config_file" ]; then
        log_info "Config file already exists: $config_file"
        log_info "Edit manually to change settings: sudo nano $config_file"
    else
        log_info "Creating config file: $config_file"

        # Generate JWT secret
        local jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

        # Create config.toml (RFC 004)
        sudo tee "$config_file" > /dev/null <<EOF
# MemoGarden Configuration
# RFC 004: Verb-based deployment (serve mode)
# Auto-generated by install.sh on $(date)

[runtime]
# Resource profile: "embedded" (Raspberry Pi) or "standard" (server)
resource_profile = "embedded"

[network]
bind_address = "127.0.0.1"
bind_port = 8080

[api]
# API prefix
api_v1_prefix = "/api/v1"
# CORS origins (add your frontend URL here)
cors_origins = ["http://localhost:3000", "http://localhost:5000"]

[security]
# JWT authentication settings
jwt_secret_key = "$jwt_secret"
jwt_expiry_days = 30
# Allow admin registration from remote networks (for headless deployments)
bypass_localhost_check = true
# Bcrypt work factor (lower for faster performance on embedded systems)
bcrypt_work_factor = 8
# Encryption mode (disabled, optional, required)
encryption = "disabled"

[paths]
# Path overrides (optional, defaults shown)
# data_dir = "/var/lib/memogarden"
# config_dir = "/etc/memogarden"
# log_dir = "/var/log/memogarden"
EOF

        # Set ownership and permissions
        sudo chown "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$config_file"
        sudo chmod 640 "$config_file"

        log_info "Config file created with defaults"
    fi
}

step_install_cli_wrapper() {
    log_step "Installing CLI wrapper binary..."

    # Find wrapper script relative to install script location
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local wrapper_source="$script_dir/scripts/memogarden-wrapper.sh"
    local wrapper_target="$MEMOGARDEN_INSTALL_DIR/bin/memogarden"

    if [ -f "$wrapper_source" ]; then
        # Copy wrapper script
        sudo cp "$wrapper_source" "$wrapper_target"
        sudo chmod +x "$wrapper_target"
        sudo chown "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$wrapper_target"
        log_info "CLI wrapper installed: $wrapper_target"
    else
        log_warn "Wrapper script not found at $wrapper_source"
        log_warn "Skipping CLI wrapper installation"
    fi
}

step_install_gunicorn_config() {
    log_step "Installing gunicorn configuration..."

    local gunicorn_conf="/etc/memogarden/gunicorn.conf.py"

    if [ -f "$gunicorn_conf" ]; then
        log_info "Gunicorn config already exists: $gunicorn_conf"
    else
        # Create gunicorn config
        sudo tee "$gunicorn_conf" > /dev/null <<EOF
# Gunicorn configuration for MemoGarden
import multiprocessing

# Server socket
bind = "127.0.0.1:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "memogarden"

# Logging
loglevel = "info"
accesslog = "/var/log/memogarden/access.log"
errorlog = "/var/log/memogarden/error.log"
access_logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process management
daemon = False
pidfile = "/run/memogarden/memogarden.pid"
umask = 0o077

# Server mechanics
max_requests = 1000
max_requests_jitter = 50
preload_app = True
sendfile = True
reuse_port = True
EOF

        sudo chown "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$gunicorn_conf"
        sudo chmod 640 "$gunicorn_conf"

        log_info "Gunicorn config created: $gunicorn_conf"
    fi
}

step_install_systemd_service() {
    log_step "Installing systemd service..."

    local service_file="/etc/systemd/system/memogarden.service"

    # Create systemd service file (RFC 004)
    sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=MemoGarden Personal Information System
Documentation=https://docs.memogarden.org
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=$MEMOGARDEN_USER
Group=$MEMOGARDEN_GROUP

# Use CLI wrapper (RFC 004)
ExecStart=$MEMOGARDEN_INSTALL_DIR/bin/memogarden serve

# Working directory
WorkingDirectory=$MEMOGARDEN_DATA_DIR

# Environment
Environment="PATH=$MEMOGARDEN_VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="MEMOGARDEN_VERB=serve"

# Restart policy
Restart=on-failure
RestartSec=5s
TimeoutSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=memogarden

# Security (RFC 004)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$MEMOGARDEN_DATA_DIR /var/log/memogarden /run/memogarden

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd daemon
    sudo systemctl daemon-reload

    # Enable service (but don't start it yet)
    sudo systemctl enable memogarden.service

    log_info "Systemd service installed and enabled"
}

step_verify_installation() {
    log_step "Verifying installation..."

    # Check venv exists
    if [ ! -f "$MEMOGARDEN_VENV_DIR/bin/python" ]; then
        log_error "CRITICAL: venv not found at $MEMOGARDEN_VENV_DIR"
        exit 1
    fi

    # Check gunicorn exists
    local gunicorn_path="$MEMOGARDEN_VENV_DIR/bin/gunicorn"
    if [ ! -f "$gunicorn_path" ]; then
        log_error "CRITICAL: gunicorn not found in venv"
        exit 1
    fi

    # Check CLI wrapper exists
    if [ ! -f "$MEMOGARDEN_INSTALL_DIR/bin/memogarden" ]; then
        log_warn "WARNING: CLI wrapper not found"
    fi

    # Check config exists
    if [ ! -f "/etc/memogarden/config.toml" ]; then
        log_error "CRITICAL: config.toml not found"
        exit 1
    fi

    # Verify packages are importable
    log_info "Testing Python imports..."
    if ! "$MEMOGARDEN_VENV_DIR/bin/python" -c "import system; import api" 2>/dev/null; then
        log_error "CRITICAL: Failed to import system or api packages"
        exit 1
    fi

    log_info "Installation verification passed"
    log_info ""
    log_info "Installation summary:"
    log_info "  - Shared venv: $MEMOGARDEN_VENV_DIR"
    log_info "  - Gunicorn: $gunicorn_path"
    log_info "  - CLI wrapper: $MEMOGARDEN_INSTALL_DIR/bin/memogarden"
    log_info "  - Config: /etc/memogarden/config.toml"
    log_info "  - Data directory: $MEMOGARDEN_DATA_DIR"
}

step_finalize() {
    log_step "Finalizing installation..."

    # Set permissions on installed files
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_INSTALL_DIR"

    log_info "Installation complete!"
}

#=============================================================================
# Main Installation Flow
#=============================================================================

get_accessible_url() {
    # Try to get the hostname (for mDNS/.local access)
    local hostname=$(hostname 2>/dev/null || echo "")
    # Try to get the primary IP address
    local ip=$(ip route get 1 2>/dev/null | awk '{print $7}' | head -1 || echo "")

    if [ -n "$hostname" ]; then
        echo "http://$hostname.local:8080"
    elif [ -n "$ip" ]; then
        echo "http://$ip:8080"
    else
        echo "http://<hostname-or-ip>:8080"
    fi
}

main() {
    echo ""
    echo "=================================="
    echo "  MemoGarden Installation Script"
    echo "  RFC 004: Package Deployment v2.0"
    echo "=================================="
    echo ""

    step_check_dependencies
    step_create_user
    step_create_directories
    step_create_shared_venv
    step_install_python_packages
    step_configure_toml
    step_install_gunicorn_config
    step_install_cli_wrapper
    step_install_systemd_service
    step_verify_installation
    step_finalize

    echo ""
    log_info "MemoGarden has been installed successfully!"
    echo ""
    local accessible_url=$(get_accessible_url)
    echo "Next steps:"
    echo "  1. Review config: sudo nano /etc/memogarden/config.toml"
    echo "  2. Start the service: sudo systemctl start memogarden"
    echo "  3. Check service status: sudo systemctl status memogarden"
    echo "  4. View logs: sudo journalctl -u memogarden -f"
    echo "  5. Register admin user: Visit $accessible_url/admin/register"
    echo ""
}

# Run main function
main "$@"
