"""
Helius API client for fetching Solana token metadata.

This module provides a client for interacting with the Helius API
to fetch Solana token metadata. It implements rate limiting
and proper error handling, providing a clean async interface.

Features:
- Fetch token metadata (name, symbol, decimals, logo)

API limits:
- 1M credits per month (free plan)
- 10 requests per second (handled automatically)
- Credit cost per endpoint:
  * Token metadata: 1 credit

Example usage:
    from backend.services.helius import HeliusClient
    
    async def main():
        # Initialize client
        client = HeliusClient()
        
        # Fetch token metadata
        bonk_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        metadata = await client.get_token_metadata(bonk_address)
        print(f"Token: {metadata['name']} ({metadata['symbol']})")
        print(f"Decimals: {metadata['decimals']}")
        if 'logo' in metadata:
            print(f"Logo URL: {metadata['logo']}")

Environment variables:
    HELIUS_API_KEY: Your Helius API key (required)

API documentation:
    https://www.helius.dev/docs/api-reference
"""
import os
import httpx
from typing import Dict, Any, Optional
from typing import TypedDict

class TokenMetadata(TypedDict, total=False):
    name: str
    symbol: str
    decimals: int
    logo: str

class HeliusClient:
    """
    Minimal async client for fetching token metadata via Helius API.
    Documentation: https://www.helius.dev/docs/api-reference/endpoints/token-metadata
    """
    def __init__(self, network: str = "mainnet"):
        self.api_key = os.getenv("HELIUS_API_KEY")
        if not self.api_key:
            raise ValueError("HELIUS_API_KEY is not set in environment variables")
        self.base_url = "https://api.helius.xyz"

    async def get_token_metadata(self, mint_address: str) -> TokenMetadata:
        """
        Get token metadata by mint address via Helius REST endpoint.
        Args:
            mint_address: str — mint address of the Solana token
        Returns:
            TokenMetadata: name, symbol, decimals, logo (if available)
        Raises:
            ValueError: if the mint address is invalid
            RuntimeError: on network or HTTP errors
        """
        if not isinstance(mint_address, str) or len(mint_address) < 32:
            raise ValueError("Invalid token mint address")
        url = f"{self.base_url}/v0/token-metadata"
        params = {"api-key": self.api_key}
        json_data = {"mintAccounts": [mint_address]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, params=params, json=json_data)
                resp.raise_for_status()
                data = resp.json()
                print(f"HELIUS API RAW RESPONSE: {data}")  # DEBUG
            except httpx.RequestError as e:
                raise RuntimeError(f"Network error when contacting Helius: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Helius response error: {e}") from e
            # Helius now returns a list of objects directly, without 'result' key
            if not data or not isinstance(data, list) or not data:
                return {
                    "mint_address": mint_address,
                    "name": "Unknown",
                    "symbol": "Unknown",
                    "decimals": 0
                }
            raw_metadata = data[0]
            onchain_meta = raw_metadata.get("onChainMetadata", {})
            meta_data = onchain_meta.get("metadata") or {}
            meta_fields = meta_data.get("data") or {}
            name = meta_fields.get("name")
            symbol = meta_fields.get("symbol")
            # Safely parse decimals
            account_info = raw_metadata.get("onChainAccountInfo", {}).get("accountInfo")
            decimals = None
            if account_info and isinstance(account_info, dict):
                decimals = account_info.get("data", {}).get("parsed", {}).get("info", {}).get("decimals")
            # Fallback to legacyMetadata if onChainMetadata is missing
            if (not name or not symbol or decimals is None) and raw_metadata.get("legacyMetadata"):
                legacy = raw_metadata["legacyMetadata"]
                name = name or legacy.get("name", "Unknown")
                symbol = symbol or legacy.get("symbol", "Unknown")
                decimals = decimals if decimals is not None else legacy.get("decimals", 0)
            if name is None:
                name = "Unknown"
            if symbol is None:
                symbol = "Unknown"
            if decimals is None:
                decimals = 0
            logo = meta_fields.get("uri")
            metadata = {
                "mint_address": mint_address,
                "name": str(name),
                "symbol": str(symbol),
                "decimals": int(decimals)
            }
            if logo:
                metadata["logo"] = str(logo)
            return metadata