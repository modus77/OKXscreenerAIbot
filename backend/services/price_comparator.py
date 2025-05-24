from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from decimal import Decimal
import time
from backend.config.tokens import TOKENS

logger = logging.getLogger(__name__)

MIN_PRICE = 0.000001  # Minimum price for validation
MAX_SPREAD = 10.0     # Maximum spread in percent
MIN_VOLUME = 100     # Minimum volume in USDC

def format_volume(volume: float) -> str:
    """Format volume in a human-readable format."""
    if volume >= 1_000_000:
        return f"{volume/1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.2f}K"
    else:
        return f"{volume:.2f}"

@dataclass
class PriceComparisonResult:
    token: str
    price_cex: float
    price_dex: float
    spread_pct: float
    volume_cex: float
    volume_dex: float
    slippage: Optional[float]
    trend: Optional[float]  # 24h change from OKX
    source: str
    timestamp: str
    is_valid: bool
    error: Optional[str] = None

    @property
    def formatted_volume(self, volume: float) -> str:
        if volume >= 1_000_000:
            return f"${volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"${volume/1_000:.1f}K"
        else:
            return f"${volume:.1f}"

    @property
    def spread_emoji(self) -> str:
        return "📈" if self.spread_pct > 0 else "📉"

    @property
    def trend_emoji(self) -> str:
        return "📈" if self.trend and self.trend > 0 else "📉"

    @property
    def trade_link(self) -> str:
        return f"https://www.okx.com/trade-spot/{self.token}-USDC"

    def __str__(self) -> str:
        if not self.is_valid:
            return f"💱 {self.token}\nError: {self.error}"
        
        # Format time to show only HH:MM:SS
        time_only = self.timestamp.split()[1]
        
        # Format trend if available
        trend_str = f"\n24h: {self.trend:+.2f}% {self.trend_emoji}" if self.trend is not None else ""
        
        return (
            f"💱 {self.token}\n"
            f"CEX (OKX): ${self.price_cex:.4f} | DEX (Jupiter): ${self.price_dex:.4f}\n"
            f"Spread: {self.spread_pct:+.2f}% {self.spread_emoji}{trend_str}\n"
            f"OKX Vol: {self.formatted_volume(self.volume_cex)} | JUP Vol: {self.formatted_volume(self.volume_dex)}\n"
            f"🕒 {time_only}\n"
            f"👉 [Trade on OKX]({self.trade_link})"
        )

    def __lt__(self, other):
        # For sorting by absolute spread value
        return abs(self.spread_pct) > abs(other.spread_pct)

