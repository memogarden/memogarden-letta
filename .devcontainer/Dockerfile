FROM mcr.microsoft.com/devcontainers/base:ubuntu

# =============================================================================
# MemoGarden Devcontainer - System Layer
# =============================================================================
#
# This Dockerfile installs SYSTEM-LEVEL packages that require root access.
#
# Responsibility split:
# - Dockerfile (this file): System packages, global tools, Python runtime
# - post-create.sh: User-specific tools (Poetry), project dependencies
#
# What goes here (as root):
# - System packages via apt (Python 3.13, build tools, git)
# - Global tools: gh (GitHub CLI), pip tools (pytest, ruff, black, mypy)
# - Python runtime configuration
#
# What does NOT go here:
# - Poetry (installed by post-create.sh for vscode user)
# - Project dependencies (installed by post-create.sh via poetry install)
# - User configuration (handled in post-create.sh)
#
# =============================================================================

# Install deadsnakes PPA for Python 3.13
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get -y install --no-install-recommends \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    python3-pip \
    build-essential \
    curl \
    git \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.13 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.13 1

# Install common development tools (globally via pip)
RUN pip3 install --no-cache-dir --ignore-installed \
    pytest==8.0.0 \
    pytest-flask==1.3.0 \
    pytest-cov==4.1.0 \
    black==24.1.1 \
    ruff==0.2.0 \
    mypy==1.8.0

# Install GitHub CLI (gh)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set default working directory
WORKDIR /workspace

# Verify installations (Poetry will be installed by post-create script for vscode user)
RUN python3 --version \
    && pytest --version \
    && gh --version

# The base image already has a vscode user, just ensure workspace ownership
RUN chown -R vscode:vscode /workspace

# Switch to vscode user (matches VSCode remote user)
USER vscode

# Set PATH for vscode user
# Includes system paths and user-local bin for Poetry (installed by post-create.sh)
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin:/home/vscode/.local/bin"
