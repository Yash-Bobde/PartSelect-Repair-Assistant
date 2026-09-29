"""
Agent Tools - Database and Search Functions

These are the agent's "hands" - how it interacts with data
"""

from typing import List, Dict, Optional
import asyncpg
from app.core.database import get_db_pool
from app.core.vector_store import get_chroma_client
from app.core.llm import get_llm_client
import json


class SearchTools:
    """
    Tools for searching products and knowledge base
    """
    
    def __init__(self):
        self.chroma_client = get_chroma_client()
        self.collection = self.chroma_client.get_collection("partselect_knowledge")
        self.llm = get_llm_client()
    
    async def search_products_by_keyword(
        self, 
        keyword: str, 
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search products using PostgreSQL full-text search
        
        Why full-text search? Fast for exact/partial matches
        """
        pool = await get_db_pool()
        
        query = """
            SELECT 
                part_number,
                name,
                description,
                category,
                brand,
                price,
                in_stock,
                rating,
                specifications
            FROM products
            WHERE search_vector @@ plainto_tsquery('english', $1)
        """
        
        params = [keyword]
        
        if category:
            query += " AND category = $2"
            params.append(category)
        
        query += f" ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC LIMIT {limit}"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def search_products_by_symptom(
        self,
        symptom: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search products that fix a specific symptom
        
        Strategy:
        1. Search ChromaDB for relevant troubleshooting docs
        2. Extract recommended part numbers
        3. Fetch full product details from PostgreSQL
        """
        
        # Semantic search in ChromaDB
        results = self.collection.query(
            query_texts=[symptom],
            n_results=20,
            where={"doc_type": "troubleshooting"} if not category else {
                "$and": [
                    {"doc_type": "troubleshooting"},
                    {"category": category}
                ]
            }
        )
        
        # Extract part numbers from results
        part_numbers = set()
        for metadata in results['metadatas'][0]:
            part_num = metadata.get('part_number')
            if part_num:
                part_numbers.add(part_num)
        
        if not part_numbers:
            return []
        
        # Fetch product details
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    part_number,
                    name,
                    description,
                    category,
                    brand,
                    price,
                    in_stock,
                    rating,
                    specifications
                FROM products
                WHERE part_number = ANY($1)
                LIMIT $2
            """, list(part_numbers), limit)
        
        return [dict(row) for row in rows]
    
    async def semantic_search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Semantic search across all documents
        
        Why semantic search? Understands "ice maker broken" = "ice machine not working"
        """
        
        where_filter = {"doc_type": doc_type} if doc_type else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        # Combine results with metadata
        docs = []
        for i in range(len(results['ids'][0])):
            docs.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return docs
    
    async def get_installation_guide(self, part_number: str) -> Optional[Dict]:
        """Get installation instructions for a part"""
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    difficulty,
                    estimated_time_minutes,
                    tools_required,
                    video_url,
                    pdf_url
                FROM installation_guides
                WHERE part_number = $1
            """, part_number)
        
        return dict(row) if row else None
    
    async def get_troubleshooting_info(
        self,
        symptom: str,
        appliance_type: Optional[str] = None
    ) -> List[Dict]:
        """Get troubleshooting guidance for a symptom"""
        
        pool = await get_db_pool()
        
        query = """
            SELECT 
                issue_title,
                symptoms,
                possible_causes,
                diagnostic_steps,
                recommended_parts,
                appliance_type,
                brand
            FROM troubleshooting_kb
            WHERE issue_title ILIKE $1
        """
        
        params = [f"%{symptom}%"]
        
        if appliance_type:
            query += " AND appliance_type = $2"
            params.append(appliance_type)
        
        query += " LIMIT 5"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def check_compatibility(
        self,
        part_number: str,
        model_number: str
    ) -> Optional[Dict]:
        """Check if a part is compatible with a model"""
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    compatible,
                    confidence_score,
                    notes
                FROM compatibility
                WHERE part_number = $1 AND model_number = $2
            """, part_number, model_number)
        
        return dict(row) if row else None
    
    async def get_product_details(self, part_number: str) -> Optional[Dict]:
        """Get full details for a specific product"""
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    part_number,
                    name,
                    description,
                    category,
                    brand,
                    price,
                    in_stock,
                    image_urls,
                    specifications,
                    rating,
                    reviews_count
                FROM products
                WHERE part_number = $1
            """, part_number)
        
        if not row:
            return None
        
        product = dict(row)
        
        # Parse JSON fields
        product['image_urls'] = json.loads(product['image_urls']) if product['image_urls'] else []
        product['specifications'] = json.loads(product['specifications']) if product['specifications'] else {}
        
        return product