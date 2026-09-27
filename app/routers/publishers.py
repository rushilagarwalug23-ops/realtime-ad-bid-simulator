"""Publishers and Slots router endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.publisher import Publisher
from app.models.ad_slot import AdSlot
from app.schemas.bid_response import PublisherSchema, SlotSchema

router = APIRouter(prefix='/api/v1/publishers', tags=['publishers'])

@router.get('', response_model=list[PublisherSchema])
async def list_publishers(db: AsyncSession = Depends(get_db)):
    """List all publishers."""
    result = await db.execute(select(Publisher))
    return result.scalars().all()

@router.post('', response_model=PublisherSchema)
async def create_publisher(publisher: PublisherSchema, db: AsyncSession = Depends(get_db)):
    """Create a new publisher."""
    new_pub = Publisher(
        name=publisher.name,
        domain=publisher.domain,
        category=publisher.category,
        config=publisher.config,
        is_active=publisher.is_active
    )
    db.add(new_pub)
    await db.commit()
    await db.refresh(new_pub)
    return new_pub

@router.get('/{id}', response_model=PublisherSchema)
async def get_publisher(id: int, db: AsyncSession = Depends(get_db)):
    """Get a publisher by ID."""
    result = await db.execute(select(Publisher).where(Publisher.id == id))
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return pub

@router.post('/{id}/slots', response_model=SlotSchema)
async def create_slot(id: int, slot: SlotSchema, db: AsyncSession = Depends(get_db)):
    """Create an ad slot for a publisher."""
    # Ensure publisher exists
    result = await db.execute(select(Publisher).where(Publisher.id == id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Publisher not found")
        
    new_slot = AdSlot(
        publisher_id=id,
        slot_name=slot.slot_name,
        slot_type=slot.slot_type,
        width=slot.width,
        height=slot.height,
        floor_price=slot.floor_price,
        is_active=slot.is_active
    )
    db.add(new_slot)
    await db.commit()
    await db.refresh(new_slot)
    return new_slot

@router.get('/{id}/slots', response_model=list[SlotSchema])
async def list_slots(id: int, db: AsyncSession = Depends(get_db)):
    """List ad slots for a publisher."""
    result = await db.execute(select(AdSlot).where(AdSlot.publisher_id == id))
    return result.scalars().all()
