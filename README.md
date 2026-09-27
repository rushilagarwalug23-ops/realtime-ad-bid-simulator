# Real-Time Ad Bid Simulator

## Overview
The Real-Time Ad Bid Simulator is a robust backend system designed to simulate real-time bidding (RTB) auctions for digital advertising. It processes bid requests from publishers, evaluates eligible ad campaigns, applies relevance and quality scoring, and determines the winning bid with ultra-low latency.

## Architecture
```text
+-----------+        +-----------------+        +-------------+
| Publisher | -----> | FastAPI Backend | -----> | PostgreSQL  |
| Request   |        | (Auction Logic) |        | (DB)        |
+-----------+        +-----------------+        +-------------+
                            |
                            V
                        +---------+
                        |  Redis  |
                        | (Cache) |
                        +---------+
```
Components:
- **FastAPI**: Provides high-performance async API endpoints.
- **Redis**: Serves as a high-speed caching layer to reduce DB load and latency.
- **PostgreSQL**: Primary data store for publishers, campaigns, ad slots, and analytics logs.

## Features
- Real-time bid evaluation and auction resolution
- Advanced scoring algorithm combining relevance, quality, and bid price
- Comprehensive caching strategy for ultra-low latency
- Scalable architecture with async PostgreSQL access
- Realistic seed data generation for testing
- Benchmarking scripts to measure cache performance
- Detailed analytics logging

## Tech Stack
| Technology | Description | Why we use it |
|------------|-------------|---------------|
| FastAPI | Web Framework | Extremely fast, async native, auto-generates OpenAPI docs |
| PostgreSQL | Database | Robust relational data modeling, great JSON support |
| Redis | Cache | In-memory key-value store for sub-millisecond lookups |
| SQLAlchemy | ORM | Mature ORM with async support |
| pytest | Testing | Simple and powerful testing framework |

## Quick Start
1. **Prerequisites**: Docker, Python 3.11+
2. **Clone repo**: `git clone <repo>`
3. **Start infrastructure**: `docker-compose up -d` (starts Postgres + Redis)
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Setup environment**: `cp .env.example .env`
6. **Seed data**: `python scripts/seed_data.py`
7. **Start server**: `uvicorn app.main:app --reload`
8. **Swagger UI**: Open http://localhost:8000/docs
9. **Dashboard**: Open http://localhost:8000/dashboard

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check endpoint |
| POST | `/api/v1/bid` | Submit a bid request (uses cache) |
| POST | `/api/v1/bid/no-cache` | Submit a bid request (bypasses cache) |
| GET | `/api/v1/campaigns` | List active campaigns |

## Auction Algorithm
The auction determines the winner using a composite score formula:
`final_score = relevance_score × bid_price × quality_score`
- **Relevance Score**: Evaluates category, geo-targeting, and interest overlap. Exact matches score 1.0, run-of-network scores 0.5, and mismatches score 0.0.
- **Quality Score**: Multiplier (0.3 to 1.0) to penalize low-quality ads despite high bids.

## Caching Strategy
Redis is used with differentiated TTLs:
- **Publisher/Slot Configs**: Cached for 300 seconds as they change infrequently.
- **Campaign Data**: Cached for 30 seconds to reflect real-time budget depletion.
Keys are structured for granular invalidation, e.g., `{category}:{geo}:{slot_type}`.

## Query Optimization
Complex analytics queries are optimized using appropriate PostgreSQL indexes (composite, partial, and covering indexes). See [scripts/slow_queries.sql](scripts/slow_queries.sql) for detailed BEFORE/AFTER analysis of slow queries.

## Benchmarking
Run the benchmarking script to compare cached vs uncached latency:
```bash
python scripts/benchmark.py --requests 200 --concurrency 10 --base-url http://localhost:8000
```
This generates a detailed report of min, max, mean, median, p95, p99 latencies, and speedup factor.

## Testing
Run unit and integration tests using pytest:
```bash
pytest tests/
```

## Project Structure
```text
.
├── .env.example
├── docker-compose.yml
├── requirements.txt
├── README.md
├── docs/
│   └── AI_TOOL_USAGE.md
├── scripts/
│   ├── benchmark.py
│   ├── seed_data.py
│   └── slow_queries.sql
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_auction.py
    └── test_scoring.py
```

## AI Tool Usage
See [docs/AI_TOOL_USAGE.md](docs/AI_TOOL_USAGE.md) for details on how AI assistants were used and the engineering judgments applied to their output.

## Engineering Trade-offs
- **TTL-based cache invalidation over event-driven**: Short TTLs (30s) are simpler to implement and self-correct quickly, avoiding the complexity of tracking and invalidating all possible cache keys on write.
- **Raw SQL for analytics vs ORM**: SQLAlchemy ORM adds overhead for pure read/aggregate queries. Raw SQL is clearer and more performant for complex GROUP BY statements.
- **Async Python over Node.js**: Python's ecosystem provides better data science and analytics tools, while async capabilities (FastAPI/asyncpg) offer competitive performance for I/O bound tasks.
- **First-price vs Second-price auction**: Implemented first-price for simplicity, though second-price is more realistic in RTB. This trade-off prioritizes readability and ease of implementation for the simulator.