class PriceComparator:
    def __init__(self):
        self.tokens = TOKENS
        self.MIN_PRICE = 0.000001
        self.MAX_SPREAD = 10.0
        self.MIN_VOLUME = 1000  # Lowered to 1000 USDC to include more tokens

    async def compare_price(self, token: str) -> PriceComparisonResult:
        try:
            if token not in self.tokens:
                return PriceComparisonResult(
                    token=token,
                    price_cex=0,
                    price_dex=0,
                    spread_pct=0,
                    volume_cex=0,
                    volume_dex=0,
                    slippage=None,
                    trend=None,
                    source="",
                    timestamp="",
                    is_valid=False,
                    error=f"Token {token} not supported"
                )

            # Get CEX price and volume
            cex_data = await self._get_cex_price(token)
            if not cex_data:
                return PriceComparisonResult(
                    token=token,
                    price_cex=0,
                    price_dex=0,
                    spread_pct=0,
                    volume_cex=0,
                    volume_dex=0,
                    slippage=None,
                    trend=None,
                    source="",
                    timestamp="",
                    is_valid=False,
                    error="Failed to get CEX price"
                )

            price_cex = float(cex_data.get("last", 0))
            volume_cex = float(cex_data.get("vol24h", 0)) * price_cex  # Convert to USDC
            trend = float(cex_data.get("change24h", 0))

            # Get DEX price and volume
            dex_data = await self._get_dex_price(token)
            if not dex_data:
                return PriceComparisonResult(
                    token=token,
                    price_cex=price_cex,
                    price_dex=0,
                    spread_pct=0,
                    volume_cex=volume_cex,
                    volume_dex=0,
                    slippage=None,
                    trend=trend,
                    source="",
                    timestamp="",
                    is_valid=False,
                    error="Failed to get DEX price"
                )

            price_dex = float(dex_data.get("outAmount", 0)) / float(dex_data.get("inAmount", 1))
            volume_dex = float(dex_data.get("volume24h", 0))  # Use actual DEX volume
            slippage = float(dex_data.get("priceImpactPct", 0))

            # Validate prices
            if price_cex < self.MIN_PRICE or price_dex < self.MIN_PRICE:
                return PriceComparisonResult(
                    token=token,
                    price_cex=price_cex,
                    price_dex=price_dex,
                    spread_pct=0,
                    volume_cex=volume_cex,
                    volume_dex=volume_dex,
                    slippage=slippage,
                    trend=trend,
                    source="Jupiter",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                    is_valid=False,
                    error="Price too low"
                )

            # Check volume using DEX volume
            if volume_dex < self.MIN_VOLUME:
                return PriceComparisonResult(
                    token=token,
                    price_cex=price_cex,
                    price_dex=price_dex,
                    spread_pct=0,
                    volume_cex=volume_cex,
                    volume_dex=volume_dex,
                    slippage=slippage,
                    trend=trend,
                    source="Jupiter",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                    is_valid=False,
                    error=f"Volume too low: {volume_dex:.2f} USDC"
                )

            # Calculate spread
            spread_pct = ((price_dex - price_cex) / price_cex) * 100

            # Check spread
            if abs(spread_pct) > self.MAX_SPREAD:
                return PriceComparisonResult(
                    token=token,
                    price_cex=price_cex,
                    price_dex=price_dex,
                    spread_pct=spread_pct,
                    volume_cex=volume_cex,
                    volume_dex=volume_dex,
                    slippage=slippage,
                    trend=trend,
                    source="Jupiter",
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                    is_valid=False,
                    error=f"Spread too high: {spread_pct:+.2f}%"
                )

            return PriceComparisonResult(
                token=token,
                price_cex=price_cex,
                price_dex=price_dex,
                spread_pct=spread_pct,
                volume_cex=volume_cex,
                volume_dex=volume_dex,
                slippage=slippage,
                trend=trend,
                source="Jupiter",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                is_valid=True
            )

        except Exception as e:
            logger.error(f"Error comparing prices for {token}: {e}")
            return PriceComparisonResult(
                token=token,
                price_cex=0,
                price_dex=0,
                spread_pct=0,
                volume_cex=0,
                volume_dex=0,
                slippage=None,
                trend=None,
                source="",
                timestamp="",
                is_valid=False,
                error=str(e)
            )

    async def _get_cex_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            import aiohttp
            session = aiohttp.ClientSession()
            base_url = "https://www.okx.com"
            
            # Get ticker
            ticker_url = f"{base_url}/api/v5/market/ticker?instId={symbol}-USDC"
            logger.info(f"Fetching CEX price from: {ticker_url}")
            
            async with session.get(ticker_url) as response:
                if response.status != 200:
                    logger.error(f"CEX API error: {response.status}")
                    return None
                data = await response.json()
                if not data.get("data"):
                    logger.error(f"No CEX data for {symbol}")
                    return None
                
                ticker_data = data["data"][0]
                logger.info(f"CEX data for {symbol}: {ticker_data}")
                
                # Get candles for trend
                candles_url = f"{base_url}/api/v5/market/candles?instId={symbol}-USDC&bar=1D&limit=2"
                async with session.get(candles_url) as candles_response:
                    if candles_response.status == 200:
                        candles_data = await candles_response.json()
                        if candles_data.get("data"):
                            current_price = float(ticker_data["last"])
                            prev_price = float(candles_data["data"][1][4])
                            change_24h = ((current_price - prev_price) / prev_price) * 100
                            ticker_data["change24h"] = change_24h
                            logger.info(f"24h change for {symbol}: {change_24h}%")

                await session.close()
                return {
                    "last": ticker_data["last"],
                    "vol24h": ticker_data.get("volCcy24h", "0"),
                    "change24h": ticker_data.get("change24h", 0)
                }

        except Exception as e:
            logger.error(f"Error getting CEX price for {symbol}: {e}")
            return None

    async def _get_dex_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            import aiohttp
            session = aiohttp.ClientSession()
            base_url = "https://quote-api.jup.ag/v6"
            tokens_base_url = "https://tokens.jup.ag/token"
            
            mint, usdc_mint, decimals = self.tokens[symbol]
            amount = 10 ** decimals  # 1 token

            # Get token info including daily volume
            token_url = f"{tokens_base_url}/{mint}"
            logger.info(f"Fetching token info from: {token_url}")
            async with session.get(token_url) as token_response:
                if token_response.status != 200:
                    logger.error(f"Token info API error: {token_response.status}")
                    await session.close()
                    return None
                token_data = await token_response.json()
                daily_volume = float(token_data.get("daily_volume", 0))
                logger.info(f"Token info for {symbol}: {token_data}")

            # Get quote for price and route
            quote_url = f"{base_url}/quote?inputMint={mint}&outputMint={usdc_mint}&amount={amount}&slippageBps=50"
            logger.info(f"Fetching DEX quote from: {quote_url}")
            async with session.get(quote_url) as response:
                if response.status != 200:
                    logger.error(f"DEX quote API error: {response.status}")
                    await session.close()
                    return None
                data = await response.json()
                logger.info(f"DEX quote data for {symbol}: {data}")

            await session.close()

            return {
                "inAmount": amount,
                "outAmount": data.get("outAmount", 0),
                "priceImpactPct": data.get("priceImpactPct", 0),
                "source": "Jupiter",
                "volume24h": daily_volume
            }

        except Exception as e:
            logger.error(f"Error getting DEX price for {symbol}: {e}")
            return None
