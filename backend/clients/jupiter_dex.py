import httpx
from typing import Dict, Any

class JupiterDEXClient:
    BASE_URL = "https://quote-api.jup.ag"

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50, swap_mode: str = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/v6/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps)
        }
        if swap_mode:
            params["swapMode"] = swap_mode
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
