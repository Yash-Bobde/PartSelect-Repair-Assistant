"""
Load processed data into PostgreSQL and ChromaDB
Fixed to handle foreign key violations
"""

import asyncio
import asyncpg
import pandas as pd
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import sys

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings

settings = get_settings()


async def load_products(conn: asyncpg.Connection, df: pd.DataFrame):
    """Load products into PostgreSQL"""
    print("\n📦 Loading products to PostgreSQL...")
    
    records = []
    for _, row in df.iterrows():
        records.append((
            row['part_number'],
            row['name'],
            row['description'],
            row['category'],
            float(row['price']),
            bool(row['in_stock']),
            row['image_urls'],  # Already JSON string
            row['specifications'],  # Already JSON string
            float(row['rating']) if pd.notna(row['rating']) else None,
            int(row['reviews_count']),
            row['brand'] if pd.notna(row['brand']) else None
        ))
    
    # Bulk insert with conflict handling
    await conn.executemany('''
        INSERT INTO products (
            part_number, name, description, category, price,
            in_stock, image_urls, specifications, rating, reviews_count, brand
        ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11)
        ON CONFLICT (part_number) DO UPDATE SET
            name = EXCLUDED.name,
            price = EXCLUDED.price,
            in_stock = EXCLUDED.in_stock,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP
    ''', records)
    
    print(f"✓ Loaded {len(records)} products")


async def load_installation_guides(conn: asyncpg.Connection, df: pd.DataFrame):
    """Load installation guides - only for parts that exist in products table"""
    print("\n🔧 Loading installation guides...")
    
    if len(df) == 0:
        print("  (No guides to load)")
        return
    
    # Get list of valid part numbers from products table
    print("  Checking valid part numbers...")
    valid_parts = await conn.fetch("SELECT part_number FROM products")
    valid_part_numbers = set(row['part_number'] for row in valid_parts)
    
    # Filter guides to only include those with valid part numbers
    original_count = len(df)
    df_filtered = df[df['part_number'].isin(valid_part_numbers)].copy()
    filtered_count = len(df_filtered)
    
    if filtered_count < original_count:
        skipped = original_count - filtered_count
        print(f"  ⚠️  Skipped {skipped} guides (parts not in products table)")
    
    if len(df_filtered) == 0:
        print("  (No valid guides to load)")
        return
    
    records = []
    for _, row in df_filtered.iterrows():
        records.append((
            row['part_number'],
            row['difficulty'],
            int(row['estimated_time_minutes']) if pd.notna(row['estimated_time_minutes']) else None,
            row['tools_required'],  # Already JSON string
            row['video_url'] if pd.notna(row['video_url']) else None,
            row['pdf_url'] if pd.notna(row['pdf_url']) else None,
            row['chromadb_doc_id']
        ))
    
    await conn.executemany('''
        INSERT INTO installation_guides (
            part_number, difficulty, estimated_time_minutes,
            tools_required, video_url, pdf_url, chromadb_doc_id
        ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
        ON CONFLICT DO NOTHING
    ''', records)
    
    print(f"✓ Loaded {len(records)} installation guides")


async def load_troubleshooting_kb(conn: asyncpg.Connection, df: pd.DataFrame):
    """Load troubleshooting knowledge base - filter to only valid parts"""
    print("\n🔍 Loading troubleshooting KB...")
    
    if len(df) == 0:
        print("  (No KB entries to load)")
        return
    
    # Get list of valid part numbers
    print("  Checking valid part numbers...")
    valid_parts = await conn.fetch("SELECT part_number FROM products")
    valid_part_numbers = set(row['part_number'] for row in valid_parts)
    
    # Filter recommended parts in KB entries
    filtered_entries = []
    for _, row in df.iterrows():
        # Parse recommended parts
        try:
            recommended = json.loads(row['recommended_parts']) if isinstance(row['recommended_parts'], str) else row['recommended_parts']
        except:
            recommended = []
        
        # Filter to only valid parts
        valid_recommended = [p for p in recommended if p in valid_part_numbers]
        
        # Only include entry if it has at least one valid part
        if valid_recommended:
            filtered_entries.append({
                'appliance_type': row['appliance_type'],
                'brand': row['brand'] if pd.notna(row['brand']) else None,
                'issue_title': row['issue_title'],
                'symptoms': row['symptoms'],
                'possible_causes': row['possible_causes'],
                'diagnostic_steps': row['diagnostic_steps'],
                'recommended_parts': json.dumps(valid_recommended),
                'chromadb_doc_id': row['chromadb_doc_id']
            })
    
    original_count = len(df)
    filtered_count = len(filtered_entries)
    
    if filtered_count < original_count:
        skipped = original_count - filtered_count
        print(f"  ⚠️  Skipped {skipped} entries (no valid parts)")
    
    if len(filtered_entries) == 0:
        print("  (No valid KB entries to load)")
        return
    
    records = []
    for entry in filtered_entries:
        records.append((
            entry['appliance_type'],
            entry['brand'],
            entry['issue_title'],
            entry['symptoms'],
            entry['possible_causes'],
            entry['diagnostic_steps'],
            entry['recommended_parts'],
            entry['chromadb_doc_id']
        ))
    
    await conn.executemany('''
        INSERT INTO troubleshooting_kb (
            appliance_type, brand, issue_title, symptoms,
            possible_causes, diagnostic_steps, recommended_parts, chromadb_doc_id
        ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8)
        ON CONFLICT DO NOTHING
    ''', records)
    
    print(f"✓ Loaded {len(records)} troubleshooting entries")


