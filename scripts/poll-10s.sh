#!/bin/bash
REPO_DIR="/tmp/sensen-backup"
while true; do
    cd "$REPO_DIR" 2>/dev/null && git pull >/dev/null 2>&1
    sleep 10
done
