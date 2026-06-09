#!/bin/bash
# Consistent backup of all user data from the running Docker stack:
#   - accounts.sqlite3 / soundboards.sqlite3 (SQLite online backup API,
#     safe while the site is serving traffic)
#   - uploaded media files (sound files, images)
#   - .env runtime configuration (not in git; contains secrets)
#
# Backups are written to plain directories on the host filesystem so that
# host/instance snapshots (e.g. Lightsail) always contain a known-good copy.
#
# Usage:   ./scripts/backup.sh [backup_root]
# Env:     BACKUP_ROOT (default: $HOME/soundboard-backups)
#          KEEP_BACKUPS (default: 14 most recent backups kept)
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_ROOT="${1:-${BACKUP_ROOT:-$HOME/soundboard-backups}}"
KEEP="${KEEP_BACKUPS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"

echo "=== Soundboard backup -> $DEST ==="

if ! docker compose ps --status running app | grep -q app; then
    echo "ERROR: the 'app' container is not running; cannot take a backup." >&2
    exit 1
fi

mkdir -p "$DEST"
chmod 700 "$BACKUP_ROOT"

# 1. SQLite online backup (consistent even under concurrent writes)
for db in accounts soundboards; do
    docker compose exec -T app sqlite3 "/app/data/${db}.sqlite3" ".backup '/tmp/${db}.bak'"
    docker compose exec -T app cat "/tmp/${db}.bak" > "$DEST/${db}.sqlite3"
    docker compose exec -T app rm -f "/tmp/${db}.bak"
    # Verify the copy is a healthy database
    RESULT=$(docker compose exec -T app sh -c \
        "cat > /tmp/${db}.verify && sqlite3 /tmp/${db}.verify 'PRAGMA integrity_check;' && rm -f /tmp/${db}.verify" \
        < "$DEST/${db}.sqlite3")
    if [ "$RESULT" != "ok" ]; then
        echo "ERROR: integrity check failed for ${db}.sqlite3: $RESULT" >&2
        exit 1
    fi
    echo "  ${db}.sqlite3 backed up (integrity: ok)"
done

# 2. Uploaded media (streamed out of the uploads volume)
docker compose exec -T app tar czf - -C /app/app/static/uploads . > "$DEST/uploads.tar.gz"
echo "  uploads.tar.gz backed up ($(du -h "$DEST/uploads.tar.gz" | cut -f1))"

# 3. Runtime configuration (.env holds DOMAIN, OAuth secrets, SECRET_KEY)
if [ -f .env ]; then
    install -m 600 .env "$DEST/env"
    echo "  .env backed up"
fi

chmod 700 "$DEST"

# 4. Rotate: keep only the most recent $KEEP backups
ls -1dt "$BACKUP_ROOT"/*/ 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -rf

echo "=== Backup complete: $DEST ($(du -sh "$DEST" | cut -f1)) ==="
