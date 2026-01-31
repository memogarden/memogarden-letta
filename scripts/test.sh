#!/bin/bash
# Run MemoGarden API test suite

cd /home/kureshii/memogarden/api
poetry run pytest "$@"
