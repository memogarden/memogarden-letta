# MemoGarden Devcontainer

This directory contains the VSCode devcontainer configuration for MemoGarden development.

## Architecture Overview

The devcontainer uses a **two-layer architecture** with clear separation of concerns:

### Layer 1: System Layer (`Dockerfile`)
- **Runs as:** `root` at build time
- **Installs:** System packages (Python 3.13, gh, global tools)
- **Not:** User-specific tools (Poetry), project dependencies

### Layer 2: User Layer (`post-create.sh`)
- **Runs as:** `vscode` on first container creation
- **Installs:** Poetry, project dependencies, user config
- **Not:** System packages (handled by Dockerfile)

**Why?** This avoids permission issues (Poetry installed as root is inaccessible to vscode user) and provides clear separation of concerns.

## What This Provides

- **Python 3.13** environment isolated from your system Python
- **Poetry** for dependency management across all three repositories (installed as vscode user)
- **Pre-installed VSCode extensions** for Python, Poetry, and testing
- **Development tools**: pytest, ruff, black, mypy, gh (GitHub CLI)
- **Convenient aliases** for common tasks

## Quick Start

1. **Open in Devcontainer** (VSCode):
   - Press `F1` → "Dev Containers: Reopen in Container"
   - Or click "Reopen in Container" when prompted

2. **First-time setup**:
   - The container will automatically run `post-create.sh`
   - This installs all Poetry dependencies for both sub-repositories
   - Takes ~2-3 minutes on first build

3. **Start developing**:
   ```bash
   mg-api        # Start Flask API server
   mg-test       # Run API tests
   mg-lint       # Run linter
   ```

## Repository Boundaries

⚠️ **CRITICAL**: MemoGarden has **three separate git repositories**:

```bash
/workspaces/memogarden                    # Root repo (docs, plans, scripts)
/workspaces/memogarden/memogarden-system  # System repo (db, utils) - SEPARATE GIT!
/workspaces/memogarden/memogarden-api     # API repo (Flask, tests) - SEPARATE GIT!
```

**Before committing, always check:**
```bash
pwd                    # Verify your directory
git status             # Check what will be committed
```

## Available Aliases

| Alias | Description |
|-------|-------------|
| `mg-api` | Start Flask API server (from memogarden-api) |
| `mg-test` | Run API tests (from memogarden-api) |
| `mg-test-system` | Run system tests (from memogarden-system) |
| `mg-lint` | Run ruff linter (from root) |
| `mg-status` | Show git status for all three repos |
| `mg-root` | Change to workspace root |

## Running Tests

### API Tests
```bash
cd /workspaces/memogarden/memogarden-api
poetry run pytest
# Or use alias:
mg-test
```

### System Tests
```bash
cd /workspaces/memogarden/memogarden-system
poetry run pytest
# Or use alias:
mg-test-system
```

### Specific Test File
```bash
cd /workspaces/memogarden/memogarden-api
poetry run pytest tests/test_transactions.py
```

## Development Workflow

1. **Make changes** to code in either sub-repo
2. **Run tests** in the corresponding repository
3. **Commit** in the specific repository (not root!)
4. **Repeat**

## Troubleshooting

### Container won't start
- Check Docker is running: `docker ps`
- Rebuild: `F1` → "Dev Containers: Rebuild Container"

### Poetry not found
- Restart the container
- Check `/home/vscode/.local/bin` is in PATH

### Tests fail with import errors
- Make sure you're in the correct repository directory
- Run `poetry install` to ensure dependencies are installed
- Check you're using the right Python: `which python`

### Git commits go to wrong repo
- Always check `pwd` before committing
- Use `git status` to verify what will be committed
- See [AGENTS.md](../AGENTS.md) for repository boundaries

## Ports Forwarded

- **5000**: Flask API (production)
- **5001**: Flask API (debug mode, if configured)

## VSCode Extensions Installed

- Python (ms-python.python)
- Even Better TOML (for pyproject.toml)
- Python Test Explorer (littlefoxteam.vscode-python-test-adapter)
- Pylance (ms-python.vscode-pylance)
- Debuggy (ms-python.debuggy)
- GitLens (eamodio.gitlens)

## File Structure

```
/devcontainer/
├── devcontainer.json    # Main VSCode devcontainer config
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Container image definition (system layer)
├── post-create.sh       # Setup script (user layer, runs on container create)
└── README.md            # This file
```

### Responsibility Split

| File | Runs As | When | What |
|------|---------|------|------|
| `Dockerfile` | root | Build time | System packages, global tools |
| `post-create.sh` | vscode | First start | Poetry, project deps, user config |
| `devcontainer.json` | - | VSCode UI | Extensions, settings, port forwarding |

**Note:** We don't use devcontainer "features" because they conflict with our manual Python 3.13 installation from the deadsnakes PPA (not available in the default features).

## Customization

To add more VSCode extensions, edit `devcontainer.json`:
```json
"extensions": [
  "ms-python.python",
  "your.extension.here"
]
```

To install global packages, edit `Dockerfile`:
```dockerfile
RUN pip3 install --no-cache-dir your-package-here
```

To add more aliases, edit `post-create.sh`:
```bash
alias mg-your-alias='your-command-here'
```
