#!/bin/bash
# Run tests with coverage report

cd /home/kureshii/memogarden/api
poetry run pytest --cov=api --cov-report=term-missing "$@"
