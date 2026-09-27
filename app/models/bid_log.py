"""Bid Log database model."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, Index
from app.database import Base

class BidLog(Base):
    """Bid Log model for tracking auction results and analytics."""
    __tablename__ = 'bid_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey('ad_slots.id'), nullable=False)
    publisher_id = Column(Integer, ForeignKey('publishers.id'), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)  # null if no fill
    bid_price = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    won = Column(Boolean, default=False)
    latency_ms = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False)
    no_fill = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_bid_logs_created_at', 'created_at'),
        Index('idx_bid_logs_slot_created', 'slot_id', 'created_at'),
        Index('idx_bid_logs_campaign_won', 'campaign_id', 'won'),
        Index('idx_bid_logs_cache_latency', 'cache_hit', 'latency_ms'),
    )
