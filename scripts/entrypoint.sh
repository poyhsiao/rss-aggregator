#!/bin/bash
set -e

DB_PATH="/app/data/rss.db"

run_migrations() {
    echo "Running database migrations..."
    uv run alembic upgrade head
}

init_db() {
    echo "Initializing database..."
    
    uv run python -c "
import sqlite3
import os
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = '/app/data/rss.db'
timezone_str = os.environ.get('APP_TIMEZONE', 'Asia/Taipei')
tz = ZoneInfo(timezone_str)
now = datetime.now(tz).replace(tzinfo=None).isoformat()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if api_keys table exists and has default key
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'\")
if cursor.fetchone():
    cursor.execute('SELECT key FROM api_keys WHERE key = ?', ('rss-aggregator-default-key-2024',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO api_keys (key, name, is_active, created_at, updated_at) VALUES (?, ?, 1, ?, ?)',
            ('rss-aggregator-default-key-2024', 'Default API Key', now, now))
        print('Created default API key')
else:
    print('api_keys table not found, skipping default key creation')

# Initialize default sources from environment
default_sources = os.environ.get('DEFAULT_SOURCES', '')
if default_sources:
    sources = [s.strip() for s in default_sources.split(',') if s.strip()]
    for i, url in enumerate(sources):
        cursor.execute('SELECT id FROM sources WHERE url = ?', (url,))
        if not cursor.fetchone():
            name = f'Source {i+1}'
            cursor.execute('INSERT INTO sources (name, url, fetch_interval, is_active, created_at, updated_at) VALUES (?, ?, 0, 1, ?, ?)',
                (name, url, now, now))
            print(f'Created source: {name} ({url})')

conn.commit()
conn.close()
print('Database initialization complete')
"
}

# Main startup logic
echo "Starting RSS Aggregator..."

# Check if database exists
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, checking integrity..."
    
    # Check if alembic_version table exists
    TABLE_COUNT=$(uv run python -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
print(len(cursor.fetchall()))
conn.close()
" 2>/dev/null || echo "0")
    
    if [ "$TABLE_COUNT" = "1" ]; then
        # Only alembic_version exists, database is corrupted
        echo "Database is incomplete, recreating..."
        rm -f "$DB_PATH"
        run_migrations
    else
        echo "Database looks ok, running migrations..."
        run_migrations
    fi
else
    echo "Database not found, creating..."
    run_migrations
fi

# Initialize default data
init_db

# Start the application
echo "Starting application..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000