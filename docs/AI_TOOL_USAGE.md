# AI Tool Usage Documentation

## Overview
This document records how AI coding assistants were used during the development of the Real-Time Ad Bid Simulator, what was accepted, modified, and rejected from their output.

## Tools Used
- **Claude (Anthropic)** — Primary AI coding assistant for architecture design, code generation, and review
- **GitHub Copilot** — Code completion during implementation

## What AI Generated vs What I Modified

### 1. Database Schema Design
**AI Suggested:** Basic tables without indexes, using `Integer` IDs only.
**What I Changed:**
- Added composite indexes on `bid_logs` for the specific query patterns I knew the analytics would need (`idx_bid_logs_slot_created`, `idx_bid_logs_campaign_won`, `idx_bid_logs_cache_latency`)
- Added partial indexes for active campaign lookups
- Changed from naive `DateTime` to `DateTime(timezone=True)` for proper timezone handling

**Why:** AI tools tend to generate "correct" schemas that work functionally but don't account for production query patterns. The index strategy had to be designed around the actual queries the analytics dashboard would run.

### 2. Scoring Algorithm
**AI Suggested:** Simple `bid_price × relevance` linear scoring.
**What I Changed:**
- Added the `quality_score` multiplier to penalize low-quality ads even with high bids
- Implemented tiered geo matching (exact match = 1.0, worldwide = 0.7, no match = 0.0) instead of binary
- Added interest overlap scoring as a bonus factor

**Why:** The simple model would let the highest bidder always win, which isn't how real ad auctions work. Quality score prevents advertiser gaming, and tiered matching is closer to how real DSPs work.

### 3. Caching Strategy
**AI Suggested:** Cache everything with a single TTL.
**What I Changed:**
- Implemented differentiated TTLs: publisher/slot configs (300s) vs campaign data (30s)
- Campaign cache key includes `{category}:{geo}:{slot_type}` for granularity
- Added cache-through pattern where DB results are written back to cache

**Why:** Publisher configs rarely change, but campaign budgets deplete in real-time. A single TTL would either cache stale budget data or invalidate stable configs too often. This is a classic engineering trade-off.

### 4. Auction Service Architecture
**AI Suggested:** Functional approach with standalone functions.
**What I Changed:**
- Refactored to class-based `AuctionService` with dependency injection (accepts `db` session)
- Separated scoring into its own module for testability
- Added comprehensive error handling and no-fill tracking

**Why:** The functional approach made testing harder and didn't allow for easy mocking of the DB layer. The class-based approach with DI is more testable and follows SOLID principles.

### 5. What I Rejected
- **ORM-based analytics queries**: AI generated SQLAlchemy ORM queries for the analytics endpoints. I rejected these in favor of raw SQL via `text()` because the ORM adds overhead for pure read/aggregate queries, and raw SQL is clearer for complex GROUP BY with CASE expressions.
- **In-memory caching with `lru_cache`**: AI suggested Python's `functools.lru_cache` as an alternative to Redis. Rejected because it doesn't work across multiple worker processes and can't be invalidated externally.
- **Automatic cache invalidation on write**: AI suggested invalidating all related cache keys whenever a campaign is updated. I kept manual invalidation simpler — the short TTL (30s) on campaigns means stale data self-corrects quickly, and the complexity of tracking all possible cache keys wasn't worth it for this use case.

## Key Takeaways
1. AI tools are excellent for boilerplate (CRUD routes, Pydantic schemas, basic SQLAlchemy models)
2. AI tools need human judgment for: index strategy, caching TTL design, scoring algorithm tuning
3. The biggest value was in accelerating the "known" patterns so I could focus on the "unknown" engineering decisions
4. Always review AI-generated SQL — it tends to be correct but not optimized
