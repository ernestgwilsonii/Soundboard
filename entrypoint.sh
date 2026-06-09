#!/bin/bash
set -e

# Ensure data directory exists
mkdir -p /app/data

# Initialize databases if they don't exist
DB_PATH_ACCOUNTS=${ACCOUNTS_DB:-/app/data/accounts.sqlite3}
DB_PATH_SOUNDBOARDS=${SOUNDBOARDS_DB:-/app/data/soundboards.sqlite3}

echo "Checking databases..."

# Function to check if a table exists
table_exists() {
    local db=$1
    local table=$2
    if [ ! -f "$db" ]; then return 1; fi
    sqlite3 "$db" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" | grep -q "$table"
}

if ! table_exists "$DB_PATH_ACCOUNTS" "users" || ! table_exists "$DB_PATH_SOUNDBOARDS" "sounds"; then
    echo "One or more tables missing. Initializing Databases..."
    export ACCOUNTS_DB=$DB_PATH_ACCOUNTS
    export SOUNDBOARDS_DB=$DB_PATH_SOUNDBOARDS
    python3 manage.py
else
    echo "Databases already initialized."
fi

# Run any pending migrations
echo "Running migrations..."
# export ACCOUNTS_DB=$DB_PATH_ACCOUNTS
# export SOUNDBOARDS_DB=$DB_PATH_SOUNDBOARDS
# python3 migrate.py

# Execute the CMD from Dockerfile
exec "$@"
