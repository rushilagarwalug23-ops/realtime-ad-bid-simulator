"""Ad request schemas."""
from pydantic import BaseModel, Field
from typing import Optional

class AdRequest(BaseModel):
    """Schema for an incoming ad request."""
    publisher_id: int
    slot_id: int
    user_geo: str = Field(..., min_length=2, max_length=2, description='ISO country code')
    user_interests: list[str] = Field(default_factory=list)
    page_category: str
    page_url: str = ''
    user_id: str = ''  # anonymous identifier

class AdRequestBatch(BaseModel):
    """Schema for a batch of ad requests."""
    requests: list[AdRequest]
