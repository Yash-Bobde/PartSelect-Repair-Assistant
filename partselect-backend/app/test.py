"""
Final working test for Docker services
"""

import asyncio
import asyncpg
import redis.asyncio as redis
import httpx


async def test_postgresql():
    """Test PostgreSQL"""
    print("🔍 Testing PostgreSQL...")
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='partselect'
        )
        
        # THIS IS THE FIX - use pg_catalog instead of information_schema
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        table_names = [t['tablename'] for t in tables]
        
        print(f"  ✅ PostgreSQL connected")
        print(f"     Tables found: {len(table_names)}")
        
        # Count products
        count = await conn.fetchval("SELECT COUNT(*) FROM products")
        print(f"     Products: {count}")
        
        if count > 0:
            products = await conn.fetch(
                "SELECT part_number, name, price FROM products LIMIT 2"
            )
            print(f"     Samples:")
            for p in products:
                print(f"       - {p['part_number']}: {p['name']} (${p['price']})")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_redis():
    """Test Redis"""
    print("\n🔍 Testing Redis...")
    
    try:
        client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await client.set('test', 'ok', ex=10)
        value = await client.get('test')
        await client.aclose()
        
        print(f"  ✅ Redis connected")
        print(f"     Test: {value}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def test_chromadb():
    """Test ChromaDB"""
    print("\n🔍 Testing ChromaDB...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/v2/heartbeat")
            
            if response.status_code == 200:
                print(f"  ✅ ChromaDB connected (v2 API)")
                return True
            else:
                print(f"  ⚠️  Status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


async def main():
    print("=" * 60)
    print("🧪 Testing Docker Services")
    print("=" * 60)
    print()
    
    results = {
        "PostgreSQL": await test_postgresql(),
        "Redis": await test_redis(),
        "ChromaDB": await test_chromadb()
    }
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    for service, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {service}")
    
    if all(results.values()):
        print("\n" + "🎉" * 20)
        print("ALL SERVICES READY!")
        print("🎉" * 20)
        print("\nYour infrastructure is fully set up!")
        print("\n📋 Next Steps:")
        print("  1. ✅ Docker infrastructure - DONE")
        print("  2. ⏭️  Process scraped data")
        print("  3. ⏭️  Load data to databases")
        print("  4. ⏭️  Build LangGraph agent")
        print("  5. ⏭️  Create API endpoints")
        print("  6. ⏭️  Connect React frontend")
        print("\nReady to continue? 🚀")
    else:
        print("\n⚠️  Fix failed services")


if __name__ == "__main__":
    asyncio.run(main())