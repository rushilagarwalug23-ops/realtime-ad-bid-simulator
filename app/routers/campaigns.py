"""Campaigns router endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.campaign import Campaign
from app.schemas.bid_response import CampaignSchema

router = APIRouter(prefix='/api/v1/campaigns', tags=['campaigns'])

@router.get('', response_model=list[CampaignSchema])
async def list_campaigns(status: str = None, db: AsyncSession = Depends(get_db)):
    """List all campaigns, optionally filtering by status."""
    query = select(Campaign)
    if status:
        query = query.where(Campaign.status == status)
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    # Format dates to string for response
    for c in campaigns:
        c.start_date = c.start_date.strftime('%Y-%m-%d') if c.start_date else ''
        c.end_date = c.end_date.strftime('%Y-%m-%d') if c.end_date else ''
    return campaigns

@router.post('', response_model=CampaignSchema)
async def create_campaign(campaign: CampaignSchema, db: AsyncSession = Depends(get_db)):
    """Create a new campaign."""
    start_date = datetime.strptime(campaign.start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(campaign.end_date, '%Y-%m-%d').date()
    
    new_campaign = Campaign(
        advertiser_name=campaign.advertiser_name,
        campaign_name=campaign.campaign_name,
        budget=campaign.budget,
        daily_budget=campaign.daily_budget,
        bid_price=campaign.bid_price,
        target_categories=campaign.target_categories,
        target_geos=campaign.target_geos,
        target_slot_types=campaign.target_slot_types,
        creative_url=campaign.creative_url,
        status=campaign.status,
        quality_score=campaign.quality_score,
        start_date=start_date,
        end_date=end_date
    )
    db.add(new_campaign)
    await db.commit()
    await db.refresh(new_campaign)
    new_campaign.start_date = new_campaign.start_date.strftime('%Y-%m-%d')
    new_campaign.end_date = new_campaign.end_date.strftime('%Y-%m-%d')
    return new_campaign

@router.get('/{id}', response_model=CampaignSchema)
async def get_campaign(id: int, db: AsyncSession = Depends(get_db)):
    """Get a campaign by ID."""
    result = await db.execute(select(Campaign).where(Campaign.id == id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.start_date = campaign.start_date.strftime('%Y-%m-%d')
    campaign.end_date = campaign.end_date.strftime('%Y-%m-%d')
    return campaign

@router.put('/{id}', response_model=CampaignSchema)
async def update_campaign(id: int, campaign_update: CampaignSchema, db: AsyncSession = Depends(get_db)):
    """Update an existing campaign."""
    result = await db.execute(select(Campaign).where(Campaign.id == id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.advertiser_name = campaign_update.advertiser_name
    campaign.campaign_name = campaign_update.campaign_name
    campaign.budget = campaign_update.budget
    campaign.daily_budget = campaign_update.daily_budget
    campaign.bid_price = campaign_update.bid_price
    campaign.target_categories = campaign_update.target_categories
    campaign.target_geos = campaign_update.target_geos
    campaign.target_slot_types = campaign_update.target_slot_types
    campaign.creative_url = campaign_update.creative_url
    campaign.status = campaign_update.status
    campaign.quality_score = campaign_update.quality_score
    campaign.start_date = datetime.strptime(campaign_update.start_date, '%Y-%m-%d').date()
    campaign.end_date = datetime.strptime(campaign_update.end_date, '%Y-%m-%d').date()
    
    await db.commit()
    await db.refresh(campaign)
    campaign.start_date = campaign.start_date.strftime('%Y-%m-%d')
    campaign.end_date = campaign.end_date.strftime('%Y-%m-%d')
    return campaign
