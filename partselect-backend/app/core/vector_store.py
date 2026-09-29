"""
ChromaDB Vector Store Client

Handles semantic search with embeddings
"""

import chromadb
from chromadb.config import Settings
from typing import Optional
from app.config import get_settings

settings = get_settings()

# Global ChromaDB client
_chroma_client: Optional[chromadb.HttpClient] = None


def get_chroma_client() -> chromadb.HttpClient:
    
    global _chroma_client
    
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False)
        )
    
    return _chroma_client


def close_chroma_client():
    """Close ChromaDB client"""
    global _chroma_client
    # HTTP client doesn't need explicit closing
    _chroma_client = None