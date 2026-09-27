"""Auction service logic."""
import uuid
import time
import json
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Publisher, AdSlot, Campaign, BidLog
from app.schemas.ad_request import AdRequest
from app.schemas.bid_response import BidResponse
from app.services.scoring import calculate_relevance_score, calculate_final_score
from app.cache import cache
from app.config import settings


class AuctionService:
    """Core service for running ad auctions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def run_auction(self, ad_request: AdRequest, use_cache: bool = True) -> BidResponse:
        """Run a full ad auction for the given request."""
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        cache_hit = False
        
        try:
            # 1. Fetch publisher config
            publisher, pub_from_cache = await self._get_publisher(ad_request.publisher_id, use_cache)
            if not publisher:
                return self._no_fill_response(request_id, start_time, cache_hit=False)
            
            # 2. Fetch ad slot config
            slot, slot_from_cache = await self._get_slot(ad_request.slot_id, use_cache)
            if not slot:
                return self._no_fill_response(request_id, start_time, cache_hit=False)
            
            cache_hit = pub_from_cache or slot_from_cache
            
            # 3. Check publisher blocked categories
            blocked = publisher.get('config', {}).get('blocked_categories', [])
            if ad_request.page_category in blocked:
                return self._no_fill_response(request_id, start_time, cache_hit)
            
            # 4. Get eligible campaigns
            campaigns, camp_from_cache = await self._get_eligible_campaigns(
                slot, ad_request.page_category, ad_request.user_geo, use_cache
            )
            cache_hit = cache_hit or camp_from_cache
            
            if not campaigns:
                latency = (time.perf_counter() - start_time) * 1000
                await self._log_bid(request_id, ad_request.slot_id, ad_request.publisher_id,
                                   None, latency, cache_hit, no_fill=True)
                return self._no_fill_response(request_id, start_time, cache_hit)
            
            # 5. Score and rank
            scored = self._score_and_rank(campaigns, ad_request)
            
            if not scored:
                latency = (time.perf_counter() - start_time) * 1000
                await self._log_bid(request_id, ad_request.slot_id, ad_request.publisher_id,
                                   None, latency, cache_hit, no_fill=True)
                return self._no_fill_response(request_id, start_time, cache_hit)
            
            # 6. Winner is the highest scored campaign
            winner = scored[0]
            latency = (time.perf_counter() - start_time) * 1000
            
            # 7. Log the bid
            await self._log_bid(
                request_id, ad_request.slot_id, ad_request.publisher_id,
                winner, latency, cache_hit, no_fill=False
            )
            
            return BidResponse(
                request_id=request_id,
                won=True,
                campaign_id=winner['campaign_id'],
                advertiser=winner['advertiser_name'],
                campaign_name=winner['campaign_name'],
                bid_price=winner['bid_price'],
                creative_url=winner['creative_url'],
                final_score=winner['final_score'],
                latency_ms=round(latency, 2),
                cache_hit=cache_hit,
                no_fill=False
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return BidResponse(
                request_id=request_id,
                won=False,
                latency_ms=round(latency, 2),
                cache_hit=cache_hit,
                no_fill=True
            )
    
    async def _get_publisher(self, publisher_id: int, use_cache: bool) -> tuple[dict|None, bool]:
        """Fetch publisher details, optionally from cache."""
        cache_key = f'pub:{publisher_id}'
        if use_cache:
            cached = await cache.get_json(cache_key)
            if cached:
                return cached, True
        
        result = await self.db.execute(
            select(Publisher).where(Publisher.id == publisher_id, Publisher.is_active == True)
        )
        pub = result.scalar_one_or_none()
        if not pub:
            return None, False
        
        pub_dict = {
            'id': pub.id, 'name': pub.name, 'domain': pub.domain,
            'category': pub.category, 'config': pub.config or {},
            'is_active': pub.is_active
        }
        if use_cache:
            await cache.set_json(cache_key, pub_dict, settings.CACHE_TTL_PUBLISHER)
        return pub_dict, False
    
    async def _get_slot(self, slot_id: int, use_cache: bool) -> tuple[dict|None, bool]:
        """Fetch ad slot details, optionally from cache."""
        cache_key = f'slot:{slot_id}'
        if use_cache:
            cached = await cache.get_json(cache_key)
            if cached:
                return cached, True
        
        result = await self.db.execute(
            select(AdSlot).where(AdSlot.id == slot_id, AdSlot.is_active == True)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return None, False
        
        slot_dict = {
            'id': slot.id, 'publisher_id': slot.publisher_id,
            'slot_name': slot.slot_name, 'slot_type': slot.slot_type,
            'width': slot.width, 'height': slot.height,
            'floor_price': slot.floor_price, 'is_active': slot.is_active
        }
        if use_cache:
            await cache.set_json(cache_key, slot_dict, settings.CACHE_TTL_SLOT)
        return slot_dict, False
    
    async def _get_eligible_campaigns(self, slot: dict, page_category: str, 
                                       user_geo: str, use_cache: bool) -> tuple[list[dict], bool]:
        """Fetch eligible campaigns for the auction."""
        cache_key = f'campaigns:{page_category}:{user_geo}:{slot["slot_type"]}'
        if use_cache:
            cached = await cache.get_json(cache_key)
            if cached is not None:
                # Filter by floor price even from cache
                return [c for c in cached if c['bid_price'] >= slot['floor_price']], True
        
        today = date.today()
        result = await self.db.execute(
            select(Campaign).where(
                and_(
                    Campaign.status == 'active',
                    Campaign.budget > Campaign.spent,
                    Campaign.daily_budget > Campaign.daily_spent,
                    Campaign.start_date <= today,
                    Campaign.end_date >= today,
                    Campaign.bid_price >= slot['floor_price']
                )
            )
        )
        campaigns = result.scalars().all()
        
        campaign_dicts = []
        for c in campaigns:
            campaign_dicts.append({
                'campaign_id': c.id,
                'advertiser_name': c.advertiser_name,
                'campaign_name': c.campaign_name,
                'bid_price': c.bid_price,
                'target_categories': c.target_categories or [],
                'target_geos': c.target_geos or [],
                'target_slot_types': c.target_slot_types or [],
                'creative_url': c.creative_url or '',
                'quality_score': c.quality_score,
                'budget': c.budget,
                'spent': c.spent,
            })
        
        if use_cache and campaign_dicts:
            await cache.set_json(cache_key, campaign_dicts, settings.CACHE_TTL_CAMPAIGNS)
        
        return [c for c in campaign_dicts if c['bid_price'] >= slot['floor_price']], False
    
    def _score_and_rank(self, campaigns: list[dict], ad_request: AdRequest) -> list[dict]:
        """Score and rank campaigns based on relevance and bid price."""
        scored = []
        for camp in campaigns:
            # Filter by slot type
            if camp['target_slot_types'] and ad_request.page_category not in camp.get('target_slot_types', []):
                pass  # Don't filter by slot type here, we don't have slot_type in ad_request
            
            relevance = calculate_relevance_score(
                page_category=ad_request.page_category,
                user_geo=ad_request.user_geo,
                user_interests=ad_request.user_interests,
                target_categories=camp['target_categories'],
                target_geos=camp['target_geos']
            )
            
            if relevance <= 0:
                continue
            
            final_score = calculate_final_score(
                relevance_score=relevance,
                bid_price=camp['bid_price'],
                quality_score=camp['quality_score']
            )
            
            scored.append({
                **camp,
                'relevance_score': relevance,
                'final_score': final_score
            })
        
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        return scored
    
    async def _log_bid(self, request_id: str, slot_id: int, publisher_id: int,
                       winner: dict | None, latency_ms: float, 
                       cache_hit: bool, no_fill: bool):
        """Log the result of the auction to the database."""
        log = BidLog(
            request_id=request_id,
            slot_id=slot_id,
            publisher_id=publisher_id,
            campaign_id=winner['campaign_id'] if winner else None,
            bid_price=winner['bid_price'] if winner else None,
            relevance_score=winner.get('relevance_score') if winner else None,
            final_score=winner.get('final_score') if winner else None,
            won=winner is not None,
            latency_ms=round(latency_ms, 2),
            cache_hit=cache_hit,
            no_fill=no_fill
        )
        self.db.add(log)
        await self.db.commit()
    
    def _no_fill_response(self, request_id: str, start_time: float, cache_hit: bool) -> BidResponse:
        """Create a response for when no campaign wins."""
        latency = (time.perf_counter() - start_time) * 1000
        return BidResponse(
            request_id=request_id,
            won=False,
            latency_ms=round(latency, 2),
            cache_hit=cache_hit,
            no_fill=True
        )
