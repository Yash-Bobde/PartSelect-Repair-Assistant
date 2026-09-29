"""
Products API Endpoints

Direct product search without agent
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.database import get_db_pool
import json

router = APIRouter()


class Product(BaseModel):
    """Product model"""
    part_number: str
    name: str
    description: Optional[str]
    category: str
    brand: Optional[str]
    price: float
    in_stock: bool
    rating: Optional[float]
    reviews_count: int
    image_urls: List[str]
    specifications: dict


@router.get("/products/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """
    Search products by keyword
    
    Fast product search without agent reasoning
    """
    
    try:
        pool = await get_db_pool()
        
        query = """
            SELECT 
                part_number, name, description, category, brand,
                price, in_stock, rating, reviews_count,
                image_urls, specifications
            FROM products
            WHERE search_vector @@ plainto_tsquery('english', $1)
        """
        
        params = [q]
        
        if category:
            query += " AND category = $2"
            params.append(category)
        
        query += f" ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC LIMIT {limit}"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        products = []
        for row in rows:
            product = dict(row)
            product['image_urls'] = json.loads(product['image_urls']) if product['image_urls'] else []
            product['specifications'] = json.loads(product['specifications']) if product['specifications'] else {}
            products.append(Product(**product))
        
        return products
    
    except Exception as e:
        print(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{part_number}", response_model=Product)
async def get_product(part_number: str):
    """
    Get product details by part number
    """
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    part_number, name, description, category, brand,
                    price, in_stock, rating, reviews_count,
                    image_urls, specifications
                FROM products
                WHERE part_number = $1
            """, part_number)
        
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = dict(row)
        product['image_urls'] = json.loads(product['image_urls']) if product['image_urls'] else []
        product['specifications'] = json.loads(product['specifications']) if product['specifications'] else {}
        
        return Product(**product)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{part_number}/installation")
async def get_installation_guide(part_number: str):
    """
    Get installation guide for a product
    """
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    difficulty, estimated_time_minutes,
                    tools_required, video_url, pdf_url
                FROM installation_guides
                WHERE part_number = $1
            """, part_number)
        
        if not row:
            raise HTTPException(status_code=404, detail="Installation guide not found")
        
        guide = dict(row)
        guide['tools_required'] = json.loads(guide['tools_required']) if guide['tools_required'] else []
        
        return guide
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving installation guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))