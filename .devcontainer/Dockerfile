FROM mcr.microsoft.com/devcontainers/base:ubuntu

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

# Add Poetry to PATH globally
ENV PATH="/root/.local/bin:${PATH}"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true

# Install common development tools (globally via pip)
RUN pip3 install --no-cache-dir --ignore-installed \
    pytest==8.0.0 \
    pytest-flask==1.3.0 \
    pytest-cov==4.1.0 \
    black==24.1.1 \
    ruff==0.2.0 \
    mypy==1.8.0

# Set default working directory
WORKDIR /workspace

# Verify installations
RUN python3 --version \
    && poetry --version \
    && pytest --version

# The base image already has a vscode user, just ensure workspace ownership
RUN chown -R vscode:vscode /workspace

# Switch to vscode user (matches VSCode remote user)
USER vscode

# Add Poetry to PATH for vscode user
ENV PATH="${PATH}:/home/vscode/.local/bin"
