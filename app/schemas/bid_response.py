"""Bid response and related schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BidResponse(BaseModel):
    """Schema for a bid response."""
    request_id: str
    won: bool
    campaign_id: Optional[int] = None
    advertiser: Optional[str] = None
    campaign_name: Optional[str] = None
    bid_price: Optional[float] = None
    creative_url: Optional[str] = None
    final_score: Optional[float] = None
    latency_ms: float
    cache_hit: bool
    no_fill: bool = False

class CampaignSchema(BaseModel):
    """Schema for campaign management."""
    id: Optional[int] = None
    advertiser_name: str
    campaign_name: str
    budget: float
    daily_budget: float
    spent: float = 0.0
    daily_spent: float = 0.0
    bid_price: float
    target_categories: list[str] = []
    target_geos: list[str] = []
    target_slot_types: list[str] = []
    creative_url: str = ''
    status: str = 'active'
    quality_score: float = 0.8
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    
    class Config:
        from_attributes = True

class PublisherSchema(BaseModel):
    """Schema for publisher management."""
    id: Optional[int] = None
    name: str
    domain: str
    category: str = ''
    config: dict = {}
    is_active: bool = True
    
    class Config:
        from_attributes = True

class SlotSchema(BaseModel):
    """Schema for slot management."""
    id: Optional[int] = None
    publisher_id: int
    slot_name: str
    slot_type: str  # banner, video, native
    width: int = 728
    height: int = 90
    floor_price: float = 0.5
    is_active: bool = True
    
    class Config:
        from_attributes = True

class AnalyticsOverview(BaseModel):
    """Schema for analytics overview."""
    total_requests: int
    total_wins: int
    win_rate: float
    no_fill_rate: float
    avg_latency_ms: float
    avg_latency_cached_ms: float
    avg_latency_uncached_ms: float
    cache_hit_rate: float
    avg_bid_price: float
    total_revenue: float

class LatencyBucket(BaseModel):
    """Schema for latency bucket."""
    time_bucket: str
    avg_latency_ms: float
    avg_cached_ms: float
    avg_uncached_ms: float
    request_count: int

class WinRateBucket(BaseModel):
    """Schema for win rate bucket."""
    time_bucket: str
    total: int
    wins: int
    win_rate: float
    no_fills: int
