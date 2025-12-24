#!/bin/bash
# Run tests with coverage report

cd /home/kureshii/memogarden/memogarden-core
poetry run pytest --cov=memogarden_core --cov-report=term-missing "$@"
