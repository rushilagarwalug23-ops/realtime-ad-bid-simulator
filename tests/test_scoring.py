import pytest
from app.services.scoring import calculate_relevance_score, calculate_final_score

class TestRelevanceScore:
    def test_exact_category_and_geo_match(self):
        score = calculate_relevance_score('tech', 'US', ['tech'], ['tech'], ['US'])
        assert score == 1.0  # 1.0 * 1.0 * (0.5 + 0.5*1) = 1.0
    
    def test_no_category_match_returns_zero(self):
        score = calculate_relevance_score('tech', 'US', [], ['finance'], ['US'])
        assert score == 0.0
    
    def test_no_geo_match_returns_zero(self):
        score = calculate_relevance_score('tech', 'JP', [], ['tech'], ['US', 'UK'])
        assert score == 0.0
    
    def test_run_of_network_category(self):
        # Empty target_categories = run of network = 0.5 category score
        score = calculate_relevance_score('tech', 'US', [], [], ['US'])
        assert score > 0
        assert score < 1.0
    
    def test_worldwide_geo(self):
        # Empty target_geos = worldwide = 0.7 geo score
        score = calculate_relevance_score('tech', 'JP', [], ['tech'], [])
        assert score > 0
    
    def test_interest_overlap_increases_score(self):
        no_overlap = calculate_relevance_score('tech', 'US', [], ['tech'], ['US'])
        with_overlap = calculate_relevance_score('tech', 'US', ['tech', 'gaming'], ['tech', 'gaming'], ['US'])
        assert with_overlap >= no_overlap

class TestFinalScore:
    def test_basic_calculation(self):
        score = calculate_final_score(0.8, 2.5, 0.9)
        assert score == round(0.8 * 2.5 * 0.9, 4)
    
    def test_zero_relevance(self):
        score = calculate_final_score(0.0, 5.0, 1.0)
        assert score == 0.0
    
    def test_higher_bid_wins(self):
        low_bid = calculate_final_score(0.8, 1.0, 0.9)
        high_bid = calculate_final_score(0.8, 5.0, 0.9)
        assert high_bid > low_bid
    
    def test_quality_matters(self):
        low_q = calculate_final_score(0.8, 2.0, 0.3)
        high_q = calculate_final_score(0.8, 2.0, 1.0)
        assert high_q > low_q
