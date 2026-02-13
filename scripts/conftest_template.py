# -*- coding: utf-8 -*-
"""MemoGarden Test Configuration Template

This template provides standardized test environment setup for MemoGarden projects.

Environment Variables Standard:
------------------------------
Tests should rely on environment variables for configuration. Each project's
conftest.py should set required defaults.

Common test environment variables:

Database Paths (Soil/Core):
- MEMOGARDEN_SOIL_DB: Path to Soil database (default: ~/.memogarden/soil.db)
- MEMOGARDEN_CORE_DB: Path to Core database (default: ~/.memogarden/core.db)
- MEMOGARDEN_DATA_DIR: Base directory for MemoGarden data (default: ~/.memogarden)

API Specific:
- DATABASE_PATH: SQLite database path (default: :memory: for tests)
- JWT_SECRET_KEY: Secret key for JWT tokens (required for API tests)
- BYPASS_LOCALHOST_CHECK: Allow API calls from any host (default: true for tests)

Usage Example:
--------------
import os
import pytest


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set test-specific environment variables before all tests."""
    # Set test database to use in-memory database for isolation
    os.environ["DATABASE_PATH"] = ":memory:"

    # Set test JWT secret
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-do-not-use-in-production"

    # Allow testing from any host
    os.environ["BYPASS_LOCALHOST_CHECK"] = "true"

    yield

    # Cleanup: unset test environment variables
    os.environ.pop("DATABASE_PATH", None)
    os.environ.pop("JWT_SECRET_KEY", None)
    os.environ.pop("BYPASS_LOCALHOST_CHECK", None)
"""

# Template file - no actual code here, just documentation
