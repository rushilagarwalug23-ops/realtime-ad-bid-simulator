import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models.publisher import Publisher
from app.models.ad_slot import AdSlot
from app.models.campaign import Campaign

console = Console()

async def seed():
    console.print("[bold blue]Starting Database Seeding...[/bold blue]")
    
    # Ensure tables are created
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # 1. Publishers
        console.print("[yellow]Seeding Publishers...[/yellow]")
        publishers_data = [
            (1, 'TechDaily', 'techdaily.com', 'tech', {"blocked_categories": [], "floor_price_multiplier": 1.0}),
            (2, 'FinanceHub', 'financehub.com', 'finance', {"blocked_categories": ["gaming"], "floor_price_multiplier": 1.0}),
            (3, 'GamerZone', 'gamerzone.com', 'gaming', {"blocked_categories": [], "floor_price_multiplier": 1.0}),
            (4, 'HealthLife', 'healthlife.com', 'health', {"blocked_categories": [], "floor_price_multiplier": 1.0}),
            (5, 'NewsWorld', 'newsworld.com', 'news', {"blocked_categories": [], "floor_price_multiplier": 1.0}),
        ]
        
        for pid, name, domain, category, config in publishers_data:
            existing = await session.execute(select(Publisher).where(Publisher.id == pid))
            if not existing.scalar_one_or_none():
                pub = Publisher(id=pid, name=name, domain=domain, category=category, config=config, is_active=True)
                session.add(pub)
        await session.commit()
        
        # 2. Ad Slots
        console.print("[yellow]Seeding Ad Slots...[/yellow]")
        publisher_names = {1: 'TechDaily', 2: 'FinanceHub', 3: 'GamerZone', 4: 'HealthLife', 5: 'NewsWorld'}
        slot_id = 1
        for pid in range(1, 6):
            pub_name = publisher_names[pid]
            # Slot 1 - Banner
            existing = await session.execute(select(AdSlot).where(AdSlot.id == slot_id))
            if not existing.scalar_one_or_none():
                session.add(AdSlot(
                    id=slot_id,
                    publisher_id=pid,
                    slot_name=f"{pub_name} Top Banner",
                    slot_type="banner",
                    width=728,
                    height=90,
                    floor_price=round(random.uniform(0.50, 1.50), 2),
                    is_active=True
                ))
            slot_id += 1
            
            # Slot 2 - Native
            existing = await session.execute(select(AdSlot).where(AdSlot.id == slot_id))
            if not existing.scalar_one_or_none():
                session.add(AdSlot(
                    id=slot_id,
                    publisher_id=pid,
                    slot_name=f"{pub_name} Native Widget",
                    slot_type="native",
                    width=300,
                    height=250,
                    floor_price=round(random.uniform(1.00, 2.50), 2),
                    is_active=True
                ))
            slot_id += 1
        await session.commit()

        # 3. Campaigns
        console.print("[yellow]Seeding Campaigns...[/yellow]")
        advertisers = [
            "TechCorp", "FinanceInc", "GameStudio", "HealthBrand", "AutoDealer",
            "FashionCo", "FoodChain", "TravelAgency", "EduPlatform", "InsuranceCo",
            "CryptoExchange", "StreamingService", "CloudProvider", "FitnessApp", "RealEstateCo"
        ]
        
        today = date.today()
        for i in range(1, 16):
            adv_name = advertisers[i - 1]
            existing = await session.execute(select(Campaign).where(Campaign.id == i))
            if not existing.scalar_one_or_none():
                budget = float(random.randint(1000, 50000))
                daily_budget = float(random.randint(100, 5000))
                bid_price = round(random.uniform(0.50, 8.00), 2)
                
                categories = [] if random.random() < 0.2 else random.sample(['tech', 'finance', 'gaming', 'health', 'news'], k=random.randint(1, 3))
                geos = [] if random.random() < 0.2 else random.sample(['US', 'UK', 'IN', 'DE', 'CA', 'AU', 'JP', 'FR', 'BR', 'SG'], k=random.randint(1, 5))
                slot_types = random.sample(['banner', 'native', 'video'], k=random.randint(1, 2))
                quality_score = round(random.uniform(0.3, 1.0), 2)
                status = 'paused' if i in [3, 7] else 'active'
                
                session.add(Campaign(
                    id=i,
                    advertiser_name=adv_name,
                    campaign_name=f"{adv_name} Campaign Q3",
                    budget=budget,
                    daily_budget=daily_budget,
                    spent=0.0,
                    daily_spent=0.0,
                    bid_price=bid_price,
                    target_categories=categories,
                    target_geos=geos,
                    target_slot_types=slot_types,
                    creative_url=f"https://ads.example.com/{adv_name.lower()}/creative_q3.jpg",
                    quality_score=quality_score,
                    start_date=today - timedelta(days=30),
                    end_date=today + timedelta(days=30),
                    status=status
                ))
        await session.commit()

    console.print("[bold green]Database successfully seeded![/bold green]")
    
    # Display sample data
    table = Table(title="Sample Seeded Campaigns")
    table.add_column("Advertiser", style="cyan")
    table.add_column("Bid Price", style="magenta")
    table.add_column("Status", style="green")
    for adv, bid, status in [("TechCorp", 2.50, "active"), ("FinanceInc", 4.10, "active"), ("GameStudio", 1.20, "paused")]:
        table.add_row(adv, f"${bid:.2f}", status)
    console.print(table)

if __name__ == "__main__":
    asyncio.run(seed())
