#!/usr/bin/env python3
"""
Diagnostic script for Tauri App history query issue.

This script checks:
1. Database existence and structure
2. Test data presence
3. API functionality via JSON-RPC

Usage:
    uv run python scripts/diagnose_app.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path


async def check_database():
    """Check database existence and structure."""
    print("\n=== Database Check ===\n")

    # Check default database path for Tauri App
    home = Path.home()
    db_path = home / "Library" / "Application Support" / "RSS Aggregator" / "rss.db"

    print(f"Expected database path: {db_path}")

    if not db_path.exists():
        print("❌ Database file does not exist!")
        print("   This means the Tauri App has not been launched yet, or is using a different path.")
        return False

    print("✅ Database file exists")

    # Check database structure
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTables in database: {tables}")

    if "fetch_batches" not in tables:
        print("❌ fetch_batches table does not exist!")
        conn.close()
        return False

    print("✅ fetch_batches table exists")

    # Check columns in feed_items
    cursor.execute("PRAGMA table_info(feed_items)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nColumns in feed_items: {columns}")

    if "batch_id" not in columns:
        print("❌ batch_id column does not exist in feed_items!")
        conn.close()
        return False

    print("✅ batch_id column exists in feed_items")

    conn.close()
    return True


async def check_test_data():
    """Check if test data exists."""
    print("\n=== Test Data Check ===\n")

    home = Path.home()
    db_path = home / "Library" / "Application Support" / "RSS Aggregator" / "rss.db"

    if not db_path.exists():
        print("❌ Database does not exist, cannot check test data")
        return False

    import sqlite3

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check fetch_batches count
    cursor.execute("SELECT COUNT(*) FROM fetch_batches")
    batch_count = cursor.fetchone()[0]
    print(f"Fetch batches count: {batch_count}")

    if batch_count == 0:
        print("❌ No fetch batches in database!")
        conn.close()
        return False

    print("✅ Fetch batches exist")

    # Check feed_items with batch_id
    cursor.execute("SELECT COUNT(*) FROM feed_items WHERE batch_id IS NOT NULL")
    items_count = cursor.fetchone()[0]
    print(f"Feed items with batch_id: {items_count}")

    if items_count == 0:
        print("❌ No feed items with batch_id!")
        conn.close()
        return False

    print("✅ Feed items with batch_id exist")

    # Show sample data
    cursor.execute("""
        SELECT fb.id, fb.items_count, fb.created_at, COUNT(fi.id) as actual_items
        FROM fetch_batches fb
        LEFT JOIN feed_items fi ON fi.batch_id = fb.id
        GROUP BY fb.id
        ORDER BY fb.created_at DESC
        LIMIT 5
    """)
    batches = cursor.fetchall()
    print(f"\nSample batches:")
    for batch in batches:
        print(f"  Batch {batch[0]}: {batch[3]} items (expected {batch[1]})")

    conn.close()
    return True


async def check_jsonrpc_api():
    """Check API via JSON-RPC."""
    print("\n=== JSON-RPC API Check ===\n")

    try:
        from src.stdio.router import StdioRouter
        from src.stdio.protocol import JSONRPCRequest
        from src.db.database import async_session_factory
        from src.models import Base
        from sqlalchemy.ext.asyncio import create_async_engine

        # Use Tauri App database path
        home = Path.home()
        db_path = home / "Library" / "Application Support" / "RSS Aggregator" / "rss.db"
        db_url = f"sqlite+aiosqlite:///{db_path}"

        print(f"Connecting to database: {db_url}")

        # Create test engine
        from src.db.database import engine

        router = StdioRouter()

        # Test get_history_batches
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="GET /api/v1/history/batches",
            params={"query": {"limit": "10", "offset": "0"}},
            id=1
        )

        response = await router.route(request)

        if response.error:
            print(f"❌ API Error: {response.error}")
            return False

        result = response.result
        if result and result.get("status") == 200:
            body = result.get("body", {})
            batches = body.get("batches", [])
            total_batches = body.get("total_batches", 0)
            total_items = body.get("total_items", 0)

            print(f"✅ API Response: {total_batches} batches, {total_items} items")
            print(f"   First batch: {json.dumps(batches[0] if batches else {}, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected response: {result}")
            return False

    except Exception as e:
        print(f"❌ Error checking API: {e}")
        import traceback
        traceback.print_exc()
        return False


async def create_test_data():
    """Create test data if needed."""
    print("\n=== Creating Test Data ===\n")

    home = Path.home()
    db_path = home / "Library" / "Application Support" / "RSS Aggregator" / "rss.db"

    if not db_path.exists():
        print("Creating database directory...")
        db_path.parent.mkdir(parents=True, exist_ok=True)

    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables if not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fetch_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items_count INTEGER NOT NULL,
            sources TEXT NOT NULL,
            notes VARCHAR(500),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            deleted_at DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            url VARCHAR(500) NOT NULL UNIQUE,
            fetch_interval INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            last_fetched_at DATETIME,
            last_error TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            deleted_at DATETIME
        )
    """)

    # Check if batch_id column exists in feed_items
    cursor.execute("PRAGMA table_info(feed_items)")
    columns = [row[1] for row in cursor.fetchall()]

    if "batch_id" not in columns:
        print("Adding batch_id column to feed_items...")
        try:
            cursor.execute("ALTER TABLE feed_items ADD COLUMN batch_id INTEGER")
        except Exception as e:
            print(f"Note: {e}")

    # Create test source
    cursor.execute("SELECT id FROM sources WHERE url = 'https://test.example.com/feed'")
    if not cursor.fetchone():
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO sources (name, url, fetch_interval, is_active, created_at, updated_at)
            VALUES ('Test Source', 'https://test.example.com/feed', 1800, 1, ?, ?)
        """, (now, now))
        print("Created test source")

    source_id = cursor.execute("SELECT id FROM sources WHERE url = 'https://test.example.com/feed'").fetchone()[0]

    # Create test batch
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO fetch_batches (items_count, sources, created_at, updated_at)
        VALUES (3, '["Test Source"]', ?, ?)
    """, (now, now))
    batch_id = cursor.lastrowid
    print(f"Created test batch: {batch_id}")

    # Create test feed items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            title VARCHAR(500) NOT NULL,
            link VARCHAR(1000) NOT NULL UNIQUE,
            description TEXT,
            published_at DATETIME,
            fetched_at DATETIME NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            deleted_at DATETIME,
            batch_id INTEGER
        )
    """)

    for i in range(1, 4):
        cursor.execute("""
            INSERT OR IGNORE INTO feed_items 
            (source_id, title, link, description, published_at, fetched_at, created_at, updated_at, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id,
            f"Test Item {i}",
            f"https://test.example.com/item-{i}",
            f"Description for test item {i}",
            now,
            now,
            now,
            now,
            batch_id
        ))

    print(f"Created 3 test feed items")

    conn.commit()
    conn.close()

    print("✅ Test data created successfully!")
    return True


async def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("Tauri App History Query Diagnostic")
    print("=" * 60)

    # Check database
    db_ok = await check_database()

    if not db_ok:
        print("\n⚠️ Database issues found. Attempting to create test data...")
        await create_test_data()
        db_ok = await check_database()

    if db_ok:
        # Check test data
        data_ok = await check_test_data()

        if not data_ok:
            print("\n⚠️ No test data found. Creating test data...")
            await create_test_data()
            data_ok = await check_test_data()

        if data_ok:
            # Check API
            api_ok = await check_jsonrpc_api()

    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. If database is OK but API failed, restart the Tauri App")
    print("2. If database is empty, the test data has been created - restart the app")
    print("3. If still having issues, check Tauri App logs (View > Toggle Developer Tools)")


if __name__ == "__main__":
    asyncio.run(main())