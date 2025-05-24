from backend.services.price_comparator import PriceComparator, PriceComparisonResult
from backend.config.tokens import TOKENS
from backend.ai.alpha_insight_service import AlphaInsightService
from backend.services.price_history import PriceHistoryService
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List

class HistoryStore:
    def __init__(self, maxlen: int = 100):
        self._store = defaultdict(lambda: deque(maxlen=maxlen))

    def add(self, symbol: str, result: PriceComparisonResult):
        if result.is_valid:
            self._store[symbol].append({
                "symbol": result.token,
                "price_cex": result.price_cex,
                "price_dex": result.price_dex,
                "spread_pct": result.spread_pct,
                "source": result.source,
                "timestamp": result.timestamp,
            })

    def get_history(self, symbol: str) -> List[Dict]:
        return list(self._store[symbol])

class PriceComparatorService:
    def __init__(self):
        self.comparator = PriceComparator()
        self.history = HistoryStore()
        self.tokens = TOKENS
        self.price_history_service = PriceHistoryService()

    async def compare(self, symbol: str) -> dict:
        if symbol not in self.tokens:
            return {"error": f"Token {symbol} not supported"}
        
        result = await self.comparator.compare_price(symbol)
        if result.is_valid:
            self.history.add(symbol, result)
            self.price_history_service.save(
                symbol=result.token,
                price_cex=result.price_cex,
                price_dex=result.price_dex,
                spread_pct=result.spread_pct,
                timestamp=result.timestamp,
                volume_cex=result.volume_cex,
                volume_dex=result.volume_dex,
                source_dex=result.source,
                is_valid=True,
                error_message=None
            )
            return {
                "token": result.token,
                "price_cex": result.price_cex,
                "price_dex": result.price_dex,
                "spread_pct": result.spread_pct,
                "volume_cex": result.volume_cex,
                "volume_dex": result.volume_dex,
                "slippage": result.slippage,
                "trend": result.trend,
                "source": result.source,
                "timestamp": result.timestamp,
                "is_valid": True,
                "error": None
            }
        else:
            self.price_history_service.save(
                symbol=result.token,
                price_cex=result.price_cex,
                price_dex=result.price_dex,
                spread_pct=result.spread_pct,
                timestamp=result.timestamp,
                volume_cex=result.volume_cex,
                volume_dex=result.volume_dex,
                source_dex=result.source,
                is_valid=False,
                error_message=result.error
            )
            return {
                "token": result.token,
                "price_cex": result.price_cex,
                "price_dex": result.price_dex,
                "spread_pct": result.spread_pct,
                "volume_cex": result.volume_cex,
                "volume_dex": result.volume_dex,
                "slippage": result.slippage,
                "trend": result.trend,
                "source": result.source,
                "timestamp": result.timestamp,
                "is_valid": False,
                "error": result.error
            }

    def get_history(self, symbol: str) -> List[Dict]:
        return self.history.get_history(symbol)

    async def compare_prices(self) -> List[PriceComparisonResult]:
        """Compare prices for all tokens and return top 3 by spread."""
        results = []
        for token in self.tokens:
            result = await self.comparator.compare_price(token)
            if result.is_valid:
                # Save to history
                self.history.add(token, result)
                self.price_history_service.save(
                    symbol=result.token,
                    price_cex=result.price_cex,
                    price_dex=result.price_dex,
                    spread_pct=result.spread_pct,
                    timestamp=result.timestamp,
                    volume_cex=result.volume_cex,
                    volume_dex=result.volume_dex,
                    source_dex=result.source,
                    is_valid=True,
                    error_message=None
                )
                results.append(result)
        
        # Sort by absolute spread value and take top 3
        results.sort()
        return results[:3]
