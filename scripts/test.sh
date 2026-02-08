#!/bin/bash
# Run MemoGarden API test suite

cd "$(dirname "$0")/../memogarden-api"
poetry run pytest "$@"
