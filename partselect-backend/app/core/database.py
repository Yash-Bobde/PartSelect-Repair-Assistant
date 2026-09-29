"""
Database Connection Pool

Manages PostgreSQL connections efficiently
"""

import asyncpg
from typing import Optional
from app.config import get_settings

settings = get_settings()

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool
    
    Why pooling? Reusing connections is much faster than creating new ones
    """
    global _db_pool
    
    if _db_pool is None:
        # Extract connection params from DATABASE_URL
        db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        _db_pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    
    return _db_pool


async def close_db_pool():
    """Close database pool on shutdown"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None