import os
import pytest
from backend.services.jupiter import JupiterClient

JUPITER_BASE_URL = "https://quote-api.jup.ag"
# Example: USDC -> RAY (mint addresses SPL, both valid)
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
RAY_MINT = "4k3Dyjzvzp8e2ugyqj9cwU6NFaMZntxVkcpeBMUZvDvc"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_jupiter_get_quote_integration():
    client = JupiterClient()
    # amount = 1 USDC (6 decimals)
    amount = 10**6
    result = await client.get_quote(
        input_mint=USDC_MINT,
        output_mint=RAY_MINT,
        amount=amount,
        slippage_bps=50
    )
    print("Jupiter API result:", result)
    if "error" in result:
        pytest.skip(f"Jupiter API error: {result['error']}")
    assert isinstance(result, dict)
    assert any(key in result for key in ["data", "routes", "outAmount"])
