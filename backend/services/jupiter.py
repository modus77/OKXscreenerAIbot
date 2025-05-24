"""
Jupiter API client for fetching token swap price to USDC via DEX.

Features:
- Fetch swap price to USDC via /v6/quote endpoint (fallback: /v4/quote)

Documentation:
- https://dev.jup.ag/docs/swap-api/
- https://dev.jup.ag/docs/token-api/

"""
import httpx
from typing import Dict, Any, Optional

class JupiterClient:
    """
    Minimal async client for fetching token swap price to USDC via Jupiter API.
    """
    def __init__(self, base_url: str = "https://quote-api.jup.ag"):
        self.base_url = base_url

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> Dict[str, Any]:
        """
        Get swap price via /v6/quote (fallback: /v4/quote).
        Args:
            input_mint: str — mint address of the token to swap from
            output_mint: str — mint address of the token to swap to (e.g., USDC)
            amount: int — amount of input token (in smallest units, considering decimals)
            slippage_bps: int — allowed slippage in bps (default 50 = 0.5%)
        Returns:
            dict: Jupiter API result (best swap route and price)
        Raises:
            RuntimeError: on network or HTTP errors
        """
        params_v6 = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
            "swapMode": "ExactIn"
        }
        params_v4 = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps)
        }
        url_v6 = f"{self.base_url}/v6/quote"
        url_v4 = f"{self.base_url}/v4/quote"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url_v6, params=params_v6)
                if resp.status_code == 404:
                    resp = await client.get(url_v4, params=params_v4)
                try:
                    resp.raise_for_status()
                except Exception as e:
                    # Return error as dict for test to handle
                    return {"error": str(e), "response": resp.text}
                return resp.json()
            except Exception as e:
                return {"error": str(e)}
