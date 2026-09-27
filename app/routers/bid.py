"""Bid router endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.ad_request import AdRequest
from app.schemas.bid_response import BidResponse
from app.services.auction import AuctionService

router = APIRouter(prefix='/api/v1', tags=['bidding'])

@router.post('/bid', response_model=BidResponse)
async def submit_bid(ad_request: AdRequest, db: AsyncSession = Depends(get_db)):
    """Submit an ad request and receive a bid."""
    service = AuctionService(db)
    return await service.run_auction(ad_request, use_cache=True)

@router.post('/bid/no-cache', response_model=BidResponse)
async def submit_bid_no_cache(ad_request: AdRequest, db: AsyncSession = Depends(get_db)):
    """Submit an ad request bypassing the cache."""
    service = AuctionService(db)
    return await service.run_auction(ad_request, use_cache=False)
