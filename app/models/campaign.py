"""Campaign database model."""
from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, Date, func
from app.database import Base

class Campaign(Base):
    """Campaign model representing an advertiser's ad campaign."""
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True, index=True)
    advertiser_name = Column(String(255), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    budget = Column(Float, nullable=False)  # total budget
    daily_budget = Column(Float, nullable=False)
    spent = Column(Float, default=0.0)
    daily_spent = Column(Float, default=0.0)
    bid_price = Column(Float, nullable=False, index=True)  # max CPM bid
    target_categories = Column(JSON, default=[])  # e.g. ['tech', 'finance']
    target_geos = Column(JSON, default=[])  # e.g. ['US', 'UK', 'IN']
    target_slot_types = Column(JSON, default=[])  # e.g. ['banner', 'native']
    creative_url = Column(String(500))
    status = Column(String(50), default='active', index=True)  # active, paused, completed
    quality_score = Column(Float, default=0.8)  # 0.0 to 1.0
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
