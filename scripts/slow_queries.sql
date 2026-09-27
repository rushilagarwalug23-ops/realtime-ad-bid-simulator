-- ============================================================
-- QUERY OPTIMIZATION ANALYSIS
-- Real-Time Ad Bid Simulator
-- ============================================================

-- ============================================================
-- PROBLEM 1: Full Table Scan on bid_logs for Analytics
-- ============================================================

-- SLOW QUERY (no index on created_at + aggregation columns)
-- This does a sequential scan on millions of rows
EXPLAIN ANALYZE
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total,
    SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins,
    AVG(latency_ms) as avg_latency
FROM bid_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour;

-- OPTIMIZATION: Composite index on (created_at) already exists
-- But we can add a covering index:
CREATE INDEX idx_bid_logs_analytics 
    ON bid_logs (created_at, won, latency_ms, cache_hit);

-- After index: Seq Scan -> Index Scan, ~10x speedup


-- ============================================================
-- PROBLEM 2: Campaign Eligibility Query
-- ============================================================

-- SLOW: Full scan checking multiple conditions
EXPLAIN ANALYZE
SELECT * FROM campaigns
WHERE status = 'active'
  AND budget > spent
  AND daily_budget > daily_spent
  AND start_date <= CURRENT_DATE
  AND end_date >= CURRENT_DATE
  AND bid_price >= 1.50;

-- OPTIMIZATION: Partial index for active campaigns
CREATE INDEX idx_campaigns_active_eligible 
    ON campaigns (bid_price, start_date, end_date)
    WHERE status = 'active';

-- Also: composite index on the most selective columns
CREATE INDEX idx_campaigns_bid_dates 
    ON campaigns (status, bid_price, start_date, end_date);


-- ============================================================
-- PROBLEM 3: Win Rate per Campaign (reporting query)
-- ============================================================

-- SLOW: Aggregation across full bid_logs joining campaigns
EXPLAIN ANALYZE  
SELECT 
    c.advertiser_name,
    c.campaign_name,
    COUNT(*) as total_bids,
    SUM(CASE WHEN bl.won THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(CASE WHEN bl.won THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate_pct,
    ROUND(AVG(bl.latency_ms), 2) as avg_latency
FROM bid_logs bl
JOIN campaigns c ON bl.campaign_id = c.id
WHERE bl.created_at >= NOW() - INTERVAL '7 days'
GROUP BY c.advertiser_name, c.campaign_name
ORDER BY wins DESC;

-- OPTIMIZATION: Index on (campaign_id, won) already exists as idx_bid_logs_campaign_won
-- Add: covering index
CREATE INDEX idx_bid_logs_campaign_analytics
    ON bid_logs (campaign_id, created_at, won, latency_ms);


-- ============================================================
-- PROBLEM 4: Publisher Performance Dashboard
-- ============================================================

-- SLOW: Aggregating by publisher without proper index
EXPLAIN ANALYZE
SELECT 
    p.name as publisher_name,
    COUNT(*) as total_requests,
    SUM(CASE WHEN bl.won THEN 1 ELSE 0 END) as filled,
    SUM(CASE WHEN bl.no_fill THEN 1 ELSE 0 END) as no_fills,
    ROUND(AVG(bl.latency_ms), 2) as avg_latency,
    ROUND(SUM(CASE WHEN bl.won THEN bl.bid_price ELSE 0 END), 2) as revenue
FROM bid_logs bl
JOIN publishers p ON bl.publisher_id = p.id
WHERE bl.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY p.name
ORDER BY revenue DESC;

-- OPTIMIZATION:
CREATE INDEX idx_bid_logs_publisher_perf
    ON bid_logs (publisher_id, created_at)
    INCLUDE (won, no_fill, latency_ms, bid_price);


-- ============================================================
-- PROBLEM 5: Cache Hit Rate Analysis Over Time
-- ============================================================

-- SLOW: Scanning all logs to compute cache stats
EXPLAIN ANALYZE
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
    ROUND(AVG(CASE WHEN cache_hit THEN 1.0 ELSE 0.0 END) * 100, 2) as hit_rate_pct,
    ROUND(AVG(CASE WHEN cache_hit THEN latency_ms END), 2) as avg_cached_latency,
    ROUND(AVG(CASE WHEN NOT cache_hit THEN latency_ms END), 2) as avg_uncached_latency
FROM bid_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour;

-- OPTIMIZATION: The idx_bid_logs_cache_latency index helps here
-- But for time-series queries, a BRIN index on created_at is more efficient:
CREATE INDEX idx_bid_logs_created_brin ON bid_logs USING BRIN (created_at);

-- Combined with the existing idx_bid_logs_cache_latency, this gives
-- efficient time-range filtering + cache_hit access
