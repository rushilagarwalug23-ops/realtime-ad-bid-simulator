import os
import json
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from rich.console import Console
from rich.table import Table

console = Console()

DATABASE_URL = os.getenv("DATABASE_URL_SYNC", "postgresql+psycopg2://postgres:postgres@localhost:5432/adbiddb")

def main():
    console.print("[bold blue]Starting Database Seeding...[/bold blue]")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.begin() as conn:
            # 1. Publishers
            console.print("[yellow]Seeding Publishers...[/yellow]")
            publishers_data = [
                (1, 'TechDaily', 'techdaily.com', 'tech', json.dumps({"blocked_categories": [], "floor_price_multiplier": 1.0})),
                (2, 'FinanceHub', 'financehub.com', 'finance', json.dumps({"blocked_categories": ["gaming"], "floor_price_multiplier": 1.0})),
                (3, 'GamerZone', 'gamerzone.com', 'gaming', json.dumps({"blocked_categories": [], "floor_price_multiplier": 1.0})),
                (4, 'HealthLife', 'healthlife.com', 'health', json.dumps({"blocked_categories": [], "floor_price_multiplier": 1.0})),
                (5, 'NewsWorld', 'newsworld.com', 'news', json.dumps({"blocked_categories": [], "floor_price_multiplier": 1.0})),
            ]
            for pid, name, domain, category, config in publishers_data:
                conn.execute(
                    text("""
                    INSERT INTO publishers (id, name, domain, category, config) 
                    VALUES (:id, :name, :domain, :category, :config::jsonb)
                    ON CONFLICT (id) DO NOTHING
                    """),
                    {"id": pid, "name": name, "domain": domain, "category": category, "config": config}
                )
            
            # 2. Ad Slots
            console.print("[yellow]Seeding Ad Slots...[/yellow]")
            publisher_names = {1: 'TechDaily', 2: 'FinanceHub', 3: 'GamerZone', 4: 'HealthLife', 5: 'NewsWorld'}
            slot_id = 1
            for pid in range(1, 6):
                pub_name = publisher_names[pid]
                # Slot 1 - Banner
                conn.execute(
                    text("""
                    INSERT INTO ad_slots (id, publisher_id, slot_name, slot_type, width, height, floor_price) 
                    VALUES (:id, :publisher_id, :slot_name, :slot_type, :width, :height, :floor_price)
                    ON CONFLICT (id) DO NOTHING
                    """),
                    {"id": slot_id, "publisher_id": pid, "slot_name": f"{pub_name} Top Banner", "slot_type": "banner", "width": 728, "height": 90, "floor_price": round(random.uniform(0.50, 1.50), 2)}
                )
                slot_id += 1
                # Slot 2 - Native
                conn.execute(
                    text("""
                    INSERT INTO ad_slots (id, publisher_id, slot_name, slot_type, width, height, floor_price) 
                    VALUES (:id, :publisher_id, :slot_name, :slot_type, :width, :height, :floor_price)
                    ON CONFLICT (id) DO NOTHING
                    """),
                    {"id": slot_id, "publisher_id": pid, "slot_name": f"{pub_name} Native Widget", "slot_type": "native", "width": 300, "height": 250, "floor_price": round(random.uniform(1.00, 2.50), 2)}
                )
                slot_id += 1

            # 3. Campaigns
            console.print("[yellow]Seeding Campaigns...[/yellow]")
            advertisers = ["TechCorp", "FinanceInc", "GameStudio", "HealthBrand", "AutoDealer", "FashionCo", "FoodChain", "TravelAgency", "EduPlatform", "InsuranceCo", "CryptoExchange", "StreamingService", "CloudProvider", "FitnessApp", "RealEstateCo"]
            
            for i in range(1, 16):
                adv_name = advertisers[i-1]
                budget = random.randint(1000, 50000)
                daily_budget = random.randint(100, 5000)
                bid_price = round(random.uniform(0.50, 8.00), 2)
                
                categories = [] if random.random() < 0.2 else random.sample(['tech', 'finance', 'gaming', 'health', 'news'], k=random.randint(1, 3))
                geos = [] if random.random() < 0.2 else random.sample(['US', 'UK', 'IN', 'DE', 'CA', 'AU', 'JP', 'FR', 'BR', 'SG'], k=random.randint(1, 5))
                slot_types = random.sample(['banner', 'native', 'video'], k=random.randint(1, 2))
                
                quality_score = round(random.uniform(0.3, 1.0), 2)
                start_date = datetime.now() - timedelta(days=30)
                end_date = datetime.now() + timedelta(days=30)
                status = 'paused' if i in [3, 7] else 'active'
                
                conn.execute(
                    text("""
                    INSERT INTO campaigns (id, advertiser_name, campaign_name, budget, daily_budget, bid_price, target_categories, target_geos, target_slot_types, creative_url, quality_score, start_date, end_date, status) 
                    VALUES (:id, :advertiser_name, :campaign_name, :budget, :daily_budget, :bid_price, :target_categories::jsonb, :target_geos::jsonb, :target_slot_types::jsonb, :creative_url, :quality_score, :start_date, :end_date, :status)
                    ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": i,
                        "advertiser_name": adv_name,
                        "campaign_name": f"{adv_name} Campaign Q3",
                        "budget": budget,
                        "daily_budget": daily_budget,
                        "bid_price": bid_price,
                        "target_categories": json.dumps(categories),
                        "target_geos": json.dumps(geos),
                        "target_slot_types": json.dumps(slot_types),
                        "creative_url": f"https://ads.example.com/{adv_name.lower()}/creative_q3.jpg",
                        "quality_score": quality_score,
                        "start_date": start_date,
                        "end_date": end_date,
                        "status": status
                    }
                )

        console.print("[bold green]Database successfully seeded![/bold green]")
        
        # Display sample data
        table = Table(title="Sample Campaigns")
        table.add_column("Adv", style="cyan")
        table.add_column("Bid", style="magenta")
        table.add_column("Status", style="green")
        for adv, bid, status in [("TechCorp", 2.50, "active"), ("FinanceInc", 4.10, "active"), ("GameStudio", 1.20, "paused")]:
            table.add_row(adv, str(bid), status)
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error during seeding: {e}[/bold red]")

if __name__ == "__main__":
    main()
