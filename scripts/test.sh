#!/bin/bash
# Run MemoGarden Core test suite

cd /home/kureshii/memogarden/memogarden-core
poetry run pytest "$@"
