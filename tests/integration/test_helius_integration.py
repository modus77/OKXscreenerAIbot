import os
import asyncio
import pytest
from backend.services.helius import HeliusClient

# For the integration test, a real API key and a real token mint address are required
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TEST_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # BONK

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_token_metadata_integration():
    if not HELIUS_API_KEY:
        pytest.skip("HELIUS_API_KEY is not set in environment variables")
    client = HeliusClient()
    metadata = await client.get_token_metadata(TEST_MINT)
    assert isinstance(metadata, dict)
    assert metadata.get("name")
    assert metadata.get("symbol")
    assert isinstance(metadata.get("decimals"), int)
    # logo may be absent, but if present, it should be a string
    if "logo" in metadata:
        assert isinstance(metadata["logo"], str)
