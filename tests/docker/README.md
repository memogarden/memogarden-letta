# MemoGarden Deployment Tests

This directory contains integration tests for the MemoGarden deployment infrastructure.

## Auto-Detection

The test script automatically detects your environment and runs appropriate tests:

- **In container (Docker, codespaces)**: Runs local validation tests
- **On host machine with Docker**: Runs full Docker-based test
- **On host without Docker**: Runs local validation tests

## Quick Test (Auto-Detect)

```bash
cd /workspaces/memogarden
bash tests/docker/test-deployment.sh
```

The script will:
1. Auto-detect your environment
2. Choose appropriate test mode
3. Validate deployment configuration

## Manual Mode Selection

Force specific test mode:

```bash
# Force Docker test (requires Docker)
bash tests/docker/test-deployment.sh --docker

# Force local test (skip Docker)
bash tests/docker/test-deployment.sh --local

# Show help
bash tests/docker/test-deployment.sh --help
```

## What Gets Tested

### In Container (Local Tests)
1. **Environment**: Python 3.10+
2. **Source Validation**: install.sh structure and components
3. **Directory Structure**: Package organization
4. **Configuration**: .env.example with RFC-004 variables
5. **Poetry**: pyproject.toml validation
6. **API Module**: Import verification

### Full Docker Test (Host Machine)
1. **Environment**: Python 3.10+, git, curl
2. **Installation**: Full install.sh execution
3. **Directories**: /opt/memogarden, /var/lib/memogarden
4. **Configuration**: .env file generation
5. **Dependencies**: Poetry install
6. **API Startup**: Flask app starts
7. **Endpoints**: /health and /status work

## CI/CD Integration

Add to your CI pipeline:

```yaml
# Example for GitHub Actions
- name: Test Deployment
  run: |
    bash tests/docker/test-deployment.sh
```

## Troubleshooting

### Test fails with "No source directory found"
- Ensure you're running from repository root
- Check that install.sh exists

### API import fails
- Expected in shared test environments
- Test will pass with warning

### Poetry not found
- Test will skip poetry install checks
- Only validates pyproject.toml structure
