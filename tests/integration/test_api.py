import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
import asyncio

@pytest.mark.asyncio
async def test_api_spreads():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/spreads")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(token['symbol'] == 'WIF' for token in data)
        assert all('spread_pct' in token for token in data)

@pytest.mark.asyncio
async def test_api_insight():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/insight/WIF")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "WIF"
        assert isinstance(data["insight"], str)
        assert len(data["insight"]) > 10
