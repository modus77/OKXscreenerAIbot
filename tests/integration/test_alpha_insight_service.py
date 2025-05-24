import pytest
import asyncio
from backend.ai.alpha_insight_service import AlphaInsightService

@pytest.mark.asyncio
async def test_alpha_insight_service_basic():
    service = AlphaInsightService()
    # Example real data for WIF
    insight = await service.get_insight(
        price_cex=1.32,
        price_dex=1.35,
        spread=2.27,
        token="WIF",
        volume=25000000,
        trend=+3.5
    )
    print("AI Insight:", insight)
    assert isinstance(insight, str)
    assert len(insight) > 10
    assert any(word in insight for word in ["DEX", "CEX", "pump", "arbitrage"])
