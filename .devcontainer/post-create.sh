#!/bin/bash
set -e

# =============================================================================
# MemoGarden Devcontainer - User Layer (post-create)
# =============================================================================
#
# This script runs ONCE when the devcontainer is first created.
# It runs as the 'vscode' user and sets up user-specific configuration.
#
# What happens here:
# - Install Poetry (user-specific Python package manager)
# - Install project dependencies via Poetry
# - Configure user shell (.bashrc aliases)
#
# What does NOT happen here:
# - System package installation (handled by Dockerfile)
# - Global tool installation (handled by Dockerfile)
#
# =============================================================================

echo "🌱 Setting up MemoGarden Development Environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Install Poetry if not already installed
echo ""
echo "📦 Installing Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ Poetry installed${NC}"
else
    echo -e "${GREEN}✓ Poetry already installed${NC}"
fi

# Configure Poetry to use in-project virtualenvs
echo ""
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.in-project true
echo -e "${GREEN}✓ Poetry configured to use in-project .venv${NC}"

# Function to install Poetry dependencies
install_poetry_deps() {
    local project_path=$1
    local project_name=$2

    if [ -d "$project_path" ] && [ -f "$project_path/pyproject.toml" ]; then
        echo -e "${BLUE}Installing dependencies for $project_name...${NC}"
        cd "$project_path"
        poetry install --with dev
        echo -e "${GREEN}✓ $project_name dependencies installed${NC}"
    else
        echo -e "${BLUE}⚠ $project_path not found or no pyproject.toml, skipping...${NC}"
    fi
}

# Install dependencies for each Poetry project
echo ""
echo "📦 Installing project dependencies..."
install_poetry_deps "/workspaces/memogarden/memogarden-system" "memogarden-system"
install_poetry_deps "/workspaces/memogarden/memogarden-api" "memogarden-api"
install_poetry_deps "/workspaces/memogarden/memogarden-client" "memogarden-client"

# Setup pre-commit hooks
echo ""
echo "🪝 Setting up pre-commit hooks..."
cd /workspaces/memogarden
if [ -f "scripts/pre-commit" ]; then
    chmod +x scripts/pre-commit
    echo -e "${GREEN}✓ Root pre-commit hook marked executable${NC}"
fi

# Verify installations
echo ""
echo "🔍 Verifying installation..."
echo -e "${BLUE}Python version:${NC}"
python3 --version

echo -e "${BLUE}Poetry version:${NC}"
poetry --version

echo -e "${BLUE}Development tools:${NC}"
echo "  - pytest: $(pytest --version 2>&1 | head -n1)"
echo "  - ruff: $(ruff --version)"
echo "  - black: $(black --version)"

# Create helpful aliases
echo ""
echo "📝 Creating helper aliases..."
cat >> /home/vscode/.bashrc << 'EOF'

# MemoGarden Development Aliases
alias mg-api='cd /workspaces/memogarden/memogarden-api && poetry run flask --app api/main run --debug'
alias mg-test='cd /workspaces/memogarden/memogarden-api && poetry run pytest'
alias mg-test-system='cd /workspaces/memogarden/memogarden-system && poetry run pytest'
alias mg-test-client='cd /workspaces/memogarden/memogarden-client && poetry run pytest'
alias mg-lint='/workspaces/memogarden/scripts/lint.sh'
alias mg-root='cd /workspaces/memogarden'

# Quick git status for all repos
alias mg-status='echo "=== Root ===" && git status && echo -e "\n=== System ===" && cd /workspaces/memogarden/memogarden-system && git status && echo -e "\n=== API ===" && cd /workspaces/memogarden/memogarden-api && git status && echo -e "\n=== Client ===" && cd /workspaces/memogarden/memogarden-client && git status && cd /workspaces/memogarden'
EOF

echo -e "${GREEN}✓ Aliases added to ~/.bashrc${NC}"

# Print workspace structure
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       MemoGarden Devcontainer Ready! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📂 Workspace structure:"
echo "  /workspaces/memogarden                    → Root repository (docs, plans, scripts)"
echo "  /workspaces/memogarden/memogarden-system  → System package (db operations, utils)"
echo "  /workspaces/memogarden/memogarden-api     → Flask API (endpoints, tests)"
echo "  /workspaces/memogarden/memogarden-client  → Python SDK for MemoGarden API"
echo ""
echo "🚀 Quick commands:"
echo "  mg-api         → Start Flask API server"
echo "  mg-test        → Run API tests"
echo "  mg-test-system → Run system tests"
echo "  mg-test-client → Run client tests"
echo "  mg-lint        → Run ruff linter"
echo "  mg-status      → Show git status for all repos"
echo "  mg-root        → Go to workspace root"
echo ""
echo "📖 Remember: Each subdirectory has its own git repository!"
echo "   Use 'git status' in the specific directory you're working on."
echo ""