def load_chromadb_documents(df: pd.DataFrame, valid_part_numbers: set):
    """Load documents into ChromaDB - only for valid parts"""
    print("\n📝 Loading documents to ChromaDB...")
    
    # Filter to only documents for valid parts
    original_count = len(df)
    df_filtered = df[df['part_number'].isin(valid_part_numbers)].copy()
    filtered_count = len(df_filtered)
    
    if filtered_count < original_count:
        skipped = original_count - filtered_count
        print(f"  ⚠️  Skipped {skipped} docs (parts not in products table)")
    
    # Remove duplicate doc_ids
    before_dedup = len(df_filtered)
    df_filtered = df_filtered.drop_duplicates(subset=['doc_id'], keep='first')
    after_dedup = len(df_filtered)
    
    if after_dedup < before_dedup:
        dupes = before_dedup - after_dedup
        print(f"  ⚠️  Removed {dupes} duplicate documents")
    
    if len(df_filtered) == 0:
        print("  (No valid documents to load)")
        return
    
    # Connect to ChromaDB
    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Delete existing collection if it exists (fresh start)
    try:
        client.delete_collection(name=settings.CHROMA_COLLECTION)
        print("  ✓ Deleted existing collection")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Load embedding model
    print("  Loading embedding model...")
    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    print("  ✓ Model loaded")
    
    # Process in batches
    batch_size = 100
    total_docs = len(df_filtered)
    
    print(f"  Processing {total_docs} documents in batches of {batch_size}...")
    
    for i in range(0, total_docs, batch_size):
        batch = df_filtered.iloc[i:i+batch_size]
        
        # Prepare data
        ids = batch['doc_id'].tolist()
        documents = batch['content'].tolist()
        
        # Parse metadata and clean it for ChromaDB
        metadatas = []
        for _, row in batch.iterrows():
            # Parse stored metadata
            try:
                meta = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
            except:
                meta = {}
            
            # ChromaDB only allows: str, int, float, bool, None
            # Convert lists and dicts to strings
            clean_meta = {}
            for key, value in meta.items():
                if isinstance(value, list):
                    # Convert list to comma-separated string
                    clean_meta[key] = ", ".join(str(v) for v in value) if value else ""
                elif isinstance(value, dict):
                    # Convert dict to JSON string
                    clean_meta[key] = json.dumps(value)
                elif value is None:
                    clean_meta[key] = None
                elif isinstance(value, (str, int, float, bool)):
                    clean_meta[key] = value
                else:
                    # Convert anything else to string
                    clean_meta[key] = str(value)
            
            # Add doc_type and part_number (already primitives)
            clean_meta['doc_type'] = str(row['doc_type'])
            clean_meta['part_number'] = str(row['part_number'])
            
            metadatas.append(clean_meta)
        
        # Generate embeddings
        embeddings = embedding_model.encode(documents, show_progress_bar=False).tolist()
        
        # Add to ChromaDB
        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            batch_num = i//batch_size + 1
            total_batches = (total_docs-1)//batch_size + 1
            print(f"  ✓ Batch {batch_num}/{total_batches} ({len(batch)} docs)")
            
        except Exception as e:
            print(f"  ❌ Error in batch {i//batch_size + 1}: {e}")
            print(f"     First ID: {ids[0] if ids else 'none'}")
            print(f"     Sample metadata: {metadatas[0] if metadatas else 'none'}")
            raise
    
    print(f"✓ Loaded {total_docs} documents to ChromaDB")


