"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import init_db
from app.cache import cache
from app.middleware.latency import LatencyMiddleware
from app.routers import bid, campaigns, publishers, analytics, health
import app.models  # noqa: F401 — Ensure all models are registered with Base.metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await cache.close()

app = FastAPI(
    title='Real-Time Ad Bid Simulator',
    description='Simulates real-time ad auction/bidding with caching layer',
    version='1.0.0',
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Latency tracking
app.add_middleware(LatencyMiddleware)

# Routers
app.include_router(bid.router)
app.include_router(campaigns.router)
app.include_router(publishers.router)
app.include_router(analytics.router)
app.include_router(health.router)

# Serve dashboard static files
dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard')
if os.path.exists(dashboard_dir):
    app.mount('/dashboard', StaticFiles(directory=dashboard_dir, html=True), name='dashboard')

@app.get('/')
def root():
    return {'message': 'Real-Time Ad Bid Simulator API', 'docs': '/docs', 'dashboard': '/dashboard'}
