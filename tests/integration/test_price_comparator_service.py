import pytest
import asyncio
from backend.services.price_comparator_service import PriceComparatorService

@pytest.mark.asyncio
async def test_compare_and_history_wif():
    service = PriceComparatorService()
    # Compare for WIF
    result = await service.compare("WIF")
    assert result["symbol"] == "WIF"
    assert result["price_cex"] > 0
    assert result["price_dex"] > 0
    assert isinstance(result["spread_pct"], float)
    # History should contain at least one record
    history = service.get_history("WIF")
    assert len(history) > 0
    last = history[-1]
    assert last["symbol"] == "WIF"
    assert last["price_cex"] == result["price_cex"]
    assert last["price_dex"] == result["price_dex"]
    assert last["spread_pct"] == result["spread_pct"]
    assert "timestamp" in last
