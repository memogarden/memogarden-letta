#!/bin/bash
# MemoGarden Database Initialization Script
# =========================================
#
# This script initializes the MemoGarden databases (Soil and Core).
# It is safe to run multiple times - checks for existing databases.
#
# Usage:
#   ./scripts/init-db.sh
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

#=============================================================================
# Main Logic
#=============================================================================

cd "$API_DIR"

log_info "Initializing MemoGarden databases..."
log_info "API directory: $API_DIR"

# Run Python initialization script
poetry run python -c "
from system.config import settings
from system.core import init_db
from system.soil.database import Soil
import os

# Get database paths
soil_path = settings.soil_database_path or './soil.db'
core_path = settings.database_path or './core.db'

print(f'Soil database: {soil_path}')
print(f'Core database: {core_path}')
print()

# Check if databases exist
soil_exists = os.path.exists(soil_path)
core_exists = os.path.exists(core_path)

if soil_exists and core_exists:
    print('⚠️  Both databases already exist.')
    print('   To reinitialize, delete the existing databases first.')
    exit(0)

# Initialize databases
print('Initializing Core database...')
init_db()

print('Initializing Soil database...')
soil = Soil(db_path=str(soil_path))
soil.init_schema()

print()
print('✅ Databases initialized successfully!')
print()
print('Next steps:')
print('  1. Start the API server: ./scripts/run.sh')
print('  2. Register admin user: Visit http://localhost:5000/admin/register')
"

echo ""
log_info "Database initialization complete!"
