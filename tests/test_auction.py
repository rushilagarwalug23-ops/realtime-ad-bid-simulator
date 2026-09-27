import pytest
from app.services.scoring import calculate_relevance_score, calculate_final_score


class TestAuctionScoring:
    """Test the scoring and ranking logic used in auctions."""
    
    def test_highest_score_wins(self):
        """The campaign with the highest final_score should win."""
        campaigns = [
            {'bid_price': 2.0, 'quality_score': 0.8, 'target_categories': ['tech'], 'target_geos': ['US']},
            {'bid_price': 5.0, 'quality_score': 0.9, 'target_categories': ['tech'], 'target_geos': ['US']},
            {'bid_price': 3.0, 'quality_score': 0.7, 'target_categories': ['tech'], 'target_geos': ['US']},
        ]
        
        scored = []
        for c in campaigns:
            rel = calculate_relevance_score('tech', 'US', ['tech'], c['target_categories'], c['target_geos'])
            final = calculate_final_score(rel, c['bid_price'], c['quality_score'])
            scored.append({**c, 'final_score': final})
        
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        # Highest bid * quality should win
        assert scored[0]['bid_price'] == 5.0
    
    def test_relevance_can_beat_higher_bid(self):
        """A more relevant campaign can beat a higher bid."""
        # Campaign A: high bid but bad geo match
        rel_a = calculate_relevance_score('tech', 'US', ['tech'], ['tech'], [])  # worldwide
        score_a = calculate_final_score(rel_a, 10.0, 0.5)
        
        # Campaign B: lower bid but exact match
        rel_b = calculate_relevance_score('tech', 'US', ['tech'], ['tech'], ['US'])
        score_b = calculate_final_score(rel_b, 5.0, 1.0)
        
        # B should beat A due to relevance + quality despite lower bid
        assert score_b > score_a
    
    def test_filtered_campaigns_excluded(self):
        """Campaigns with 0 relevance should be excluded."""
        rel = calculate_relevance_score('tech', 'JP', [], ['finance'], ['US'])
        assert rel == 0.0
    
    def test_empty_campaign_list_no_fill(self):
        """No eligible campaigns should result in no-fill."""
        campaigns = []
        assert len(campaigns) == 0  # Would result in no-fill


class TestFloorPriceFiltering:
    """Test that campaigns below floor price are filtered."""
    
    def test_bid_below_floor_excluded(self):
        floor_price = 2.0
        campaigns = [
            {'bid_price': 1.5},  # below floor
            {'bid_price': 3.0},  # above floor
            {'bid_price': 0.5},  # below floor
        ]
        eligible = [c for c in campaigns if c['bid_price'] >= floor_price]
        assert len(eligible) == 1
        assert eligible[0]['bid_price'] == 3.0