async def verify_data():
    """Verify data was loaded correctly"""
    print("\n" + "=" * 60)
    print("🔍 Verifying Data Load")
    print("=" * 60)
    
    # PostgreSQL verification
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    products_count = await conn.fetchval("SELECT COUNT(*) FROM products")
    guides_count = await conn.fetchval("SELECT COUNT(*) FROM installation_guides")
    kb_count = await conn.fetchval("SELECT COUNT(*) FROM troubleshooting_kb")
    
    print(f"\n✅ PostgreSQL:")
    print(f"  Products: {products_count}")
    print(f"  Installation guides: {guides_count}")
    print(f"  Troubleshooting KB: {kb_count}")
    
    # Sample products by category
    fridge_count = await conn.fetchval("SELECT COUNT(*) FROM products WHERE category = 'refrigerator'")
    dish_count = await conn.fetchval("SELECT COUNT(*) FROM products WHERE category = 'dishwasher'")
    
    print(f"\n  By category:")
    print(f"    Refrigerator parts: {fridge_count}")
    print(f"    Dishwasher parts: {dish_count}")
    
    # Sample products
    samples = await conn.fetch("""
        SELECT part_number, name, price, category, brand
        FROM products 
        ORDER BY RANDOM()
        LIMIT 3
    """)
    
    print(f"\n  Sample products:")
    for s in samples:
        print(f"    • [{s['category']}] {s['part_number']}: {s['name']}")
        print(f"      ${s['price']} - {s['brand']}")
    
    await conn.close()
    
    # ChromaDB verification
    try:
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        
        collection = client.get_collection(settings.CHROMA_COLLECTION)
        chroma_count = collection.count()
        
        print(f"\n✅ ChromaDB:")
        print(f"  Total documents: {chroma_count}")
        
        # Test search
        test_queries = [
            "ice maker not working",
            "dishwasher not cleaning",
            "water filter"
        ]
        
        print(f"\n  Test searches:")
        for query in test_queries:
            results = collection.query(
                query_texts=[query],
                n_results=2
            )
            
            print(f"\n    '{query}':")
            for i, doc in enumerate(results['documents'][0]):
                doc_type = results['metadatas'][0][i].get('doc_type', 'unknown')
                print(f"      {i+1}. [{doc_type}] {doc[:70]}...")
        
    except Exception as e:
        print(f"\n⚠️  ChromaDB verification failed: {e}")


async def main():
    """Main loading pipeline"""
    print("=" * 60)
    print("🚀 Loading Processed Data to Databases")
    print("=" * 60)
    
    # Check processed files exist
    processed_dir = Path("data/processed")
    required_files = [
        "products.csv",
        "installation_guides.csv",
        "troubleshooting_kb.csv",
        "chromadb_documents.csv"
    ]
    
    for filename in required_files:
        filepath = processed_dir / filename
        if not filepath.exists():
            print(f"❌ Missing file: {filepath}")
            print("\nRun 'python scripts/process_combined.py' first!")
            return
    
    # Load CSVs
    print("\n📂 Loading processed CSV files...")
    products_df = pd.read_csv("data/processed/products.csv")
    guides_df = pd.read_csv("data/processed/installation_guides.csv")
    kb_df = pd.read_csv("data/processed/troubleshooting_kb.csv")
    docs_df = pd.read_csv("data/processed/chromadb_documents.csv")
    
    print(f"  ✓ Products: {len(products_df)}")
    print(f"  ✓ Installation guides: {len(guides_df)}")
    print(f"  ✓ Troubleshooting KB: {len(kb_df)}")
    print(f"  ✓ ChromaDB documents: {len(docs_df)}")
    
    # Connect to PostgreSQL
    print("\n🔌 Connecting to PostgreSQL...")
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Load products first (they have no foreign keys)
        await load_products(conn, products_df)
        
        # Load installation guides (references products)
        await load_installation_guides(conn, guides_df)
        
        # Load troubleshooting KB (references products in recommended_parts)
        await load_troubleshooting_kb(conn, kb_df)
        
        print("\n✓ PostgreSQL loading complete!")
    
    except Exception as e:
        print(f"\n❌ Error loading to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        await conn.close()
        return
    
    finally:
        await conn.close()
    
    # Get valid part numbers for ChromaDB filtering
    print("\n📋 Getting valid part numbers for ChromaDB...")
    conn = await asyncpg.connect(db_url)
    valid_parts = await conn.fetch("SELECT part_number FROM products")
    valid_part_numbers = set(row['part_number'] for row in valid_parts)
    await conn.close()
    
    print(f"  ✓ Found {len(valid_part_numbers)} valid parts")
    
    # Load to ChromaDB with filtering
    try:
        load_chromadb_documents(docs_df, valid_part_numbers)
    except Exception as e:
        print(f"\n❌ Error loading to ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verify everything loaded
    await verify_data()
    
    print("\n" + "=" * 60)
    print("🎉 All Data Loaded Successfully!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("  1. ✅ Docker infrastructure - DONE")
    print("  2. ✅ Data processing - DONE")
    print("  3. ✅ Data loading - DONE")
    print("  4. ⏭️  Build LangGraph agent")
    print("  5. ⏭️  Create API endpoints")
    print("  6. ⏭️  Connect React frontend")
    print("\nReady to build the agent! 🚀")


if __name__ == "__main__":
    asyncio.run(main())