#!/bin/bash
# MemoGarden Migration Runner Script
# ===================================
#
# This script runs pending database migrations for MemoGarden.
# Migrations are SQL scripts in system/schemas/sql/migrations/.
#
# Usage:
#   ./scripts/migrate.sh              # Run all pending migrations
#   ./scripts/migrate.sh --list       # List available migrations
#   ./scripts/migrate.sh --status     # Show migration status
#
# Environment:
#   MEMOGARDEN_DATA_DIR - Data directory (default: ./data)
#   MEMOGARDEN_SOIL_DB  - Soil database path
#   MEMOGARDEN_CORE_DB  - Core database path

set -eo pipefail

#=============================================================================
# Configuration
#=============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/memogarden-api"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

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
# Migration Functions
#=============================================================================

list_migrations() {
    log_info "Available migrations:"
    echo ""

    # List Soil migrations
    if [ -d "$PROJECT_ROOT/memogarden-system/system/schemas/sql/migrations" ]; then
        echo "Soil migrations:"
        ls -1 "$PROJECT_ROOT/memogarden-system/system/schemas/sql/migrations/" 2>/dev/null | grep -E '\.sql$' || echo "  (none)"
    fi

    echo ""
}

run_migrations() {
    cd "$API_DIR"

    log_step "Running database migrations..."
    log_info "API directory: $API_DIR"

    poetry run python -c "
import os
import sqlite3
from pathlib import Path

# Get database paths
from system.config import settings

soil_path = settings.soil_database_path or './soil.db'
core_path = settings.database_path or './core.db'

print(f'Soil database: {soil_path}')
print(f'Core database: {core_path}')
print()

# Check if databases exist
if not os.path.exists(soil_path):
    print('❌ Soil database does not exist.')
    print('   Run ./scripts/init-db.sh first.')
    exit(1)

if not os.path.exists(core_path):
    print('❌ Core database does not exist.')
    print('   Run ./scripts/init-db.sh first.')
    exit(1)

# Apply migrations
print('✅ Databases exist.')
print()
print('Note: Migrations are automatically applied during database initialization.')
print('      (See system/core/__init__.py and system/soil/database.py)')
print()
print('Migration tracking table (Soil): migrations')
print('Migration tracking table (Core): migrations')
"
}

show_status() {
    cd "$API_DIR"

    log_step "Checking migration status..."

    poetry run python -c "
import sqlite3
import os
from system.config import settings

soil_path = settings.soil_database_path or './soil.db'
core_path = settings.database_path or './core.db'

print('Soil database migrations:')
if os.path.exists(soil_path):
    conn = sqlite3.connect(soil_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"migrations\"')
        if cursor.fetchone():
            cursor.execute('SELECT version FROM migrations ORDER BY version DESC LIMIT 1')
            result = cursor.fetchone()
            if result:
                print(f'  Current version: {result[0]}')
            else:
                print('  No migrations applied')
        else:
            print('  Migrations table not found')
    finally:
        conn.close()
else:
    print('  Database does not exist')

print()
print('Core database migrations:')
if os.path.exists(core_path):
    conn = sqlite3.connect(core_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"migrations\"')
        if cursor.fetchone():
            cursor.execute('SELECT version FROM migrations ORDER BY version DESC LIMIT 1')
            result = cursor.fetchone()
            if result:
                print(f'  Current version: {result[0]}')
            else:
                print('  No migrations applied')
        else:
            print('  Migrations table not found')
    finally:
        conn.close()
else:
    print('  Database does not exist')
"
}

#=============================================================================
# Main
#=============================================================================

case "${1:-}" in
    --list)
        list_migrations
        ;;
    --status)
        show_status
        ;;
    "")
        run_migrations
        ;;
    *)
        echo "Usage: $0 [--list|--status]"
        echo ""
        echo "Options:"
        echo "  --list    List available migrations"
        echo "  --status  Show migration status"
        echo "  (default) Run pending migrations"
        exit 1
        ;;
esac
