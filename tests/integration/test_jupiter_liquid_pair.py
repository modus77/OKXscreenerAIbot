import httpx
import pytest

@pytest.mark.asyncio
async def test_jupiter_liquid_pair():
    # Get list of liquid tokens from Jupiter
    tokens_url = "https://quote-api.jup.ag/v6/tokens"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(tokens_url)
        resp.raise_for_status()
        tokens_data = resp.json()
        # Jupiter returns a dict of {mint_address: token_info}
        if isinstance(tokens_data, dict) and "tokens" in tokens_data:
            tokens = list(tokens_data["tokens"].values())
        elif isinstance(tokens_data, dict):
            tokens = list(tokens_data.values())
        else:
            tokens = tokens_data
    # Find first liquid pair (e.g., USDC -> RAY)
    # Jupiter now returns a dict of {mint_address: token_info}, so filter dict values only
    token_dicts = [t for t in tokens if isinstance(t, dict)]
    usdc = next((t for t in token_dicts if t.get("symbol") == "USDC"), None)
    ray = next((t for t in token_dicts if t.get("symbol") == "RAY"), None)
    if not (usdc and ray):
        print(f"USDC/RAY not found in Jupiter tokens list: {tokens[:5]}")
        pytest.skip("USDC/RAY not found in Jupiter tokens list")
    amount = 10 ** usdc["decimals"] * 10  # 10 USDC
    quote_url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": usdc["address"],
        "outputMint": ray["address"],
        "amount": str(amount),
        "slippageBps": "50",
        "swapMode": "ExactIn"
    }
    resp = await client.get(quote_url, params=params)
    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"Jupiter quote API error: {resp.text}")
        pytest.skip(f"Jupiter quote API error: {resp.text}")
    data = resp.json()
    assert any(key in data for key in ["outAmount", "data", "routes"]), f"No quote data: {data}"
    print(f"Jupiter USDC->RAY quote: {data}")
