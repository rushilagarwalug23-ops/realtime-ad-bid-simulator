"""Ad Slot database model."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from app.database import Base

class AdSlot(Base):
    """Ad Slot model representing a placement on a publisher's site."""
    __tablename__ = 'ad_slots'
    id = Column(Integer, primary_key=True, index=True)
    publisher_id = Column(Integer, ForeignKey('publishers.id'), nullable=False, index=True)
    slot_name = Column(String(255), nullable=False)
    slot_type = Column(String(50), nullable=False, index=True)  # banner, video, native
    width = Column(Integer)
    height = Column(Integer)
    floor_price = Column(Float, default=0.5)  # minimum CPM
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
