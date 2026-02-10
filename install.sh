#!/bin/bash
#
# MemoGarden Installation Script for Raspberry Pi
# ================================================
#
# This script installs MemoGarden on a Raspberry Pi running Debian-based Linux.
# It is idempotent - safe to run multiple times.
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
MEMOGARDEN_POETRY_DIR="${MEMOGARDEN_INSTALL_DIR}/.local/poetry"

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
                sudo apt install -y python3-pip
            fi

            if ! check_command git; then
                log_warn "git not found, installing..."
                sudo apt update
                sudo apt install -y git
            fi
            ;;
        *)
            log_warn "Unknown distribution $DISTRO, skipping package installation"
            log_warn "Please ensure Python 3.13+, pip3, and git are installed"
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

    # Set ownership
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_DATA_DIR"
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$log_dir"
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_INSTALL_DIR"

    log_info "Directory ownership set to $MEMOGARDEN_USER:$MEMOGARDEN_GROUP"
}

step_install_poetry() {
    log_step "Installing project-specific Poetry..."

    # Install Poetry to project-specific location
    local poetry_bin="$MEMOGARDEN_POETRY_DIR/bin"
    local poetry_exec="$poetry_bin/poetry"

    if [ -f "$poetry_exec" ]; then
        local poetry_version=$("$poetry_exec" --version)
        log_info "Poetry already installed: $poetry_version"
    else
        log_info "Installing Poetry to $MEMOGARDEN_POETRY_DIR..."
        # Create installation directory
        sudo mkdir -p "$MEMOGARDEN_POETRY_DIR"
        sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_POETRY_DIR"

        # Install Poetry as memogarden user
        sudo -u "$MEMOGARDEN_USER" bash -c "
            export POETRY_HOME='$MEMOGARDEN_POETRY_DIR'
            curl -sSL https://install.python-poetry.org | python3 -
        "

        log_info "Poetry installed successfully"
    fi

    # Configure Poetry for MemoGarden
    # 1. Use in-project virtualenvs (.venv directory)
    # 2. Set cache directory to /opt/memogarden/.cache (accessible by memogarden user)
    sudo -u "$MEMOGARDEN_USER" "$poetry_exec" config virtualenvs.in-project true
    sudo -u "$MEMOGARDEN_USER" "$poetry_exec" config cache-dir "$MEMOGARDEN_INSTALL_DIR/.cache/pypoetry"

    log_info "Poetry configured for MemoGarden"
}

