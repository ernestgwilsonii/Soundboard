#!/bin/bash
# Restore user data from a backup created by scripts/backup.sh.
# REPLACES the live databases and uploaded media, then restarts the app.
#
# Usage:   ./scripts/restore.sh <backup-directory>
#          FORCE=1 ./scripts/restore.sh <backup-directory>   # skip prompt
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP="${1:?Usage: $0 <backup-directory> (e.g. ~/soundboard-backups/20260609-031500)}"
BACKUP="$(realpath "$BACKUP")"

for f in accounts.sqlite3 soundboards.sqlite3 uploads.tar.gz; do
    [ -f "$BACKUP/$f" ] || { echo "ERROR: $BACKUP/$f not found" >&2; exit 1; }
done

echo "This will REPLACE the live databases and all uploaded media with:"
echo "  $BACKUP"
if [ "${FORCE:-0}" != "1" ]; then
    read -r -p "Type 'yes' to continue: " ANSWER
    [ "$ANSWER" = "yes" ] || { echo "Aborted."; exit 1; }
fi

echo "Stopping app..."
docker compose stop app

# Helper to run a shell in a one-off container with the data volumes attached
run_in_volumes() {
    docker compose run --rm --no-deps -T --entrypoint sh app -c "$1"
}

echo "Restoring databases..."
run_in_volumes 'cat > /app/data/accounts.sqlite3'    < "$BACKUP/accounts.sqlite3"
run_in_volumes 'cat > /app/data/soundboards.sqlite3' < "$BACKUP/soundboards.sqlite3"

echo "Restoring uploads..."
run_in_volumes 'find /app/app/static/uploads -mindepth 1 -delete && tar xzf - -C /app/app/static/uploads' \
    < "$BACKUP/uploads.tar.gz"

echo "Starting app..."
docker compose up -d app

echo "=== Restore complete from $BACKUP ==="
echo "Note: .env was NOT touched. If you are rebuilding a server, copy"
echo "      '$BACKUP/env' to .env in the repo root before 'make run'."
