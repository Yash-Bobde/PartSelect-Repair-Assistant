"""
FastAPI Application - PartSelect Chat Agent

Main entry point for the API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.core.llm import close_llm_client
from app.core.database import close_db_pool

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown
    
    Why? Properly manage resources (DB connections, HTTP clients)
    """
    # Startup
    print("🚀 Starting PartSelect Chat Agent API...")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down...")
    await close_llm_client()
    await close_db_pool()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent chat agent for appliance parts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """
    Detailed health check
    
    Checks:
    - API is running
    - Database connection
    - ChromaDB connection
    - LLM availability
    """
    from app.core.database import get_db_pool
    from app.core.vector_store import get_chroma_client
    from app.core.llm import get_llm_client
    
    health = {
        "status": "healthy",
        "checks": {
            "api": "ok",
            "database": "unknown",
            "chromadb": "unknown",
            "llm": "unknown"
        }
    }
    
    # Check database
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Check ChromaDB
    try:
        chroma = get_chroma_client()
        chroma.heartbeat()
        health["checks"]["chromadb"] = "ok"
    except Exception as e:
        health["checks"]["chromadb"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Check LLM
    try:
        llm = get_llm_client()
        # Just checking if we can create the client
        health["checks"]["llm"] = "ok"
    except Exception as e:
        health["checks"]["llm"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    return health


# Import and include routers
from app.api import chat, products

app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["chat"])
app.include_router(products.router, prefix=settings.API_V1_PREFIX, tags=["products"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )