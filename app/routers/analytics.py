"""Analytics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.schemas.bid_response import AnalyticsOverview, LatencyBucket, WinRateBucket

router = APIRouter(prefix='/api/v1/analytics', tags=['analytics'])

@router.get('/overview', response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Get aggregated analytics overview."""
    query = text("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN won THEN 1 ELSE 0 END) as total_wins,
            AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) as win_rate,
            AVG(CASE WHEN no_fill THEN 1.0 ELSE 0.0 END) as no_fill_rate,
            AVG(latency_ms) as avg_latency,
            AVG(CASE WHEN cache_hit THEN latency_ms END) as avg_cached,
            AVG(CASE WHEN NOT cache_hit THEN latency_ms END) as avg_uncached,
            AVG(CASE WHEN cache_hit THEN 1.0 ELSE 0.0 END) as cache_hit_rate,
            AVG(CASE WHEN won THEN bid_price ELSE 0 END) as avg_bid,
            SUM(CASE WHEN won THEN bid_price ELSE 0 END) as total_revenue
        FROM bid_logs
    """)
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row or (row.total_requests or 0) == 0:
        return AnalyticsOverview(
            total_requests=0, total_wins=0, win_rate=0.0, no_fill_rate=0.0,
            avg_latency_ms=0.0, avg_latency_cached_ms=0.0, avg_latency_uncached_ms=0.0,
            cache_hit_rate=0.0, avg_bid_price=0.0, total_revenue=0.0
        )
        
    return AnalyticsOverview(
        total_requests=row.total_requests or 0,
        total_wins=row.total_wins or 0,
        win_rate=float(row.win_rate or 0),
        no_fill_rate=float(row.no_fill_rate or 0),
        avg_latency_ms=float(row.avg_latency or 0),
        avg_latency_cached_ms=float(row.avg_cached or 0),
        avg_latency_uncached_ms=float(row.avg_uncached or 0),
        cache_hit_rate=float(row.cache_hit_rate or 0),
        avg_bid_price=float(row.avg_bid or 0),
        total_revenue=float(row.total_revenue or 0)
    )

@router.get('/latency', response_model=list[LatencyBucket])
async def get_latency(hours: int = 24, db: AsyncSession = Depends(get_db)):
    """Get latency metrics grouped by hour, dialect-aware."""
    bind = db.bind
    is_sqlite = bind and bind.dialect.name == "sqlite"
    
    if is_sqlite:
        query = text(f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', created_at) as time_bucket,
                AVG(latency_ms) as avg_latency_ms,
                AVG(CASE WHEN cache_hit THEN latency_ms END) as avg_cached_ms,
                AVG(CASE WHEN NOT cache_hit THEN latency_ms END) as avg_uncached_ms,
                COUNT(*) as request_count
            FROM bid_logs
            WHERE created_at >= datetime('now', '-{hours} hours')
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """)
    else:
        query = text(f"""
            SELECT 
                date_trunc('hour', created_at) as time_bucket,
                AVG(latency_ms) as avg_latency_ms,
                AVG(CASE WHEN cache_hit THEN latency_ms END) as avg_cached_ms,
                AVG(CASE WHEN NOT cache_hit THEN latency_ms END) as avg_uncached_ms,
                COUNT(*) as request_count
            FROM bid_logs
            WHERE created_at >= NOW() - INTERVAL '{hours} hours'
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """)
        
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        LatencyBucket(
            time_bucket=str(row.time_bucket),
            avg_latency_ms=float(row.avg_latency_ms or 0),
            avg_cached_ms=float(row.avg_cached_ms or 0),
            avg_uncached_ms=float(row.avg_uncached_ms or 0),
            request_count=row.request_count or 0
        ) for row in rows
    ]

@router.get('/win-rate', response_model=list[WinRateBucket])
async def get_win_rate(hours: int = 24, db: AsyncSession = Depends(get_db)):
    """Get win rate metrics grouped by hour, dialect-aware."""
    bind = db.bind
    is_sqlite = bind and bind.dialect.name == "sqlite"
    
    if is_sqlite:
        query = text(f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', created_at) as time_bucket,
                COUNT(*) as total,
                SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins,
                AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(CASE WHEN no_fill THEN 1 ELSE 0 END) as no_fills
            FROM bid_logs
            WHERE created_at >= datetime('now', '-{hours} hours')
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """)
    else:
        query = text(f"""
            SELECT 
                date_trunc('hour', created_at) as time_bucket,
                COUNT(*) as total,
                SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins,
                AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(CASE WHEN no_fill THEN 1 ELSE 0 END) as no_fills
            FROM bid_logs
            WHERE created_at >= NOW() - INTERVAL '{hours} hours'
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """)
        
    result = await db.execute(query)
    rows = result.fetchall()
    
    return [
        WinRateBucket(
            time_bucket=str(row.time_bucket),
            total=row.total or 0,
            wins=row.wins or 0,
            win_rate=float(row.win_rate or 0),
            no_fills=row.no_fills or 0
        ) for row in rows
    ]
