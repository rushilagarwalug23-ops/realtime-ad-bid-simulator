"""Publisher database model."""
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, func
from app.database import Base

class Publisher(Base):
    """Publisher model representing an entity that shows ads."""
    __tablename__ = 'publishers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), index=True)
    config = Column(JSON, default={})  # blocked_categories, floor_price_multiplier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
