import httpx
from typing import Dict, Any

class OKXCEXClient:
    BASE_URL = "https://www.okx.com"

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/api/v5/market/ticker"
        params = {"instId": symbol}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_candles(self, symbol: str, bar: str = "5m", limit: int = 100) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/api/v5/market/candles"
        params = {"instId": symbol, "bar": bar, "limit": str(limit)}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_system_time(self) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/api/v5/public/time"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
