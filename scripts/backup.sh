#!/bin/bash
# Linux Backup Script — Volume 5 QA & Hardening
# Creates tar archives of SQL database tables and local storage uploads.

BACKUP_DIR="storage/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

echo "[Backup] Starting backup collection..."

# Dump PostgreSQL (if pg_dump is available)
if command -v pg_dump &> /dev/null; then
    pg_dump -U nexora -h localhost -d nexora_ai > storage/database_backup.sql
    echo "[Backup] SQL Database dumped successfully."
else
    echo "[Backup] pg_dump tool missing. Skipping raw SQL dump."
fi

# Package files
tar -czf "$BACKUP_FILE" \
    --exclude="storage/backups" \
    storage/

echo "[Backup] Archive created successfully: $BACKUP_FILE"
