#!/bin/bash
# backup.sh — Automated PostgreSQL backup with 7-day retention
# Schedule via cron: 0 2 * * * /path/to/scripts/backup.sh >> /var/log/db_backup.log 2>&1

set -euo pipefail  # Exit on error, unset variable, or pipe failure

CONTAINER_NAME="eu_ai_act_postgres"
DB_NAME="${POSTGRES_DB:-eu_ai_act_db}"
DB_USER="${POSTGRES_USER:-omar}"
BACKUP_DIR="/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/eu_ai_act_db_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container ${CONTAINER_NAME} is not running. Aborting." >&2
    exit 1
fi

echo "[$(date -Iseconds)] Starting backup of ${DB_NAME}..."

docker exec "$CONTAINER_NAME" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" --format=plain --no-password \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "[$(date -Iseconds)] Backup complete: ${BACKUP_FILE} (${BACKUP_SIZE})"

echo "[$(date -Iseconds)] Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "eu_ai_act_db_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
echo "[$(date -Iseconds)] Retention cleanup done."

if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty! Something went wrong." >&2
    exit 1
fi

echo "[$(date -Iseconds)] Backup verified successfully."
