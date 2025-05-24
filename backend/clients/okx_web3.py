import httpx
from typing import Dict, Any
import logging

class OKXWeb3Client:
    BASE_URL = "https://www.okx.com/web3/api/v1"

    async def get_token_price(self, chain_id: int, token_address: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/token/price"
        payload = {"chainId": str(chain_id), "tokenAddress": token_address}
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"OKX Web3 token price error: {e.response.status_code} {e.response.text}")
            raise
