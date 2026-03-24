#!/usr/bin/env python3
"""Test script to verify Tauri App sidecar history query functionality."""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stdio.server import StdioServer


async def test_history_query():
    """Test history query through stdio server."""
    print("=== Starting Stdio Server ===\n")
    
    server = StdioServer()
    
    # Initialize database
    print("1. Initializing database...")
    await server._init_database()
    print("   Database initialized.\n")
    
    # Create test data
    print("2. Creating test data...")
    from src.db.database import async_session_factory
    from src.models import APIKey, FeedItem, FetchBatch, Source
    
    async with async_session_factory() as session:
        # Check if test data already exists
        from sqlalchemy import select
        result = await session.execute(select(FetchBatch))
        existing_batches = list(result.scalars().all())
        
        if existing_batches:
            print(f"   Found {len(existing_batches)} existing batches.")
        else:
            # Create API key
            api_key = APIKey(key="test-key-12345", name="Test Key", is_active=True)
            session.add(api_key)
            
            # Create source
            source = Source(name="BBC News", url="https://feeds.bbci.co.uk/news/rss.xml", is_active=True)
            session.add(source)
            await session.flush()
            
            # Create batch
            batch = FetchBatch(items_count=3, sources='["BBC News"]')
            session.add(batch)
            await session.flush()
            
            # Create items
            for i in range(3):
                item = FeedItem(
                    source_id=source.id,
                    batch_id=batch.id,
                    title=f"Test Article {i+1}",
                    link=f"https://bbc.com/article{i+1}",
                    description=f"Description for article {i+1}",
                )
                session.add(item)
            
            await session.commit()
            print("   Created test data: 1 batch with 3 items.\n")
    
    # Test history query
    print("3. Testing history query...")
    from src.stdio.protocol import JSONRPCRequest
    
    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="GET /api/v1/history/batches",
        params={"headers": {"X-API-Key": "test-key-12345"}, "query": {}},
        id=1,
    )
    
    response = await server._router.route(request)
    
    print(f"   Status: {response.result['status']}")
    body = response.result["body"]
    print(f"   Total batches: {body['total_batches']}")
    print(f"   Total items: {body['total_items']}")
    
    if body["batches"]:
        print(f"   First batch: ID={body['batches'][0]['id']}, Items={body['batches'][0]['items_count']}")
        
        # Test get items by batch
        batch_id = body["batches"][0]["id"]
        request2 = JSONRPCRequest(
            jsonrpc="2.0",
            method=f"GET /api/v1/history/batches/{batch_id}",
            params={"headers": {"X-API-Key": "test-key-12345"}, "query": {}},
            id=2,
        )
        
        response2 = await server._router.route(request2)
        body2 = response2.result["body"]
        print(f"\n   Items in batch {batch_id}:")
        for item in body2["items"]:
            print(f"     - {item['title']}")
    else:
        print("   No batches found!")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_history_query())