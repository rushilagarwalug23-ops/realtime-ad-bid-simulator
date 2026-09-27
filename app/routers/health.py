"""Health check endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.cache import cache

router = APIRouter(prefix='/api/v1/health', tags=['health'])

@router.get('')
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check database and Redis connectivity."""
    db_status = "ok"
    redis_status = "ok"
    
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        
    try:
        if not await cache.ping():
            redis_status = "error"
    except Exception:
        redis_status = "error"
        
    status = "ok" if db_status == "ok" and redis_status == "ok" else "error"
    
    return {
        "status": status,
        "database": db_status,
        "redis": redis_status
    }
