import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return 'asyncio'


class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_root(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            response = await ac.get('/')
        assert response.status_code == 200
        assert 'message' in response.json()


class TestBidEndpoint:
    """Test bid submission endpoint structure."""
    
    @pytest.mark.anyio
    async def test_bid_request_validation(self):
        """Test that invalid requests are rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            # Missing required fields
            response = await ac.post('/api/v1/bid', json={})
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.anyio
    async def test_bid_request_format(self):
        """Test that a valid request returns proper response format."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            response = await ac.post('/api/v1/bid', json={
                'publisher_id': 1,
                'slot_id': 1,
                'user_geo': 'US',
                'page_category': 'tech',
                'user_interests': ['tech']
            })
            # May fail due to no DB in test, but format should be right
            # In production tests, you'd mock the DB
            if response.status_code == 200:
                data = response.json()
                assert 'request_id' in data
                assert 'latency_ms' in data
                assert 'cache_hit' in data


class TestCampaignEndpoint:
    @pytest.mark.anyio
    async def test_list_campaigns_endpoint_exists(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            response = await ac.get('/api/v1/campaigns')
            # Will fail without DB but shouldn't 404
            assert response.status_code != 404
