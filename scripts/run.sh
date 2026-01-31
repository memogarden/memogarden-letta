#!/bin/bash
# Start MemoGarden API development server

cd /home/kureshii/memogarden/api
poetry run flask --app api.main run --debug
