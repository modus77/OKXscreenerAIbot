"""
OKX API client for fetching token price and market data from the centralized exchange.

Features:
- Get current price of a token in USDT
- Get 24h volume
- Get 24h % change
- Get bid/ask price

Implements best practices and matches OKX API documentation:
https://my.okx.com/docs-v5/en/#order-book-trading-market-data-get-tickers

Environment variables:
    OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE (not required for public endpoints)

Example usage:
    from backend.services.okx import OKXClient
    price_info = await OKXClient().get_ticker('BTC')
    print(price_info)
"""
import httpx
from typing import Dict, Any

class OKXClient:
    BASE_URL = "https://www.okx.com"
    WEB3_BASE_URL = "https://www.okx.com/web3/api/v1"

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker data for a token in USDC from OKX.
        Args:
            symbol: str — token symbol, e.g. 'BTC', 'SOL', 'ETH'
        Returns:
            Dict with keys: last, vol24h, change24h, bid, ask
        Raises:
            RuntimeError: on network or API error
        """
        inst_id = f"{symbol.upper()}-USDC"
        url = f"{self.BASE_URL}/api/v5/market/ticker"
        params = {"instId": inst_id}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except httpx.RequestError as e:
                raise RuntimeError(f"Network error with OKX: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"HTTP error from OKX: {e}") from e
        if not data or data.get("code") != '0' or not data.get("data"):
            raise RuntimeError(f"Invalid response from OKX: {data}")
        ticker = data["data"][0]
        last = float(ticker["last"])
        open24h = float(ticker["open24h"])
        change24h = (last - open24h) / open24h * 100
        return {
            "last": last,
            "vol24h": float(ticker["vol24h"]),
            "change24h": change24h,
            "bid": float(ticker["bidPx"]),
            "ask": float(ticker["askPx"])
        }

    async def get_tokens(self, chain_id: int = 101) -> Dict[str, Any]:
        """
        Получить список всех токенов DEX (Web3 API).
        https://www.okx.com/web3/api/v1/token/token-list
        """
        url = f"{self.WEB3_BASE_URL}/token/token-list"
        params = {"chainId": chain_id}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_pools(self, chain_id: int = 101) -> Dict[str, Any]:
        """
        Получить список пулов ликвидности DEX (Web3 API).
        https://www.okx.com/web3/api/v1/swap/pool/list
        """
        url = f"{self.WEB3_BASE_URL}/swap/pool/list"
        params = {"chainId": chain_id}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_prices(self, token_in: str, token_out: str, amount_in: str, chain_id: int = 101) -> Dict[str, Any]:
        """
        Получить цену обмена tokenIn → tokenOut (Web3 API).
        https://www.okx.com/web3/api/v1/swap/price
        """
        url = f"{self.WEB3_BASE_URL}/swap/price"
        params = {"chainId": chain_id, "tokenIn": token_in, "tokenOut": token_out, "amountIn": amount_in}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_swaps(self, pool_id: str, limit: int = 50, chain_id: int = 101) -> Dict[str, Any]:
        """
        Получить последние свопы по пулу (Web3 API).
        https://www.okx.com/web3/api/v1/swap/trade-list
        """
        url = f"{self.WEB3_BASE_URL}/swap/trade-list"
        params = {"chainId": chain_id, "poolId": pool_id, "limit": limit}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_candles(self, symbol: str, bar: str = "5m", limit: int = 100) -> Dict[str, Any]:
        """
        Получить свечи CEX (5m, 1h, 24h).
        https://www.okx.com/docs-v5/en/#rest-api-market-data-get-candlesticks
        Args:
            symbol: Тикер (например, 'BTC')
            bar: Интервал ('5m', '1h', '1d')
            limit: Количество свечей
        """
        inst_id = f"{symbol.upper()}-USDT"
        url = f"{self.BASE_URL}/api/v5/market/candles"
        params = {"instId": inst_id, "bar": bar, "limit": str(limit)}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_system_time(self) -> Dict[str, Any]:
        """
        Получить текущее серверное время OKX (public REST API).
        https://www.okx.com/docs-v5/en/#public-data-rest-api-get-system-time
        """
        url = f"{self.BASE_URL}/api/v5/public/time"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def get_token_price(self, chain_id: int, token_address: str) -> Dict[str, Any]:
        """
        Получить цену токена через Web3 DEX API (POST или GET).
        https://www.okx.com/web3/api/v1/token/price
        """
        url = "https://www.okx.com/web3/api/v1/token/price"
        payload = {"chainId": str(chain_id), "tokenAddress": token_address}
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 405:
                    # Пробуем GET-запрос
                    resp = await client.get(url, params=payload)
                    resp.raise_for_status()
                    return resp.json()
                raise
