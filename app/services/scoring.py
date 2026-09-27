"""Scoring logic for auctions."""

def calculate_relevance_score(
    page_category: str,
    user_geo: str, 
    user_interests: list[str],
    target_categories: list[str],
    target_geos: list[str]
) -> float:
    """Calculate relevance score (0.0 to 1.0) for a campaign against an ad request."""
    # Category match
    if target_categories and page_category in target_categories:
        category_score = 1.0
    elif not target_categories:
        category_score = 0.5  # run of network
    else:
        return 0.0  # no category match = filtered out
    
    # Geo match  
    if target_geos and user_geo in target_geos:
        geo_score = 1.0
    elif not target_geos:
        geo_score = 0.7  # worldwide targeting
    else:
        return 0.0  # no geo match = filtered out
    
    # Interest overlap bonus
    if target_categories and user_interests:
        overlap = len(set(target_categories) & set(user_interests))
        interest_score = 0.5 + 0.5 * (overlap / len(target_categories))
    else:
        interest_score = 0.5
    
    return round(category_score * geo_score * interest_score, 4)


def calculate_final_score(
    relevance_score: float,
    bid_price: float,
    quality_score: float
) -> float:
    """Final auction score = relevance × bid_price × quality."""
    return round(relevance_score * bid_price * quality_score, 4)