step_install_python_dependencies() {
    log_step "Installing Python dependencies..."

    cd "$MEMOGARDEN_INSTALL_DIR/memogarden-api"

    # Use project-specific Poetry installation
    local poetry_exec="$MEMOGARDEN_POETRY_DIR/bin/poetry"

    # Install dependencies using Poetry
    sudo -u "$MEMOGARDEN_USER" "$poetry_exec" install

    # Find where gunicorn actually is
    local gunicorn_path=""
    if [ -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" ]; then
        gunicorn_path="$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin/gunicorn"
    else
        # Search in Poetry cache
        gunicorn_path=$(find "$MEMOGARDEN_INSTALL_DIR/.cache/pypoetry/virtualenvs" -name "gunicorn" -type f 2>/dev/null | head -1)
        if [ -z "$gunicorn_path" ]; then
            log_error "Cannot find gunicorn after installation"
            sudo -u "$MEMOGARDEN_USER" "$poetry_exec" env info
            exit 1
        fi
        log_warn "Note: Poetry created venv in cache location (not in-project)"
        log_warn "This is okay - systemd service will be configured accordingly"
    fi

    log_info "Python dependencies installed successfully"
    log_info "Gunicorn: $(sudo -u "$MEMOGARDEN_USER" "$gunicorn_path" --version)"
}

step_configure_environment() {
    log_step "Configuring environment variables..."

    local env_file="$MEMOGARDEN_INSTALL_DIR/memogarden-api/.env"

    if [ ! -f "$env_file" ]; then
        # Copy .env.example to .env
        if [ -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/.env.example" ]; then
            sudo -u "$MEMOGARDEN_USER" cp "$MEMOGARDEN_INSTALL_DIR/memogarden-api/.env.example" "$env_file"
            log_info "Created .env from .env.example"
        else
            log_warn ".env.example not found, creating minimal .env"
            sudo -u "$MEMOGARDEN_USER" tee "$env_file" > /dev/null <<EOF
# MemoGarden Environment Configuration
MEMOGARDEN_DATA_DIR=$MEMOGARDEN_DATA_DIR
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
EOF
        fi
    else
        log_info ".env already exists, skipping"
    fi

    # Set environment-specific variables
    sudo -u "$MEMOGARDEN_USER" tee -a "$env_file" > /dev/null <<EOF

# Auto-generated by install.sh on $(date)
MEMOGARDEN_DATA_DIR=$MEMOGARDEN_DATA_DIR
# Allow admin registration from remote networks (for headless deployments)
BYPASS_LOCALHOST_CHECK=true
EOF

    log_info "Environment configured"
}

step_install_systemd_service() {
    log_step "Installing systemd service..."

    local service_file="/etc/systemd/system/memogarden.service"

    # Determine virtualenv path (prefer in-project, fall back to cache)
    local venv_bin_path=""
    if [ -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" ]; then
        venv_bin_path="$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin"
    else
        # Find Poetry cache venv
        venv_bin_path=$(find "$MEMOGARDEN_INSTALL_DIR/.cache/pypoetry/virtualenvs" -name "memogarden-api-*-py3.13" -type d 2>/dev/null | head -1)/bin
        if [ ! -f "$venv_bin_path/gunicorn" ]; then
            log_error "Cannot find gunicorn in any known location"
            exit 1
        fi
        log_warn "Using Poetry cache venv: $venv_bin_path"
    fi

    # Create systemd service file
    sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=MemoGarden API Server
After=network.target

[Service]
Type=notify
User=$MEMOGARDEN_USER
Group=$MEMOGARDEN_GROUP
WorkingDirectory=$MEMOGARDEN_INSTALL_DIR/memogarden-api
Environment="PATH=$venv_bin_path:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$MEMOGARDEN_INSTALL_DIR/memogarden-api/.env
ExecStart=$venv_bin_path/gunicorn --config gunicorn.conf.py --log-file /var/log/memogarden/gunicorn.log --log-level info api.main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=10
TimeoutSec=30

# Logging
StandardOutput=append:/var/log/memogarden/memogarden.log
StandardError=append:/var/log/memogarden/memogarden.error

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$MEMOGARDEN_DATA_DIR /var/log/memogarden

[Install]
WantedBy=multi-user.target
EOF

    # Create PID directory
    sudo mkdir -p /var/run/memogarden
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" /var/run/memogarden

    # Reload systemd daemon
    sudo systemctl daemon-reload

    # Enable service (but don't start it yet)
    sudo systemctl enable memogarden.service

    log_info "Systemd service installed and enabled"
}

step_verify_installation() {
    log_step "Verifying installation..."

    # Find gunicorn
    local gunicorn_path=""
    if [ -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" ]; then
        gunicorn_path="$MEMOGARDEN_INSTALL_DIR/memogarden-api/.venv/bin/gunicorn"
    else
        gunicorn_path=$(find "$MEMOGARDEN_INSTALL_DIR/.cache/pypoetry/virtualenvs" -name "gunicorn" -type f 2>/dev/null | head -1)
    fi

    if [ ! -f "$gunicorn_path" ]; then
        log_error "CRITICAL: gunicorn not found"
        log_error "Installation verification failed"
        exit 1
    fi

    if [ ! -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/gunicorn.conf.py" ]; then
        log_warn "WARNING: gunicorn.conf.py not found"
    fi

    if [ ! -f "$MEMOGARDEN_INSTALL_DIR/memogarden-api/api/main.py" ]; then
        log_error "CRITICAL: api/main.py not found"
        log_error "Installation verification failed"
        exit 1
    fi

    # Try to validate gunicorn can load the app
    log_info "Testing gunicorn configuration..."
    cd "$MEMOGARDEN_INSTALL_DIR/memogarden-api"
    local venv_bin=$(dirname "$gunicorn_path")
    if "$venv_bin/gunicorn" --check-config --config gunicorn.conf.py api.main:app 2>&1 | grep -q "Error"; then
        log_warn "gunicorn configuration check found issues (may be okay if using env vars)"
    else
        log_info "gunicorn configuration looks good"
    fi

    log_info "Installation verification passed"
    log_info ""
    log_info "Installation summary:"
    log_info "  - Poetry: $MEMOGARDEN_POETRY_DIR/bin/poetry"
    log_info "  - Gunicorn: $gunicorn_path"
    log_info "  - Data directory: $MEMOGARDEN_DATA_DIR"
}

step_finalize() {
    log_step "Finalizing installation..."

    # Set permissions on installed files
    sudo chown -R "$MEMOGARDEN_USER:$MEMOGARDEN_GROUP" "$MEMOGARDEN_INSTALL_DIR"

    # Note: CLI symlink will be created when CLI script is implemented
    # local symlink="/usr/local/bin/memogarden"
    # if [ ! -L "$symlink" ]; then
    #     sudo ln -s "$MEMOGARDEN_INSTALL_DIR/scripts/memogarden-cli.sh" "$symlink"
    # fi

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
        echo "http://$hostname.local:5000"
    elif [ -n "$ip" ]; then
        echo "http://$ip:5000"
    else
        echo "http://<hostname-or-ip>:5000"
    fi
}

main() {
    echo ""
    echo "=================================="
    echo "  MemoGarden Installation Script"
    echo "=================================="
    echo ""

    step_check_dependencies
    step_create_user
    step_create_directories
    step_install_poetry
    step_install_python_dependencies
    step_configure_environment
    step_install_systemd_service
    step_verify_installation
    step_finalize

    echo ""
    log_info "MemoGarden has been installed successfully!"
    echo ""
    local accessible_url=$(get_accessible_url)
    echo "Next steps:"
    echo "  1. Review and edit .env: sudo nano $MEMOGARDEN_INSTALL_DIR/memogarden-api/.env"
    echo "  2. Start the service: sudo systemctl start memogarden"
    echo "  3. Check service status: sudo systemctl status memogarden"
    echo "  4. View logs: sudo journalctl -u memogarden -f"
    echo "  5. Register admin user: Visit $accessible_url/admin/register"
    echo ""
}

# Run main function
main "$@"
