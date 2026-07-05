#!/bin/bash
# Linux Restore Script — Volume 5 QA & Hardening
# Restores data from the specified tar archive.

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_file_path>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[Restore] Restoring data from $BACKUP_FILE..."

# Extract tar archive
tar -xzf "$BACKUP_FILE" -C ./

echo "[Restore] Restore completed successfully."
