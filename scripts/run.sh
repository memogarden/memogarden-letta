#!/bin/bash
# Start MemoGarden Core API development server

cd /home/kureshii/memogarden/memogarden-core
poetry run flask --app memogarden_core.main run --debug
